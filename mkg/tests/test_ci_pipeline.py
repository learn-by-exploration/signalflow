# mkg/tests/test_ci_pipeline.py
"""Tests for CIPipeline — CI/CD pipeline configuration and validation.

R-CI1 through R-CI5: Pipeline stage definition, dependency validation,
execution ordering, and dry-run simulation.
"""

import pytest


class TestCIPipeline:

    @pytest.fixture
    def pipeline(self):
        from mkg.domain.services.ci_pipeline import CIPipeline
        return CIPipeline()

    def test_add_stage(self, pipeline):
        pipeline.add_stage("lint", command="ruff check .", order=1)
        assert len(pipeline.stages) == 1

    def test_stages_ordered(self, pipeline):
        pipeline.add_stage("test", command="pytest", order=2)
        pipeline.add_stage("lint", command="ruff check .", order=1)
        pipeline.add_stage("build", command="docker build", order=3)
        ordered = pipeline.get_ordered_stages()
        assert [s["name"] for s in ordered] == ["lint", "test", "build"]

    def test_validate_no_stages(self, pipeline):
        errors = pipeline.validate()
        assert any("no stages" in e.lower() for e in errors)

    def test_validate_duplicate_order(self, pipeline):
        pipeline.add_stage("lint", command="ruff", order=1)
        pipeline.add_stage("test", command="pytest", order=1)
        errors = pipeline.validate()
        assert any("duplicate" in e.lower() for e in errors)

    def test_validate_valid_pipeline(self, pipeline):
        pipeline.add_stage("lint", command="ruff", order=1)
        pipeline.add_stage("test", command="pytest", order=2)
        pipeline.add_stage("build", command="docker build", order=3)
        errors = pipeline.validate()
        assert errors == []

    def test_dry_run_returns_plan(self, pipeline):
        pipeline.add_stage("lint", command="ruff check .", order=1)
        pipeline.add_stage("test", command="pytest mkg/", order=2)
        plan = pipeline.dry_run()
        assert plan["valid"] is True
        assert len(plan["steps"]) == 2
        assert plan["steps"][0]["stage"] == "lint"

    def test_add_stage_with_depends_on(self, pipeline):
        pipeline.add_stage("lint", command="ruff", order=1)
        pipeline.add_stage("test", command="pytest", order=2, depends_on=["lint"])
        stage = pipeline.stages["test"]
        assert "lint" in stage["depends_on"]

    def test_validate_missing_dependency(self, pipeline):
        pipeline.add_stage("test", command="pytest", order=1, depends_on=["lint"])
        errors = pipeline.validate()
        assert any("lint" in e for e in errors)

    def test_get_default_pipeline(self):
        from mkg.domain.services.ci_pipeline import CIPipeline
        pipeline = CIPipeline.create_default()
        assert len(pipeline.stages) >= 3
        errors = pipeline.validate()
        assert errors == []
