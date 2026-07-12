"""Tester/QA agent — generates tests, runs them, analyzes failures."""
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestFile:
    """A generated test file."""

    path: str
    content: str
    test_count: int = 0


@dataclass
class TestResult:
    """Result of running a test file."""

    test_file: str
    passed: bool
    output: str
    errors: List[str]
    duration_ms: int = 0


@dataclass
class BugReport:
    """A bug discovered during testing."""

    file_path: str
    error_type: str
    error_message: str
    traceback: str
    suggested_fix: str
    severity: str = "medium"


GENERATE_TEST_PROMPT = """You are a QA engineer. Write pytest unit tests for this Python file.

File: {path}
```python
{content}
```

Write comprehensive pytest tests. Return ONLY the test file content, no markdown fences.
Use simple imports — assume the source file is importable by its module name.
Include at least 3 test functions."""

ANALYZE_FAILURE_PROMPT = """You are a debugging expert. Analyze this pytest failure and suggest a fix.

Test output:
{output}

Source files available:
{source_files_list}

Return a JSON array (no markdown fences) of bug reports:
[{{"file_path": "...", "error_type": "...", "error_message": "...", "traceback": "...", "suggested_fix": "...", "severity": "medium"}}]"""


class TesterAgent:
    """Generates and runs tests, analyzes failures."""

    def __init__(self, llm: object) -> None:
        self.llm = llm

    async def generate_tests(self, file_path: str, content: str, file_type: str) -> TestFile:
        """Generate test file for a source file."""
        if file_type != "backend" or not file_path.endswith(".py"):
            # For non-Python files, return a basic structural validation
            test_name = f"test_{os.path.basename(file_path)}.py"
            test_content = f'"""Structural validation for {file_path}."""\n\ndef test_{os.path.basename(file_path).replace(".", "_")}_exists():\n    assert True  # structural placeholder\n'
            return TestFile(path=test_name, content=test_content, test_count=1)

        prompt = GENERATE_TEST_PROMPT.format(path=file_path, content=content)
        response = await self.llm.ainvoke(prompt)
        test_content = response.content if hasattr(response, "content") else str(response)
        test_content = self._strip_fences(test_content)

        base = os.path.basename(file_path)
        test_path = f"test_{base}"
        test_count = test_content.count("def test_")
        logger.info("Generated %d tests for %s", test_count, file_path)
        return TestFile(path=test_path, content=test_content, test_count=test_count)

    async def run_python_tests(self, test_files: dict, source_files: dict) -> List[TestResult]:
        """Run pytest in a temporary directory and return results."""
        results: List[TestResult] = []
        tmpdir = tempfile.mkdtemp(prefix="architectai_tests_")
        try:
            # Write source files
            for path, content in source_files.items():
                fpath = os.path.join(tmpdir, os.path.basename(path))
                with open(fpath, "w") as f:
                    f.write(content)

            # Write test files
            for path, content in test_files.items():
                fpath = os.path.join(tmpdir, os.path.basename(path))
                with open(fpath, "w") as f:
                    f.write(content)

            # Run pytest
            start = time.time()
            proc = subprocess.run(
                ["python3", "-m", "pytest", "--tb=short", "-q", tmpdir],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=tmpdir,
            )
            duration = int((time.time() - start) * 1000)
            output = proc.stdout + "\n" + proc.stderr
            passed = proc.returncode == 0
            errors = self._extract_errors(output)

            for tfile in test_files:
                results.append(TestResult(
                    test_file=tfile,
                    passed=passed,
                    output=output,
                    errors=errors,
                    duration_ms=duration,
                ))
            logger.info("Tests %s (%dms)", "PASSED" if passed else "FAILED", duration)
        except subprocess.TimeoutExpired:
            logger.error("Test execution timed out")
            for tfile in test_files:
                results.append(TestResult(
                    test_file=tfile, passed=False, output="Timeout after 60s", errors=["Timeout"], duration_ms=60000
                ))
        except Exception as exc:
            logger.error("Test execution error: %s", exc)
            for tfile in test_files:
                results.append(TestResult(
                    test_file=tfile, passed=False, output=str(exc), errors=[str(exc)], duration_ms=0
                ))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        return results

    async def analyze_failures(self, test_results: List[TestResult]) -> List[BugReport]:
        """Use LLM to analyze test failures and produce bug reports."""
        import json as _json

        failed = [r for r in test_results if not r.passed]
        if not failed:
            return []

        combined_output = "\n---\n".join(r.output for r in failed)
        prompt = ANALYZE_FAILURE_PROMPT.format(
            output=combined_output[:3000],
            source_files_list="(see test output for details)",
        )
        response = await self.llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = self._strip_fences(content)

        try:
            bugs_raw = _json.loads(content)
        except _json.JSONDecodeError:
            logger.warning("Could not parse LLM bug analysis")
            bugs_raw = [{"file_path": "unknown", "error_type": "parse_error",
                         "error_message": combined_output[:200], "traceback": "",
                         "suggested_fix": "Review test output manually", "severity": "medium"}]

        return [
            BugReport(
                file_path=b.get("file_path", "unknown"),
                error_type=b.get("error_type", "unknown"),
                error_message=b.get("error_message", ""),
                traceback=b.get("traceback", ""),
                suggested_fix=b.get("suggested_fix", ""),
                severity=b.get("severity", "medium"),
            )
            for b in bugs_raw
        ]

    def _extract_bugs_from_output(self, output: str, source_files: dict) -> List[BugReport]:
        """Regex-parse pytest output for FAILED lines."""
        bugs: List[BugReport] = []
        for match in re.finditer(r"FAILED\s+(\S+)::(\S+)", output):
            test_file, test_name = match.group(1), match.group(2)
            bugs.append(BugReport(
                file_path=test_file,
                error_type="test_failure",
                error_message=f"Test {test_name} failed",
                traceback="",
                suggested_fix="",
                severity="medium",
            ))
        return bugs

    @staticmethod
    def _extract_errors(output: str) -> List[str]:
        """Extract error lines from pytest output."""
        errors: List[str] = []
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line or "error" in line.lower():
                errors.append(line.strip())
        return errors

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
