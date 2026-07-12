"""FastAPI application with modular route organization."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import init_db, get_db
from app.models.project import Project, Job
from app.models.artifact import Artifact
from app.models.testing import TestRun, BugReport, SecurityFinding
from app.schemas.project import (
    ProjectCreate, ProjectRead, JobCreate, JobRead,
    ArtifactRead, TestRunRead, BugReportRead, SecurityFindingRead,
)
from app.services.event_service import EventService
from app.services.job_service import JobService
from app.services.bundle_service import BundleService
from app.worker import run_job

logger = logging.getLogger(__name__)

# --- Shared services ---
event_service = EventService(settings.redis_url)
bundle_service = BundleService(settings.bundles_dir)
_running_jobs: dict = {}


# --- Lifespan (replaces deprecated on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    await init_db()
    logger.info("ArchitectAI started — database initialized")
    yield
    # Cleanup: cancel any running jobs
    for job_id, task in _running_jobs.items():
        if not task.done():
            task.cancel()
            logger.info("Cancelled running job %s on shutdown", job_id)
    _running_jobs.clear()
    logger.info("ArchitectAI shutdown complete")


app = FastAPI(
    title="ArchitectAI",
    version="0.2.0",
    description="Autonomous code generation platform with agentic pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Projects
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/v1/projects", response_model=ProjectRead, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    """Create a new project."""
    project = Project(
        name=data.name,
        description=data.description,
        product_goal=data.product_goal,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@app.get("/api/v1/projects", response_model=List[ProjectRead])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List projects with pagination."""
    stmt = select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/api/v1/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)) -> Project:
    """Get a project with its jobs."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.delete("/api/v1/projects/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a project and cascade to jobs."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Jobs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/v1/projects/{project_id}/jobs", response_model=JobRead, status_code=201)
async def create_job_route(
    project_id: int,
    data: Optional[JobCreate] = None,
    db: AsyncSession = Depends(get_db),
) -> Job:
    """Create a job and launch it as a background task."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    goal = (data.product_goal if data and data.product_goal else project.product_goal) or ""
    job_service = JobService(db)
    job = await job_service.create_job(str(project_id), goal)

    task = asyncio.create_task(
        run_job(str(job.id), str(project_id), goal, settings)
    )
    _running_jobs[str(job.id)] = task
    return job


@app.get("/api/v1/jobs/{job_id}", response_model=JobRead)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)) -> Job:
    """Get job details."""
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/v1/jobs/{job_id}/events/stream")
async def job_event_stream(job_id: int) -> StreamingResponse:
    """SSE stream of job events."""
    import json as _json

    async def generate():
        async for event in event_service.subscribe(str(job_id)):
            yield f"data: {_json.dumps(event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/jobs/{job_id}/events")
async def job_events_history(job_id: int, limit: int = Query(100, ge=1, le=500)) -> list:
    """Get historical events for a job."""
    return await event_service.get_history(str(job_id), limit)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Artifacts, Tests, Security
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/v1/jobs/{job_id}/artifacts", response_model=List[ArtifactRead])
async def list_artifacts(job_id: int, db: AsyncSession = Depends(get_db)) -> list:
    """List artifacts for a job."""
    stmt = select(Artifact).where(Artifact.job_id == job_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/api/v1/artifacts/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)) -> Artifact:
    """Get artifact content."""
    stmt = select(Artifact).where(Artifact.id == artifact_id)
    result = await db.execute(stmt)
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.get("/api/v1/jobs/{job_id}/tests", response_model=List[TestRunRead])
async def list_test_runs(job_id: int, db: AsyncSession = Depends(get_db)) -> list:
    """List test runs for a job."""
    stmt = select(TestRun).where(TestRun.job_id == job_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/api/v1/jobs/{job_id}/bugs", response_model=List[BugReportRead])
async def list_bug_reports(job_id: int, db: AsyncSession = Depends(get_db)) -> list:
    """List bug reports for a job."""
    stmt = select(BugReport).where(BugReport.job_id == job_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/api/v1/jobs/{job_id}/security", response_model=List[SecurityFindingRead])
async def list_security_findings(job_id: int, db: AsyncSession = Depends(get_db)) -> list:
    """List security findings for a job."""
    stmt = select(SecurityFinding).where(SecurityFinding.job_id == job_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@app.get("/api/v1/jobs/{job_id}/bundle")
async def download_bundle(job_id: int) -> FileResponse:
    """Download the generated ZIP bundle."""
    path = bundle_service.get_bundle_path(str(job_id))
    if not path:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return FileResponse(path, media_type="application/zip", filename=f"architectai-{job_id}.zip")


@app.post("/api/v1/jobs/{job_id}/retry", response_model=JobRead, status_code=201)
async def retry_job(job_id: int, db: AsyncSession = Depends(get_db)) -> Job:
    """Re-launch a failed job."""
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_service = JobService(db)
    new_job = await job_service.create_job(str(job.project_id), job.product_goal or "")
    task = asyncio.create_task(
        run_job(str(new_job.id), str(job.project_id), job.product_goal or "", settings)
    )
    _running_jobs[str(new_job.id)] = task
    return new_job


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Health & Stats
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """Health check endpoint."""
    db_ok = False
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "0.2.0",
        "db_connected": db_ok,
        "active_jobs": len([t for t in _running_jobs.values() if not t.done()]),
    }


@app.get("/api/v1/stats")
async def stats(db: AsyncSession = Depends(get_db)) -> dict:
    """Quick platform stats for the dashboard."""
    from sqlalchemy import func
    project_count = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    job_count = (await db.execute(select(func.count(Job.id)))).scalar() or 0
    artifact_count = (await db.execute(select(func.count(Artifact.id)))).scalar() or 0
    return {
        "projects": project_count,
        "jobs": job_count,
        "artifacts": artifact_count,
        "active_jobs": len([t for t in _running_jobs.values() if not t.done()]),
    }
