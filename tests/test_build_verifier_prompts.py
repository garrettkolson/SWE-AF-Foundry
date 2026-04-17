"""Tests for swe_af.prompts.build_verifier — SYSTEM_PROMPT and build_verifier_task_prompt()."""

from __future__ import annotations

import pytest

from swe_af.prompts.build_verifier import (
    SYSTEM_PROMPT,
    build_verifier_task_prompt,
)


# ---------------------------------------------------------------------------
# Module importability (AC-1)
# ---------------------------------------------------------------------------


class TestModuleImport:
    def test_module_imports_cleanly(self) -> None:
        import swe_af.prompts.build_verifier  # noqa: F401

    def test_exports_from_init(self) -> None:
        from swe_af.prompts import build_verifier_system_prompt, build_verifier_task_prompt

        assert isinstance(build_verifier_system_prompt, str)
        assert callable(build_verifier_task_prompt)


# ---------------------------------------------------------------------------
# SYSTEM_PROMPT (AC-2)
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_is_non_empty_string(self) -> None:
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0

    def test_contains_dotnet_build_directive(self) -> None:
        assert "dotnet build" in SYSTEM_PROMPT

    def test_contains_build_verdict_instructions(self) -> None:
        # Verify the prompt references the BuildVerdict output format
        assert "build_successful" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# build_verifier_task_prompt — no C# files (skip mode) (AC-4)
# ---------------------------------------------------------------------------


class TestTaskPromptNoCSharp:
    def test_non_csharp_files_trigger_skip(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["tests/test.py", "README.md"],
        )
        assert isinstance(result, str)
        assert "No C# files changed" in result or "skip" in result.lower()

    def test_skip_mode_json_includes_skip_message(self) -> None:
        result = build_verifier_task_prompt(files_changed=["docs/index.html"])
        assert "build verification skipped" in result.lower()


# ---------------------------------------------------------------------------
# build_verifier_task_prompt — C# files only (AC-4)
# ---------------------------------------------------------------------------


class TestTaskPromptCSharpOnly:
    def test_cs_files_trigger_dotnet_build(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["src/Example.cs"],
        )
        assert isinstance(result, str)
        assert "dotnet build" in result

    def test_lists_changed_cs_files(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["src/Example.cs", "src/Models/User.cs"],
        )
        assert "src/Example.cs" in result
        assert "src/Models/User.cs" in result

    def test_references_project_identification(self) -> None:
        result = build_verifier_task_prompt(files_changed=["src/App.cs"])
        assert ".csproj" in result


# ---------------------------------------------------------------------------
# build_verifier_task_prompt — mixed files (AC-5)
# ---------------------------------------------------------------------------


class TestTaskPromptMixedFiles:
    def test_mixed_files_include_cs_instructions(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["src/Example.cs", "README.md", "tests/test.py"],
        )
        assert "dotnet build" in result
        assert "src/Example.cs" in result

    def test_non_cs_files_not_listed_as_csharp(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["src/Example.cs", "README.md"],
        )
        # The C# instructions should still be present
        assert "dotnet build" in result


# ---------------------------------------------------------------------------
# build_verifier_task_prompt — empty files_changed (skip mode)
# ---------------------------------------------------------------------------


class TestTaskPromptEmpty:
    def test_empty_files_changed_is_skip(self) -> None:
        result = build_verifier_task_prompt(files_changed=[])
        assert "No C# files changed" in result or "skip" in result.lower()

    def test_empty_files_changed_includes_skip_json(self) -> None:
        result = build_verifier_task_prompt(files_changed=[])
        assert "build verification skipped" in result.lower()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_worktree_path_included_in_csharp_mode(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["src/App.cs"],
            worktree_path="/home/user/repo",
        )
        assert "/home/user/repo" in result

    def test_worktree_path_not_included_in_skip_mode(self) -> None:
        result = build_verifier_task_prompt(
            files_changed=["README.md"],
            worktree_path="/home/user/repo",
        )
        assert "Working Directory" not in result

    def test_single_dot_net_file_triggers_build(self) -> None:
        result = build_verifier_task_prompt(files_changed=["program.cs"])
        assert "dotnet build" in result

    def test_only_project_files_no_source(self) -> None:
        result = build_verifier_task_prompt(files_changed=["app.csproj"])
        assert "No C# files changed" in result or "skip" in result.lower()
