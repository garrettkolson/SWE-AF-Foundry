"""Prompt builder for the Build Verifier agent role.

The build verifier runs ``dotnet build`` on a codebase to confirm that
a given set of changes compiles successfully. It is invoked after the
coder finishes work on issues that modify C# / .NET projects.
"""

from __future__ import annotations

SYSTEM_PROMPT: str = """\
You are a build verifier operating inside an autonomous agent pipeline.
Your sole responsibility is to confirm that code changes compile and build
successfully before they are marked complete.

## Your Responsibilities

1. Identify all .csproj files in the repository using GLOB.
2. Run ``dotnet build`` on each project or the solution root.
3. Report the build result clearly: did it succeed or fail?

## Build Verdict

Return your result as a JSON object with the following shape:

{
    "build_successful": true | false,
    "error_message": "summary of any errors, or empty string if success",
    "projects_verified": ["list", "of", "project", "paths"],
    "build_output": "brief summary of dotnet build output"
}

## Important Constraints

- Do NOT modify the codebase. You are a verifier, not a fixer.
- If ``dotnet`` is not installed, report build_successful=false with an
  explanation in error_message.
- Always run ``dotnet build`` (not just ``dotnet restore``) to catch
  compilation errors.\
"""


def _is_cs_file(path: str) -> bool:
    """Return True if the given path looks like a C# source file."""
    return path.endswith(".cs")


def build_verifier_task_prompt(
    files_changed: list[str],
    worktree_path: str = "",
) -> str:
    """Build the task prompt for the build verifier agent.

    When the provided files_changed list contains at least one ``.cs`` file
    the prompt instructs the agent to run ``dotnet build`` and identify
    relevant ``.csproj`` projects.  When no ``.cs`` files are present the
    prompt instructs the agent to skip verification.

    Args:
        files_changed: List of file paths that were changed in the current
            issue.
        worktree_path: Absolute path to the working directory (default "").

    Returns:
        A fully-formed task prompt string.
    """
    cs_files = [f for f in files_changed if _is_cs_file(f)]

    sections: list[str] = []

    if not cs_files:
        sections.append(
            "## Build Verification: Skipped\n"
            "No C# files changed in this issue. "
            "There is nothing to build-verify. Return the following JSON "
            "and mark the build as not applicable:\n"
            "{\n"
            '    "build_successful": true,\n'
            '    "error_message": "No C# files changed — build verification skipped",\n'
            '    "projects_verified": [],\n'
            '    "build_output": "skipped: no C# files to verify"\n'
            "}"
        )
    else:
        sections.append(
            "## Build Verification\n"
            "C# source files have changed. Run ``dotnet build`` to confirm "
            "everything compiles successfully.\n"
        )

        sections.append(
            f"### Changed C# Files\n"
            "Use GLOB to find any ``.csproj`` files that contain or reference "
            "the following changed source files:\n"
        )
        for f in cs_files:
            sections.append(f"- `{f}`")

        if worktree_path:
            sections.append(f"\n### Working Directory\n`{worktree_path}`")

        sections.append(
            "\n### Instructions\n"
            "1. Use GLOB to find ``*.csproj`` files.\n"
            "2. Identify which projects reference the changed ``.cs`` files.\n"
            "3. Run ``dotnet build`` on those projects (or on the solution root).\n"
            "4. Record the build output.\n"
            "5. Return a BuildVerdict JSON object with:\n"
            "   - ``build_successful``: true if the build passed, false otherwise\n"
            "   - ``error_message``: summary of any errors\n"
            "   - ``projects_verified``: list of project paths built\n"
            "   - ``build_output``: brief summary of output"
        )

    return "\n".join(sections)
