import asyncio
from pathlib import Path

from swe_af.execution.coding_loop import run_coding_loop
from swe_af.execution.schemas import DAGState, ExecutionConfig, IssueOutcome


def _make_dag_state(tmp_path: Path, build_id: str) -> DAGState:
    return DAGState(
        repo_path=str(tmp_path),
        artifacts_dir=str(tmp_path / ".artifacts"),
        build_id=build_id,
    )


def test_run_coding_loop_propagates_permission_mode_to_all_agents(tmp_path: Path) -> None:
    dag_state = _make_dag_state(tmp_path, build_id="permtest1")
    config = ExecutionConfig(max_coding_iterations=1, permission_mode="bypassPermissions")
    issue = {"name": "flagged-issue", "guidance": {"needs_deeper_qa": True}}
    observed_modes: dict[str, str] = {}

    async def call_fn(target: str, **kwargs):
        observed_modes[target.split(".")[-1]] = kwargs.get("permission_mode", "")
        if target.endswith(".run_coder"):
            return {"files_changed": []}
        if target.endswith(".run_qa"):
            return {"passed": True, "summary": "qa ok", "test_failures": []}
        if target.endswith(".run_code_reviewer"):
            return {"approved": True, "blocking": False, "summary": "review ok", "debt_items": []}
        if target.endswith(".run_qa_synthesizer"):
            return {"action": "approve", "summary": "approved", "stuck": False}
        raise AssertionError(f"Unexpected target: {target}")

    result = asyncio.run(
        run_coding_loop(
            issue=issue,
            dag_state=dag_state,
            call_fn=call_fn,
            node_id="swe-planner",
            config=config,
            note_fn=None,
            memory_fn=None,
        ),
    )

    assert result.outcome == IssueOutcome.COMPLETED
    for agent_name in ("run_coder", "run_qa", "run_code_reviewer", "run_qa_synthesizer"):
        assert observed_modes[agent_name] == "bypassPermissions"
