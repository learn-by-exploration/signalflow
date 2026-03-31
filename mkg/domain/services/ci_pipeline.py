# mkg/domain/services/ci_pipeline.py
"""CIPipeline — CI/CD pipeline configuration and validation for MKG.

R-CI1 through R-CI5: Defines pipeline stages, validates dependencies,
provides execution ordering, and dry-run simulation.
"""

from __future__ import annotations

from typing import Any, Optional


class CIPipeline:
    """CI/CD pipeline configuration and validation.

    Manages ordered stages with dependencies, validates configuration,
    and produces execution plans.
    """

    def __init__(self) -> None:
        self.stages: dict[str, dict[str, Any]] = {}

    def add_stage(
        self,
        name: str,
        command: str,
        order: int,
        depends_on: Optional[list[str]] = None,
    ) -> None:
        """Add a pipeline stage.

        Args:
            name: Stage name (unique).
            command: Shell command to execute.
            order: Execution order (lower = earlier).
            depends_on: List of stage names this stage depends on.
        """
        self.stages[name] = {
            "name": name,
            "command": command,
            "order": order,
            "depends_on": depends_on or [],
        }

    def get_ordered_stages(self) -> list[dict[str, Any]]:
        """Get stages sorted by execution order.

        Returns:
            List of stage dicts sorted by order field.
        """
        return sorted(self.stages.values(), key=lambda s: s["order"])

    def validate(self) -> list[str]:
        """Validate pipeline configuration.

        Returns:
            List of error strings. Empty list = valid.
        """
        errors: list[str] = []

        if not self.stages:
            errors.append("Pipeline has no stages defined")
            return errors

        # Check for duplicate orders
        orders = [s["order"] for s in self.stages.values()]
        if len(orders) != len(set(orders)):
            errors.append("Duplicate order values found in pipeline stages")

        # Check dependencies exist
        for stage in self.stages.values():
            for dep in stage["depends_on"]:
                if dep not in self.stages:
                    errors.append(
                        f"Stage '{stage['name']}' depends on '{dep}' which does not exist"
                    )

        return errors

    def dry_run(self) -> dict[str, Any]:
        """Simulate a pipeline run without executing commands.

        Returns:
            Dict with valid flag and execution plan (steps).
        """
        errors = self.validate()
        if errors:
            return {"valid": False, "errors": errors, "steps": []}

        steps: list[dict[str, Any]] = []
        for i, stage in enumerate(self.get_ordered_stages(), start=1):
            steps.append({
                "step": i,
                "stage": stage["name"],
                "command": stage["command"],
                "depends_on": stage["depends_on"],
            })

        return {"valid": True, "steps": steps}

    @classmethod
    def create_default(cls) -> CIPipeline:
        """Create the default MKG CI pipeline.

        Returns:
            Configured pipeline with lint, test, and build stages.
        """
        pipeline = cls()
        pipeline.add_stage("lint", command="ruff check mkg/", order=1)
        pipeline.add_stage("test", command="pytest mkg/tests/ -v", order=2, depends_on=["lint"])
        pipeline.add_stage("build", command="docker build -t mkg .", order=3, depends_on=["test"])
        return pipeline
