"""Tests for BuildVerdict schema, ROLE_TO_MODEL_FIELD mapping, and
ExecutionConfig.build_verifier_model property."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from swe_af.execution.schemas import (
    BuildVerdict,
    ExecutionConfig,
    ROLE_TO_MODEL_FIELD,
)


# ---------------------------------------------------------------------------
# AC-1: BuildVerdict instantiation with all fields set and type checks
# ---------------------------------------------------------------------------


class TestBuildVerdictAllFields(unittest.TestCase):
    def test_instantiate_with_all_fields(self) -> None:
        v = BuildVerdict(
            passed=True,
            skip=False,
            build_errors=["error CS001: test error"],
            projects_built=["src/app.csproj"],
            summary="Build succeeded.",
        )
        self.assertEqual(v.passed, True)
        self.assertIsInstance(v.passed, bool)
        self.assertEqual(v.skip, False)
        self.assertIsInstance(v.skip, bool)
        self.assertEqual(v.build_errors, ["error CS001: test error"])
        self.assertIsInstance(v.build_errors, list)
        self.assertIsInstance(v.build_errors[0], str)
        self.assertEqual(v.projects_built, ["src/app.csproj"])
        self.assertIsInstance(v.projects_built, list)
        self.assertIsInstance(v.projects_built[0], str)
        self.assertEqual(v.summary, "Build succeeded.")
        self.assertIsInstance(v.summary, str)

    def test_failed_build(self) -> None:
        v = BuildVerdict(
            passed=False,
            skip=False,
            build_errors=["error CS0103: name not found"],
            projects_built=["src/lib.csproj"],
            summary="Build failed: 1 error(s)",
        )
        self.assertEqual(v.passed, False)
        self.assertEqual(len(v.build_errors), 1)


# ---------------------------------------------------------------------------
# AC-1: BuildVerdict with defaults (skip default is False)
# ---------------------------------------------------------------------------


class TestBuildVerdictDefaults(unittest.TestCase):
    def test_skip_default_is_false(self) -> None:
        """skip defaults to False, not True."""
        v = BuildVerdict(passed=True)
        self.assertEqual(v.skip, False)

    def test_all_defaults(self) -> None:
        """Only passed is required; other fields get default values."""
        v = BuildVerdict(passed=True)
        self.assertEqual(v.skip, False)
        self.assertEqual(v.build_errors, [])
        self.assertEqual(v.projects_built, [])
        self.assertEqual(v.summary, "")

    def test_passed_required(self) -> None:
        """passed is a required field — omitting it raises ValidationError."""
        with self.assertRaises(ValidationError):
            BuildVerdict()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# AC-3: build_verifier_model key in ROLE_TO_MODEL_FIELD
# ---------------------------------------------------------------------------


class TestRoleToModelFieldBuildVerifier(unittest.TestCase):
    def test_value_exists_in_mapping(self) -> None:
        """Assert 'build_verifier_model' appears in ROLE_TO_MODEL_FIELD values."""
        self.assertIn("build_verifier_model", ROLE_TO_MODEL_FIELD.values())

    def test_key_value(self) -> None:
        self.assertEqual(ROLE_TO_MODEL_FIELD["build_verifier"], "build_verifier_model")


# ---------------------------------------------------------------------------
# AC-4: ExecutionConfig.build_verifier_model property
# ---------------------------------------------------------------------------


class TestExecutionConfigBuildVerifierModel(unittest.TestCase):
    def test_property_exists(self) -> None:
        config = ExecutionConfig()
        self.assertTrue(hasattr(config, "build_verifier_model"))

    def test_property_returns_nonempty_string(self) -> None:
        config = ExecutionConfig()
        val = config.build_verifier_model
        self.assertIsInstance(val, str)
        self.assertTrue(len(val) > 0)

    def test_property_resolves_default_model(self) -> None:
        """Default runtime is claude_code → build_verifier_model = 'sonnet'."""
        config = ExecutionConfig()
        self.assertEqual(config.build_verifier_model, "sonnet")


# ---------------------------------------------------------------------------
# AC-5: BuildVerdict.model_dump() returns expected dict
# ---------------------------------------------------------------------------


class TestBuildVerdictModelDump(unittest.TestCase):
    def test_model_dump_all_fields(self) -> None:
        v = BuildVerdict(
            passed=True,
            skip=False,
            build_errors=["error 1", "error 2"],
            projects_built=["a.csproj", "b.csproj"],
            summary="ok",
        )
        dumped = v.model_dump()
        self.assertEqual(dumped, {
            "passed": True,
            "skip": False,
            "build_errors": ["error 1", "error 2"],
            "projects_built": ["a.csproj", "b.csproj"],
            "summary": "ok",
        })

    def test_model_dump_defaults(self) -> None:
        v = BuildVerdict(passed=False)
        dumped = v.model_dump()
        self.assertEqual(dumped, {
            "passed": False,
            "skip": False,
            "build_errors": [],
            "projects_built": [],
            "summary": "",
        })


# ---------------------------------------------------------------------------
# Module importability (acceptance criterion)
# ---------------------------------------------------------------------------


class TestBuildVerdictImportability(unittest.TestCase):
    def test_import_build_verdict(self) -> None:
        """Verify: python -c "from swe_af.execution.schemas import BuildVerdict; print('OK')"""
        from swe_af.execution.schemas import BuildVerdict  # noqa: F401


if __name__ == "__main__":
    unittest.main()
