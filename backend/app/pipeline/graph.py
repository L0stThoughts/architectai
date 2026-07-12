"""Full LangGraph pipeline for ArchitectAI."""
import logging
from dataclasses import asdict
from typing import Any

from langgraph.graph import StateGraph, END

from app.config import Settings
from app.pipeline.state import AgentState
from app.agents.orchestrator import OrchestratorAgent, FilePlanItem
from app.agents.coder import CoderAgent
from app.agents.tester import TesterAgent
from app.agents.security_auditor import SecurityAuditorAgent
from app.services.bundle_service import BundleService

logger = logging.getLogger(__name__)


class ArchitectAIGraph:
    """Builds and manages the LangGraph state machine for code generation."""

    def __init__(self, llm: Any, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings
        self.orchestrator = OrchestratorAgent(llm)
        self.coder = CoderAgent(llm)
        self.tester = TesterAgent(llm)
        self.security = SecurityAuditorAgent(llm)
        self.bundler = BundleService(settings.bundles_dir)

    def build(self) -> Any:
        """Build and compile the StateGraph."""
        graph = StateGraph(AgentState)

        graph.add_node("plan", self.plan_node)
        graph.add_node("generate", self.generate_node)
        graph.add_node("test", self.test_node)
        graph.add_node("patch", self.patch_node)
        graph.add_node("security", self.security_node)
        graph.add_node("package", self.package_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "generate")
        graph.add_edge("generate", "test")
        graph.add_conditional_edges("test", self.should_patch, {
            "patch": "patch",
            "security": "security",
            "failed": END,
        })
        graph.add_conditional_edges("patch", self.should_retest, {
            "test": "test",
            "package": "package",
        })
        graph.add_conditional_edges("security", self.should_security_patch, {
            "patch": "patch",
            "package": "package",
        })
        graph.add_edge("package", END)

        return graph.compile()

    async def plan_node(self, state: AgentState) -> dict:
        """Plan tech stack and file structure."""
        logger.info("[PLAN] Starting planning for job %s", state.get("job_id"))
        plan_result = await self.orchestrator.plan(state["product_goal"])
        file_plan = [
            {"path": item.path, "description": item.description,
             "file_type": item.file_type, "priority": item.priority}
            for item in plan_result.file_plan
        ]
        return {
            "tech_stack": plan_result.tech_stack,
            "file_plan": file_plan,
            "current_phase": "GENERATE",
            "current_file_index": 0,
            "generated_files": {},
        }

    async def generate_node(self, state: AgentState) -> dict:
        """Generate all files from the file plan."""
        logger.info("[GENERATE] Generating %d files", len(state.get("file_plan", [])))
        generated_files = dict(state.get("generated_files", {}))
        context = {
            "tech_stack": state.get("tech_stack", {}),
            "product_goal": state.get("product_goal", ""),
            "already_generated_files": generated_files,
        }
        for i, item_dict in enumerate(state.get("file_plan", [])):
            plan_item = FilePlanItem(
                path=item_dict["path"],
                description=item_dict["description"],
                file_type=item_dict.get("file_type", "backend"),
                priority=item_dict.get("priority", 0),
            )
            result = await self.coder.generate_file(plan_item, context)
            generated_files[result.path] = result.content
            context["already_generated_files"] = generated_files
            logger.info("[GENERATE] %d/%d: %s", i + 1, len(state["file_plan"]), result.path)

        return {
            "generated_files": generated_files,
            "current_file_index": len(state.get("file_plan", [])),
            "current_phase": "TEST",
        }

    async def test_node(self, state: AgentState) -> dict:
        """Generate and run tests for backend Python files."""
        logger.info("[TEST] Running tests for job %s", state.get("job_id"))
        generated_files = state.get("generated_files", {})
        python_backend_files = {
            p: c for p, c in generated_files.items()
            if p.endswith(".py") and not p.startswith("test_")
        }

        test_files: dict = {}
        for path, content in python_backend_files.items():
            tf = await self.tester.generate_tests(path, content, "backend")
            test_files[tf.path] = tf.content

        test_results = await self.tester.run_python_tests(test_files, python_backend_files)

        results_dicts = [
            {"test_file": r.test_file, "passed": r.passed, "output": r.output,
             "errors": r.errors, "duration_ms": r.duration_ms}
            for r in test_results
        ]

        bug_reports: list = []
        failed = [r for r in test_results if not r.passed]
        if failed:
            bugs = await self.tester.analyze_failures(test_results)
            bug_reports = [
                {"file_path": b.file_path, "error_type": b.error_type,
                 "error_message": b.error_message, "traceback": b.traceback,
                 "suggested_fix": b.suggested_fix, "severity": b.severity}
                for b in bugs
            ]

        return {
            "test_files": test_files,
            "test_results": results_dicts,
            "bug_reports": bug_reports,
            "current_phase": "TEST",
        }

    async def patch_node(self, state: AgentState) -> dict:
        """Patch files based on bug reports."""
        logger.info("[PATCH] Patching files (attempt %d)", state.get("patch_attempts", 0) + 1)
        generated_files = dict(state.get("generated_files", {}))
        for bug in state.get("bug_reports", []):
            file_path = bug.get("file_path", "")
            if file_path in generated_files:
                patch_result = await self.coder.patch_file(
                    file_path, generated_files[file_path], bug
                )
                generated_files[file_path] = patch_result.patched_content

        return {
            "generated_files": generated_files,
            "patch_attempts": state.get("patch_attempts", 0) + 1,
            "current_phase": "PATCH",
        }

    async def security_node(self, state: AgentState) -> dict:
        """Run security scans on generated files."""
        logger.info("[SECURITY] Scanning files for job %s", state.get("job_id"))
        report = await self.security.scan(state.get("generated_files", {}))
        findings_dicts = [
            {"file_path": f.file_path, "line_number": f.line_number,
             "owasp_category": f.owasp_category, "severity": f.severity,
             "description": f.description, "code_snippet": f.code_snippet,
             "suggested_fix": f.suggested_fix}
            for f in report.findings
        ]
        return {
            "security_findings": findings_dicts,
            "security_passed": report.passed,
            "current_phase": "SECURITY",
        }

    async def package_node(self, state: AgentState) -> dict:
        """Package generated files into a ZIP bundle."""
        logger.info("[PACKAGE] Creating bundle for job %s", state.get("job_id"))
        bundle_path = await self.bundler.create_bundle(
            state.get("job_id", "unknown"), state.get("generated_files", {})
        )
        return {
            "bundle_path": bundle_path,
            "current_phase": "COMPLETE",
        }

    def should_patch(self, state: AgentState) -> str:
        """Decide whether to patch, proceed to security, or fail."""
        bug_reports = state.get("bug_reports", [])
        patch_attempts = state.get("patch_attempts", 0)
        if not bug_reports:
            return "security"
        if patch_attempts >= self.settings.max_patch_attempts:
            logger.warning("Max patch attempts reached")
            return "failed"
        return "patch"

    def should_retest(self, state: AgentState) -> str:
        """Decide whether to re-test after patching."""
        patch_attempts = state.get("patch_attempts", 0)
        if patch_attempts < self.settings.max_patch_attempts:
            return "test"
        return "package"

    def should_security_patch(self, state: AgentState) -> str:
        """Decide whether to patch for security or proceed to package."""
        if state.get("security_passed", True):
            return "package"
        patch_attempts = state.get("patch_attempts", 0)
        if patch_attempts >= self.settings.max_security_patches + self.settings.max_patch_attempts:
            logger.warning("Max security patch attempts reached, proceeding to package")
            return "package"
        return "patch"
