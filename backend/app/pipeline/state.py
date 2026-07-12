"""Enhanced LangGraph state for ArchitectAI pipeline."""
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Full production state for the ArchitectAI agentic pipeline."""

    # Core identity
    job_id: str
    project_id: str
    product_goal: str

    # Planning
    tech_stack: dict
    file_plan: List[dict]

    # Generation
    generated_files: dict
    current_file_index: int

    # Testing
    test_files: dict
    test_results: List[dict]
    bug_reports: List[dict]
    patch_attempts: int

    # Security
    security_findings: List[dict]
    security_passed: bool

    # Control flow
    current_phase: Literal[
        "PLAN", "GENERATE", "TEST", "PATCH", "SECURITY", "PACKAGE", "COMPLETE", "FAILED"
    ]
    iteration: int
    max_iterations: int
    errors: List[str]

    # Output
    bundle_path: Optional[str]
    messages: Annotated[list, add_messages]
