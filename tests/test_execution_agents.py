"""Tests for swe_af.reasoners.execution_agents — run_build_verifier reasoner function."""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# (1) Import test — run_build_verifier is importable and async
# ---------------------------------------------------------------------------


class TestImportRunBuildVerifier:
    """AC-1: run_build_verifier is importable from swe_af.reasoners.execution_agents."""

    def test_import_succeeds(self) -> None:
        from swe_af.reasoners.execution_agents import run_build_verifier

        assert callable(run_build_verifier)

    def test_is_async_function(self) -> None:
        from swe_af.reasoners.execution_agents import run_build_verifier

        assert inspect.iscoroutinefunction(run_build_verifier), (
            "run_build_verifier must be an async function"
        )


# ---------------------------------------------------------------------------
# (2) Grep test — schema=BuildVerdict present
# ---------------------------------------------------------------------------


class TestGrepSchemaBuildVerdict:
    """AC-9: schema=BuildVerdict is passed to router.harness."""

    def test_schema_argument_in_source(self) -> None:
        import swe_af.reasoners.execution_agents as mod

        source = inspect.getsource(mod)
        assert "schema=BuildVerdict" in source, (
            "router.harness call in run_build_verifier must include "
            "schema=BuildVerdict"
        )


# ---------------------------------------------------------------------------
# (3) Grep test — cwd=worktree_path present
# ---------------------------------------------------------------------------


class TestGrepCwdWorktreePath:
    """AC-10: cwd is set to worktree_path in router.harness call."""

    def test_cwd_argument_in_source(self) -> None:
        import swe_af.reasoners.execution_agents as mod

        source = inspect.getsource(mod)
        # The regex matches cwd=worktree_path or cwd=worktree_path)
        assert "cwd=worktree_path" in source, (
            "router.harness call in run_build_verifier must include "
            "cwd=worktree_path"
        )


# ---------------------------------------------------------------------------
# (4) Decorator check — @router.reasoner() is present
# ---------------------------------------------------------------------------


class TestDecoratorPresence:
    """AC-1: @router.reasoner() decorator is on the function."""

    def test_router_reasoner_decorator(self) -> None:
        import swe_af.reasoners.execution_agents as mod

        source = inspect.getsource(mod)
        # Locate the decorator immediately before the function definition
        func_def = "async def run_build_verifier("
        idx = source.find(func_def)
        assert idx > 0, "run_build_verifier function definition not found"

        # Check that the line immediately before is @router.reasoner()
        preceding = source[:idx].rstrip()
        assert preceding.endswith("@router.reasoner()"), (
            "run_build_verifier must be decorated with @router.reasoner()"
        )


# ---------------------------------------------------------------------------
# (5) BuildVerdict import check
# ---------------------------------------------------------------------------


class TestBuildVerdictImport:
    """AC-5: BuildVerdict is imported in execution_agents.py."""

    def test_build_verdict_imported(self) -> None:
        import swe_af.reasoners.execution_agents as mod

        source = inspect.getsource(mod)
        assert "from swe_af.execution.schemas import" in source
        assert "BuildVerdict" in source

    def test_build_verdict_class_has_expected_fields(self) -> None:
        from swe_af.execution.schemas import BuildVerdict

        assert BuildVerdict is not None
        fields = BuildVerdict.model_fields
        assert "passed" in fields
        assert "skip" in fields
        assert "build_errors" in fields
        assert "projects_built" in fields
        assert "summary" in fields


# ---------------------------------------------------------------------------
# (6) Function signature matches architecture spec
# ---------------------------------------------------------------------------


class TestFunctionSignature:
    """Verify function signature matches the architecture spec."""

    def test_signature_params(self) -> None:
        from swe_af.reasoners.execution_agents import run_build_verifier

        sig = inspect.signature(run_build_verifier)
        params = list(sig.parameters.keys())

        assert "files_changed" in params
        assert "worktree_path" in params
        assert "model" in params
        assert "permission_mode" in params
        assert "ai_provider" in params

    def test_parameter_defaults(self) -> None:
        from swe_af.reasoners.execution_agents import run_build_verifier

        sig = inspect.signature(run_build_verifier)
        assert sig.parameters["model"].default == "sonnet"
        assert sig.parameters["permission_mode"].default == ""
        assert sig.parameters["ai_provider"].default == "claude"


# ---------------------------------------------------------------------------
# (7) Mock test — successful harness call returns model_dump
# ---------------------------------------------------------------------------


class TestMockSuccessfulHarnessCall:
    """Mock test: patch router.harness to return a BuildVerdict and verify
    the function returns the correct model_dump()."""

    @pytest.mark.asyncio
    async def test_success_returns_model_dump(self) -> None:
        from swe_af.execution.schemas import BuildVerdict
        from swe_af.reasoners.execution_agents import run_build_verifier

        # Build a mock parsed result
        mock_parsed = BuildVerdict(
            passed=True,
            skip=False,
            build_errors=[],
            projects_built=["src/MyProject.csproj"],
            summary="Build succeeded: 0 errors",
        )
        mock_harness_result = MagicMock()
        mock_harness_result.is_error = False
        mock_harness_result.error_message = ""
        mock_harness_result.parsed = mock_parsed

        with patch("swe_af.reasoners.execution_agents.router") as mock_router:
            mock_router.harness = AsyncMock(return_value=mock_harness_result)
            mock_router.note = MagicMock()

            result = await run_build_verifier(
                files_changed=["src/MyProject.cs"],
                worktree_path="/workspace/repo",
                model="sonnet",
                permission_mode="",
                ai_provider="claude",
            )

            # Verify the result is the model_dump() of BuildVerdict
            assert result == mock_parsed.model_dump()
            assert result["passed"] is True
            assert result["projects_built"] == ["src/MyProject.csproj"]

            # Verify harness was called with correct arguments
            mock_router.harness.assert_called_once()
            call_kwargs = mock_router.harness.call_args[1]
            assert call_kwargs["schema"] is BuildVerdict
            assert call_kwargs["cwd"] == "/workspace/repo"

            # Verify build_verifier_task_prompt was called
            # (it is imported at module level, so we check the harness was
            # called with the expected task prompt structure)
            call_args = mock_router.harness.call_args[0]
            task_prompt = call_args[0]
            assert "src/MyProject.cs" in task_prompt


# ---------------------------------------------------------------------------
# (8) Mock test — exception triggers fallback BuildVerdict
# ---------------------------------------------------------------------------


class TestMockExceptionFallback:
    """Mock test: patch router.harness to raise, verify fallback BuildVerdict."""

    @pytest.mark.asyncio
    async def test_exception_returns_fallback_build_verdict(self) -> None:
        from swe_af.reasoners.execution_agents import run_build_verifier

        with patch("swe_af.reasoners.execution_agents.router") as mock_router:
            mock_router.harness = AsyncMock(side_effect=RuntimeError("Agent crash"))
            mock_router.note = MagicMock()

            result = await run_build_verifier(
                files_changed=["src/App.cs"],
                worktree_path="/workspace/repo",
                model="sonnet",
                permission_mode="",
                ai_provider="claude",
            )

            # Verify fallback: passed=False, build_errors populated
            assert result["passed"] is False
            assert result["skip"] is False
            assert len(result["build_errors"]) > 0
            assert "failed to produce a valid result" in result["build_errors"][0]
            assert result["projects_built"] == []
            assert "failed to produce a valid result" in result["summary"]


# ---------------------------------------------------------------------------
# (9) build_verifier_task_prompt integration in the reasoner
# ---------------------------------------------------------------------------


class TestTaskPromptIntegration:
    """Verify build_verifier_task_prompt is called with correct arguments."""

    @pytest.mark.asyncio
    async def test_task_prompt_arguments(self) -> None:
        from swe_af.execution.schemas import BuildVerdict
        from swe_af.reasoners.execution_agents import run_build_verifier

        mock_parsed = BuildVerdict(
            passed=True,
            skip=False,
            build_errors=[],
            projects_built=[],
            summary="ok",
        )
        mock_harness_result = MagicMock()
        mock_harness_result.is_error = False
        mock_harness_result.error_message = ""
        mock_harness_result.parsed = mock_parsed

        with patch("swe_af.reasoners.execution_agents.router") as mock_router:
            mock_router.harness = AsyncMock(return_value=mock_harness_result)
            mock_router.note = MagicMock()

            files = ["src/Example.cs", "README.md"]
            worktree = "/workspace/test"

            await run_build_verifier(
                files_changed=files,
                worktree_path=worktree,
            )

            # Verify the task_prompt includes the files
            call_args = mock_router.harness.call_args[0]
            task_prompt = call_args[0]
            assert "src/Example.cs" in task_prompt
            assert worktree in task_prompt

    @pytest.mark.asyncio
    async def test_system_prompt_in_harness_call(self) -> None:
        from swe_af.execution.schemas import BuildVerdict
        from swe_af.reasoners.execution_agents import (
            BUILD_VERIFIER_SYSTEM_PROMPT,
            run_build_verifier,
        )

        mock_parsed = BuildVerdict(passed=True)
        mock_harness_result = MagicMock()
        mock_harness_result.is_error = False
        mock_harness_result.error_message = ""
        mock_harness_result.parsed = mock_parsed

        with patch("swe_af.reasoners.execution_agents.router") as mock_router:
            mock_router.harness = AsyncMock(return_value=mock_harness_result)
            mock_router.note = MagicMock()

            await run_build_verifier(
                files_changed=[],
                worktree_path="/workspace/test",
            )

            call_kwargs = mock_router.harness.call_args[1]
            assert call_kwargs["system_prompt"] is BUILD_VERIFIER_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# (10) Provider normalization
# ---------------------------------------------------------------------------


class TestProviderNormalization:
    """Verify ai_provider is normalized to claude-code."""

    @pytest.mark.asyncio
    async def test_claude_provider_normalized(self) -> None:
        from swe_af.execution.schemas import BuildVerdict
        from swe_af.reasoners.execution_agents import run_build_verifier

        mock_parsed = BuildVerdict(passed=True)
        mock_harness_result = MagicMock()
        mock_harness_result.is_error = False
        mock_harness_result.error_message = ""
        mock_harness_result.parsed = mock_parsed

        with patch("swe_af.reasoners.execution_agents.router") as mock_router:
            mock_router.harness = AsyncMock(return_value=mock_harness_result)
            mock_router.note = MagicMock()

            await run_build_verifier(
                files_changed=[],
                worktree_path="/workspace/test",
                ai_provider="claude",
            )

            call_kwargs = mock_router.harness.call_args[1]
            assert call_kwargs["provider"] == "claude-code"

    @pytest.mark.asyncio
    async def test_custom_provider_passthrough(self) -> None:
        from swe_af.execution.schemas import BuildVerdict
        from swe_af.reasoners.execution_agents import run_build_verifier

        mock_parsed = BuildVerdict(passed=True)
        mock_harness_result = MagicMock()
        mock_harness_result.is_error = False
        mock_harness_result.error_message = ""
        mock_harness_result.parsed = mock_parsed

        with patch("swe_af.reasoners.execution_agents.router") as mock_router:
            mock_router.harness = AsyncMock(return_value=mock_harness_result)
            mock_router.note = MagicMock()

            await run_build_verifier(
                files_changed=[],
                worktree_path="/workspace/test",
                ai_provider="opencode",
            )

            call_kwargs = mock_router.harness.call_args[1]
            assert call_kwargs["provider"] == "opencode"


# ---------------------------------------------------------------------------
# (11) Fallback BuildVerdict model construction
# ---------------------------------------------------------------------------


class TestFallbackBuildVerdictModel:
    """Verify the fallback BuildVerdict is correctly constructed."""

    def test_fallback_model_has_expected_fields(self) -> None:
        """The fallback BuildVerdict constructor should produce a dict with
        all required BuildVerdict fields."""
        from pydantic import BaseModel
        from swe_af.execution.schemas import BuildVerdict

        fallback = BuildVerdict(
            passed=False,
            skip=False,
            build_errors=["Build verifier agent failed to produce a valid result."],
            projects_built=[],
            summary="Build verifier agent failed to produce a valid result.",
        )

        dumped = fallback.model_dump()

        # All fields from the schema must be present
        assert set(dumped.keys()) == {
            "passed",
            "skip",
            "build_errors",
            "projects_built",
            "summary",
        }

        assert dumped["passed"] is False
        assert dumped["skip"] is False
        assert isinstance(dumped["build_errors"], list)
        assert isinstance(dumped["projects_built"], list)
        assert isinstance(dumped["summary"], str)
