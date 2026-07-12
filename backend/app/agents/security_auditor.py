"""Security auditor agent — scans generated code for vulnerabilities."""
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """A single security finding."""

    file_path: str
    line_number: Optional[int]
    owasp_category: str
    severity: str  # critical / high / medium / low / info
    description: str
    code_snippet: Optional[str]
    suggested_fix: str


@dataclass
class SecurityReport:
    """Aggregated security scan report."""

    findings: List[SecurityFinding]
    passed: bool
    scan_duration_ms: int = 0


LLM_SECURITY_PROMPT = """You are a security auditor. Review these files for vulnerabilities.

Check for (OWASP Top 10):
1. Hardcoded secrets/API keys
2. SQL injection
3. XSS in templates
4. Insecure direct object references
5. Missing authentication/authorization
6. Exposed debug endpoints
7. Insecure deserialization
8. Path traversal
9. SSRF
10. Security misconfiguration

Files:
{files_content}

Return a JSON array (no markdown fences) of findings:
[{{"file_path": "...", "line_number": null, "owasp_category": "A01:2021 Broken Access Control", "severity": "high", "description": "...", "code_snippet": "...", "suggested_fix": "..."}}]

If no issues found, return an empty array: []"""


class SecurityAuditorAgent:
    """Scans generated code for security vulnerabilities."""

    def __init__(self, llm: object) -> None:
        self.llm = llm

    async def scan(self, generated_files: dict) -> SecurityReport:
        """Run all security scans and return aggregated report."""
        start = time.time()
        findings: List[SecurityFinding] = []

        # Run bandit on Python files
        python_files = {p: c for p, c in generated_files.items() if p.endswith(".py")}
        if python_files:
            bandit_findings = await self.run_bandit(python_files)
            findings.extend(bandit_findings)

        # Run npm audit analysis on package.json
        for path, content in generated_files.items():
            if os.path.basename(path) == "package.json":
                npm_findings = await self.run_npm_audit_analysis(content)
                findings.extend(npm_findings)

        # LLM security review
        llm_findings = await self.llm_security_review(generated_files)
        findings.extend(llm_findings)

        # Deduplicate by file_path + description
        seen = set()
        unique: List[SecurityFinding] = []
        for f in findings:
            key = (f.file_path, f.description[:50])
            if key not in seen:
                seen.add(key)
                unique.append(f)

        duration = int((time.time() - start) * 1000)
        has_critical = any(f.severity in ("critical", "high") for f in unique)
        logger.info("Security scan: %d findings (%dms), passed=%s", len(unique), duration, not has_critical)
        return SecurityReport(findings=unique, passed=not has_critical, scan_duration_ms=duration)

    async def run_bandit(self, python_files: dict) -> List[SecurityFinding]:
        """Run bandit static analysis on Python files."""
        tmpdir = tempfile.mkdtemp(prefix="architectai_bandit_")
        findings: List[SecurityFinding] = []
        try:
            for path, content in python_files.items():
                fpath = os.path.join(tmpdir, os.path.basename(path))
                with open(fpath, "w") as f:
                    f.write(content)

            proc = subprocess.run(
                ["bandit", "-r", tmpdir, "-f", "json", "-q"],
                capture_output=True, text=True, timeout=30,
            )
            if proc.stdout:
                findings = self._parse_bandit_output(proc.stdout, python_files)
        except FileNotFoundError:
            logger.warning("bandit not installed, skipping static analysis")
        except subprocess.TimeoutExpired:
            logger.warning("bandit timed out")
        except Exception as exc:
            logger.error("bandit error: %s", exc)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        return findings

    async def run_npm_audit_analysis(self, package_json_content: str) -> List[SecurityFinding]:
        """Analyze package.json for known vulnerable patterns."""
        findings: List[SecurityFinding] = []
        try:
            pkg = json.loads(package_json_content)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            # Check for known vulnerable patterns
            vulnerable_patterns = {
                "event-stream": "Known supply chain attack (flatmap-stream)",
                "lodash": "Prototype pollution in versions < 4.17.21",
                "minimist": "Prototype pollution in versions < 1.2.6",
            }
            for dep, reason in vulnerable_patterns.items():
                if dep in deps:
                    findings.append(SecurityFinding(
                        file_path="package.json",
                        line_number=None,
                        owasp_category="A06:2021 Vulnerable Components",
                        severity="medium",
                        description=f"Potentially vulnerable dependency: {dep} - {reason}",
                        code_snippet=f'"{dep}": "{deps[dep]}"',
                        suggested_fix=f"Review and update {dep} to the latest secure version",
                    ))
        except json.JSONDecodeError:
            logger.warning("Could not parse package.json")
        return findings

    async def llm_security_review(self, files: dict) -> List[SecurityFinding]:
        """Use LLM to review files for security issues."""
        # Limit content sent to LLM
        files_content = ""
        for path, content in list(files.items())[:10]:
            truncated = content[:2000] if len(content) > 2000 else content
            files_content += f"\n--- {path} ---\n{truncated}\n"

        prompt = LLM_SECURITY_PROMPT.format(files_content=files_content)
        response = await self.llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            raw = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM security review output")
            return []

        findings: List[SecurityFinding] = []
        for item in raw:
            findings.append(SecurityFinding(
                file_path=item.get("file_path", "unknown"),
                line_number=item.get("line_number"),
                owasp_category=item.get("owasp_category", "Unknown"),
                severity=item.get("severity", "info"),
                description=item.get("description", ""),
                code_snippet=item.get("code_snippet"),
                suggested_fix=item.get("suggested_fix", ""),
            ))
        return findings

    def _parse_bandit_output(self, bandit_json: str, original_files: dict) -> List[SecurityFinding]:
        """Parse bandit JSON output into SecurityFinding objects."""
        findings: List[SecurityFinding] = []
        try:
            data = json.loads(bandit_json)
            # Map tmpdir basenames back to original paths
            basename_to_path = {os.path.basename(p): p for p in original_files}
            for result in data.get("results", []):
                basename = os.path.basename(result.get("filename", ""))
                original_path = basename_to_path.get(basename, result.get("filename", "unknown"))
                severity_map = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"}
                findings.append(SecurityFinding(
                    file_path=original_path,
                    line_number=result.get("line_number"),
                    owasp_category="A05:2021 Security Misconfiguration",
                    severity=severity_map.get(result.get("issue_severity", ""), "info"),
                    description=result.get("issue_text", ""),
                    code_snippet=result.get("code", ""),
                    suggested_fix=f"Review {result.get('test_id', '')}: {result.get('issue_text', '')}",
                ))
        except json.JSONDecodeError:
            logger.warning("Could not parse bandit JSON output")
        return findings
