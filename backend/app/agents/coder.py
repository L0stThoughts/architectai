"""Coder agent — generates and patches source files using LLM."""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.agents.orchestrator import FilePlanItem

logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    """Result of generating a single file."""

    path: str
    content: str
    language: str
    tokens_used: int = 0


@dataclass
class PatchResult:
    """Result of patching a file."""

    patched_content: str
    changes_made: List[str]
    confidence: float = 0.0


GENERATE_PROMPT = """You are an expert {language} developer. Generate production-grade code for the following file.

File: {path}
Description: {description}
Tech stack: {tech_stack}

Already generated files (summaries):
{existing_files_summary}

Product goal: {product_goal}

Return ONLY the file content, no markdown fences, no explanations."""

PATCH_PROMPT = """You are a debugging expert. Fix the bug in this file.

File: {path}
Error: {error}
Traceback:
{traceback}

Current code:
```
{content}
```

Return ONLY the corrected file content, no markdown fences, no explanations."""


class CoderAgent:
    """Generates and patches code files using an LLM."""

    def __init__(self, llm: object) -> None:
        self.llm = llm

    async def generate_file(self, file_plan_item: FilePlanItem, context: dict) -> GeneratedFile:
        """Generate a single file based on the plan item and context."""
        lang = self._detect_language(file_plan_item.path)
        existing_summary = "\n".join(
            f"- {p}: {c[:80]}..." for p, c in (context.get("already_generated_files") or {}).items()
        )
        prompt = GENERATE_PROMPT.format(
            language=lang,
            path=file_plan_item.path,
            description=file_plan_item.description,
            tech_stack=context.get("tech_stack", {}),
            existing_files_summary=existing_summary or "(none yet)",
            product_goal=context.get("product_goal", ""),
        )
        response = await self.llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = self._strip_fences(content)
        logger.info("Generated file: %s (%d chars)", file_plan_item.path, len(content))
        return GeneratedFile(path=file_plan_item.path, content=content, language=lang)

    async def patch_file(self, file_path: str, content: str, bug_report: dict) -> PatchResult:
        """Patch a file based on a bug report."""
        prompt = PATCH_PROMPT.format(
            path=file_path,
            error=bug_report.get("error_message", "Unknown error"),
            traceback=bug_report.get("traceback", "N/A"),
            content=content,
        )
        response = await self.llm.ainvoke(prompt)
        patched = response.content if hasattr(response, "content") else str(response)
        patched = self._strip_fences(patched)
        logger.info("Patched file: %s", file_path)
        return PatchResult(patched_content=patched, changes_made=["Applied LLM fix"], confidence=0.8)

    @staticmethod
    def _detect_language(path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript/React",
            ".js": "JavaScript", ".jsx": "JavaScript/React", ".json": "JSON",
            ".css": "CSS", ".html": "HTML", ".sql": "SQL", ".md": "Markdown",
            ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML", ".txt": "Text",
        }
        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang
        return "Text"

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences from LLM output."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
