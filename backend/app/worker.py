"""Background worker that runs the ArchitectAI pipeline."""
import asyncio
import logging
from typing import Optional

from app.config import Settings
from app.database import async_session
from app.pipeline.graph import ArchitectAIGraph
from app.pipeline.state import AgentState
from app.services.event_service import EventService
from app.services.job_service import JobService

logger = logging.getLogger(__name__)


async def run_job(
    job_id: str,
    project_id: str,
    product_goal: str,
    settings: Settings,
) -> None:
    """Entry point for running a generation job in the background."""
    logger.info("Starting job %s for project %s", job_id, project_id)
    event_service = EventService(settings.redis_url)

    async with async_session() as db:
        job_service = JobService(db)

        try:
            await job_service.update_job_status(job_id, "RUNNING")
            await event_service.publish(job_id, "phase_change", {"phase": "PLAN"})

            # Initialize LLM
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0.2,
                )
            except Exception as exc:
                logger.error("Failed to initialize LLM: %s", exc)
                await job_service.update_job_status(job_id, "FAILED", {"error": str(exc)})
                await event_service.publish(job_id, "error", {"message": str(exc)})
                return

            # Build and run pipeline
            graph = ArchitectAIGraph(llm, settings)
            compiled = graph.build()

            initial_state: AgentState = {
                "job_id": job_id,
                "project_id": project_id,
                "product_goal": product_goal,
                "tech_stack": {},
                "file_plan": [],
                "generated_files": {},
                "current_file_index": 0,
                "test_files": {},
                "test_results": [],
                "bug_reports": [],
                "patch_attempts": 0,
                "security_findings": [],
                "security_passed": False,
                "current_phase": "PLAN",
                "iteration": 0,
                "max_iterations": 10,
                "errors": [],
                "bundle_path": None,
                "messages": [],
            }

            # Run the graph
            final_state = await compiled.ainvoke(initial_state)

            # Save artifacts
            for path, content in final_state.get("generated_files", {}).items():
                await job_service.save_artifact(job_id, path, content, "generated")
                await event_service.publish(job_id, "file_generated", {"path": path})

            # Save test results
            if final_state.get("test_results"):
                await job_service.save_test_run(job_id, final_state["test_results"])
                await event_service.publish(job_id, "test_result", {
                    "total": len(final_state["test_results"]),
                    "passed": sum(1 for r in final_state["test_results"] if r.get("passed")),
                })

            # Save bug reports
            if final_state.get("bug_reports"):
                await job_service.save_bug_reports(job_id, final_state["bug_reports"])

            # Save security findings
            if final_state.get("security_findings"):
                await job_service.save_security_findings(job_id, final_state["security_findings"])

            # Determine final status
            phase = final_state.get("current_phase", "COMPLETE")
            if phase == "FAILED":
                status = "FAILED"
            elif final_state.get("security_findings") and not final_state.get("security_passed"):
                status = "COMPLETE_WITH_WARNINGS"
            else:
                status = "COMPLETE"

            result = {
                "bundle_path": final_state.get("bundle_path"),
                "files_generated": len(final_state.get("generated_files", {})),
                "tests_passed": sum(1 for r in final_state.get("test_results", []) if r.get("passed")),
                "security_findings": len(final_state.get("security_findings", [])),
            }
            await job_service.update_job_status(job_id, status, result)
            await event_service.publish(job_id, "complete", {"status": status, **result})
            logger.info("Job %s completed with status %s", job_id, status)

        except Exception as exc:
            logger.exception("Job %s failed: %s", job_id, exc)
            await job_service.update_job_status(job_id, "FAILED", {"error": str(exc)})
            await event_service.publish(job_id, "error", {"message": str(exc)})
