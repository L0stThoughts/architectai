"""Orchestrator agent — plans tech stack and file structure from a product goal."""
import json
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class FilePlanItem:
    """A single file to be generated."""

    path: str
    description: str
    file_type: str  # frontend / backend / config / test
    priority: int = 0


@dataclass
class PlanResult:
    """Output of the planning phase."""

    tech_stack: dict
    file_plan: List[FilePlanItem]


PLAN_PROMPT = """You are a software architect. Given this Product Goal, design a minimal viable full-stack application.

Product Goal: {goal}

Return a JSON object (no markdown fences) with:
{{
  "tech_stack": {{
    "frontend": "React/Next.js with TypeScript",
    "backend": "Python/FastAPI",
    "database": "SQLite",
    "styling": "Tailwind CSS"
  }},
  "file_plan": [
    {{
      "path": "backend/main.py",
      "description": "FastAPI entry point with CORS and routes",
      "file_type": "backend",
      "priority": 1
    }}
  ]
}}

Include 5-12 essential files. Prioritize backend first, then frontend. Include a requirements.txt and package.json where appropriate."""


class OrchestratorAgent:
    """Plans the architecture of a generated application."""

    def __init__(self, llm: object) -> None:
        self.llm = llm

    async def plan(self, product_goal: str) -> PlanResult:
        """Generate a tech stack and file plan from a product goal."""
        logger.info("Planning architecture for goal: %s", product_goal[:80])
        raw = await self._call_llm_for_plan(product_goal)
        tech_stack = raw.get("tech_stack", {})
        file_plan = [
            FilePlanItem(
                path=f["path"],
                description=f["description"],
                file_type=f.get("file_type", "backend"),
                priority=f.get("priority", 0),
            )
            for f in raw.get("file_plan", [])
        ]
        logger.info("Plan complete: %d files, stack=%s", len(file_plan), list(tech_stack.keys()))
        return PlanResult(tech_stack=tech_stack, file_plan=file_plan)

    async def _call_llm_for_plan(self, goal: str) -> dict:
        """Call LLM to produce a structured plan."""
        prompt = PLAN_PROMPT.format(goal=goal)
        response = await self.llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM plan output: %s", content[:200])
            return {
                "tech_stack": {"backend": "Python/FastAPI", "frontend": "React", "database": "SQLite"},
                "file_plan": [
                    {"path": "backend/main.py", "description": "Main application", "file_type": "backend", "priority": 1}
                ],
            }
