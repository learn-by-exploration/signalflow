# mkg/tests/test_architecture.py
"""Architecture tests — verify clean architecture boundaries.

Iterations 41-45: Ensures domain layer independence, dependency inversion,
consistent naming conventions, and no circular imports.
"""

import ast
import os
import importlib
import inspect
import sys

import pytest

MKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestLayerBoundaries:
    """Domain layer must never import from infrastructure."""

    def _get_imports_from_file(self, filepath: str) -> list[str]:
        """Parse imports from a Python file using AST."""
        with open(filepath) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return []
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def test_domain_does_not_import_infrastructure(self):
        """Domain layer must not depend on infrastructure layer."""
        domain_dir = os.path.join(MKG_ROOT, "domain")
        violations = []
        for root, _, files in os.walk(domain_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                imports = self._get_imports_from_file(fpath)
                for imp in imports:
                    if "mkg.infrastructure" in imp:
                        violations.append(f"{fpath}: imports {imp}")
        assert violations == [], f"Domain→Infrastructure violations: {violations}"

    def test_domain_does_not_import_api(self):
        """Domain layer must not depend on API layer."""
        domain_dir = os.path.join(MKG_ROOT, "domain")
        violations = []
        for root, _, files in os.walk(domain_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                imports = self._get_imports_from_file(fpath)
                for imp in imports:
                    if "mkg.api" in imp:
                        violations.append(f"{fpath}: imports {imp}")
        assert violations == [], f"Domain→API violations: {violations}"

    def test_infrastructure_only_imports_domain_interfaces(self):
        """Infrastructure imports from domain should only be interfaces."""
        infra_dir = os.path.join(MKG_ROOT, "infrastructure")
        violations = []
        for root, _, files in os.walk(infra_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                imports = self._get_imports_from_file(fpath)
                for imp in imports:
                    if imp.startswith("mkg.domain") and "interfaces" not in imp:
                        violations.append(f"{fpath}: imports {imp} (should use interfaces)")
        assert violations == [], f"Infrastructure→Domain non-interface imports: {violations}"


class TestNoCircularImports:
    """All MKG modules should import without circular dependency errors."""

    def _find_python_modules(self, base_dir: str, prefix: str) -> list[str]:
        modules = []
        mkg_parent = os.path.dirname(MKG_ROOT)
        for root, _, files in os.walk(base_dir):
            for fname in files:
                if not fname.endswith(".py") or fname == "__init__.py":
                    continue
                rel = os.path.relpath(os.path.join(root, fname), mkg_parent)
                module = rel.replace(os.sep, ".").replace(".py", "")
                modules.append(module)
        return modules

    def test_all_domain_modules_importable(self):
        """All domain modules should be importable without errors."""
        domain_dir = os.path.join(MKG_ROOT, "domain")
        modules = self._find_python_modules(domain_dir, "mkg.domain")
        for mod in modules:
            try:
                importlib.import_module(mod)
            except ImportError as e:
                pytest.fail(f"Failed to import {mod}: {e}")

    def test_all_infrastructure_modules_importable(self):
        """All infrastructure modules should be importable without errors."""
        infra_dir = os.path.join(MKG_ROOT, "infrastructure")
        modules = self._find_python_modules(infra_dir, "mkg.infrastructure")
        for mod in modules:
            try:
                importlib.import_module(mod)
            except ImportError as e:
                pytest.fail(f"Failed to import {mod}: {e}")


class TestNamingConventions:
    """Verify consistent naming across the codebase."""

    def test_all_services_use_snake_case_methods(self):
        """All public methods should be snake_case."""
        import mkg.domain.services as svc_pkg
        svc_dir = os.path.dirname(svc_pkg.__file__)
        for fname in os.listdir(svc_dir):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            mod_name = f"mkg.domain.services.{fname[:-3]}"
            try:
                mod = importlib.import_module(mod_name)
            except ImportError:
                continue
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if not name[0].isupper():
                    continue
                for method_name, _ in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if method_name.startswith("_"):
                        continue
                    assert method_name == method_name.lower() or "_" in method_name, \
                        f"{name}.{method_name} should be snake_case"

    def test_all_classes_use_pascal_case(self):
        """All public classes should be PascalCase."""
        import mkg.domain.services as svc_pkg
        svc_dir = os.path.dirname(svc_pkg.__file__)
        for fname in os.listdir(svc_dir):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            mod_name = f"mkg.domain.services.{fname[:-3]}"
            try:
                mod = importlib.import_module(mod_name)
            except ImportError:
                continue
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if name.startswith("_"):
                    continue
                # Skip imported classes (only check locally defined)
                if getattr(obj, "__module__", "") != mod_name:
                    continue
                # Class names should start with uppercase
                assert name[0].isupper(), f"Class {name} in {mod_name} should be PascalCase"


class TestDependencyInjection:
    """Services should accept dependencies via constructor, not create them."""

    def test_services_with_storage_dependency(self):
        """Services that need GraphStorage should accept it via __init__."""
        from mkg.domain.services.entity_service import EntityService
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        from mkg.domain.services.propagation_engine import PropagationEngine
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder
        from mkg.domain.services.impact_table import ImpactTableBuilder
        from mkg.domain.services.tribal_knowledge import TribalKnowledgeInput

        for cls in [EntityService, WeightAdjustmentService, PropagationEngine,
                    CausalChainBuilder, ImpactTableBuilder, TribalKnowledgeInput]:
            sig = inspect.signature(cls.__init__)
            params = list(sig.parameters.keys())
            assert "storage" in params, \
                f"{cls.__name__}.__init__ should accept 'storage' parameter"

    def test_graph_mutation_uses_di(self):
        from mkg.domain.services.graph_mutation import GraphMutationService
        sig = inspect.signature(GraphMutationService.__init__)
        params = list(sig.parameters.keys())
        assert "storage" in params
        assert "registry" in params
