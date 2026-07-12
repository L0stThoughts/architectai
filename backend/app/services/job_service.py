"""Job service — CRUD operations for jobs, artifacts, test runs, bugs, and security findings."""
import json
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Job
from app.models.artifact import Artifact
from app.models.testing import TestRun, BugReport, SecurityFinding

logger = logging.getLogger(__name__)


class JobService:
    """Manages job lifecycle and associated records in the database."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(self, project_id: str, product_goal: str) -> Job:
        """Create a new job record."""
        job = Job(
            project_id=int(project_id),
            product_goal=product_goal,
            status="PENDING",
            current_phase="PLAN",
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        logger.info("Created job %d for project %s", job.id, project_id)
        return job

    async def update_job_status(self, job_id: str, status: str, result: Optional[dict] = None) -> Job:
        """Update a job's status and optional result."""
        stmt = select(Job).where(Job.id == int(job_id))
        res = await self.db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        job.status = status
        if result is not None:
            job.result = result
        await self.db.commit()
        await self.db.refresh(job)
        logger.info("Updated job %s status to %s", job_id, status)
        return job

    async def save_artifact(self, job_id: str, path: str, content: str, artifact_type: str) -> Artifact:
        """Save a generated file artifact."""
        ext_to_lang = {".py": "python", ".ts": "typescript", ".tsx": "tsx", ".js": "javascript",
                       ".json": "json", ".css": "css", ".html": "html"}
        language = "text"
        for ext, lang in ext_to_lang.items():
            if path.endswith(ext):
                language = lang
                break
        artifact = Artifact(
            job_id=int(job_id),
            file_path=path,
            content=content,
            artifact_type=artifact_type,
            language=language,
        )
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def save_test_run(self, job_id: str, test_results: List[dict]) -> TestRun:
        """Save test run results."""
        total = len(test_results)
        passed_count = sum(1 for r in test_results if r.get("passed", False))
        failed_count = total - passed_count
        status = "PASSED" if failed_count == 0 else "FAILED"
        test_run = TestRun(
            job_id=int(job_id),
            status=status,
            results=test_results,
            total_tests=total,
            passed=passed_count,
            failed=failed_count,
        )
        self.db.add(test_run)
        await self.db.commit()
        await self.db.refresh(test_run)
        logger.info("Saved test run: %d passed, %d failed", passed_count, failed_count)
        return test_run

    async def save_bug_reports(self, job_id: str, bugs: List[dict]) -> None:
        """Save bug reports to the database."""
        for bug in bugs:
            report = BugReport(
                job_id=int(job_id),
                file_path=bug.get("file_path", ""),
                error_type=bug.get("error_type", ""),
                error_message=bug.get("error_message", ""),
                traceback_text=bug.get("traceback", ""),
                suggested_fix=bug.get("suggested_fix", ""),
                severity=bug.get("severity", "medium"),
            )
            self.db.add(report)
        await self.db.commit()
        logger.info("Saved %d bug reports for job %s", len(bugs), job_id)

    async def save_security_findings(self, job_id: str, findings: List[dict]) -> None:
        """Save security findings to the database."""
        for finding in findings:
            sf = SecurityFinding(
                job_id=int(job_id),
                file_path=finding.get("file_path", ""),
                line_number=finding.get("line_number"),
                owasp_category=finding.get("owasp_category", ""),
                severity=finding.get("severity", "info"),
                description=finding.get("description", ""),
                code_snippet=finding.get("code_snippet"),
                suggested_fix=finding.get("suggested_fix", ""),
            )
            self.db.add(sf)
        await self.db.commit()
        logger.info("Saved %d security findings for job %s", len(findings), job_id)

    async def get_job_with_artifacts(self, job_id: str) -> dict:
        """Get a job with all related data."""
        stmt = select(Job).where(Job.id == int(job_id))
        res = await self.db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            return {}
        # Artifacts
        art_stmt = select(Artifact).where(Artifact.job_id == job.id)
        art_res = await self.db.execute(art_stmt)
        artifacts = art_res.scalars().all()
        # Test runs
        tr_stmt = select(TestRun).where(TestRun.job_id == job.id)
        tr_res = await self.db.execute(tr_stmt)
        test_runs = tr_res.scalars().all()
        # Bug reports
        br_stmt = select(BugReport).where(BugReport.job_id == job.id)
        br_res = await self.db.execute(br_stmt)
        bug_reports = br_res.scalars().all()
        # Security findings
        sf_stmt = select(SecurityFinding).where(SecurityFinding.job_id == job.id)
        sf_res = await self.db.execute(sf_stmt)
        security_findings = sf_res.scalars().all()

        return {
            "job": job,
            "artifacts": artifacts,
            "test_runs": test_runs,
            "bug_reports": bug_reports,
            "security_findings": security_findings,
        }
