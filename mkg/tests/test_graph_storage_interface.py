# mkg/tests/test_graph_storage_interface.py
"""Tests for GraphStorage interface contract.

Verifies that the abstract interface defines all required methods
with correct signatures per R-PLAT-20, R-MF6.
"""

import inspect
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

import pytest


class TestGraphStorageInterfaceContract:
    """Verify the GraphStorage interface defines the full contract."""

    def _get_interface(self):
        from mkg.domain.interfaces.graph_storage import GraphStorage
        return GraphStorage

    def test_is_abstract_base_class(self):
        """GraphStorage must be an ABC — cannot be instantiated directly."""
        cls = self._get_interface()
        assert issubclass(cls, ABC)
        with pytest.raises(TypeError):
            cls()

    # --- Entity CRUD Methods ---

    def test_has_create_entity_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "create_entity")
        assert getattr(cls.create_entity, "__isabstractmethod__", False)

    def test_has_get_entity_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "get_entity")
        assert getattr(cls.get_entity, "__isabstractmethod__", False)

    def test_has_update_entity_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "update_entity")
        assert getattr(cls.update_entity, "__isabstractmethod__", False)

    def test_has_delete_entity_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "delete_entity")
        assert getattr(cls.delete_entity, "__isabstractmethod__", False)

    def test_has_find_entities_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "find_entities")
        assert getattr(cls.find_entities, "__isabstractmethod__", False)

    # --- Edge CRUD Methods ---

    def test_has_create_edge_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "create_edge")
        assert getattr(cls.create_edge, "__isabstractmethod__", False)

    def test_has_get_edge_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "get_edge")
        assert getattr(cls.get_edge, "__isabstractmethod__", False)

    def test_has_update_edge_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "update_edge")
        assert getattr(cls.update_edge, "__isabstractmethod__", False)

    def test_has_delete_edge_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "delete_edge")
        assert getattr(cls.delete_edge, "__isabstractmethod__", False)

    def test_has_find_edges_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "find_edges")
        assert getattr(cls.find_edges, "__isabstractmethod__", False)

    # --- Traversal Methods ---

    def test_has_get_neighbors_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "get_neighbors")
        assert getattr(cls.get_neighbors, "__isabstractmethod__", False)

    def test_has_get_subgraph_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "get_subgraph")
        assert getattr(cls.get_subgraph, "__isabstractmethod__", False)

    def test_has_traverse_method(self):
        """R-PE1: Propagation requires traversal from trigger entity."""
        cls = self._get_interface()
        assert hasattr(cls, "traverse")
        assert getattr(cls.traverse, "__isabstractmethod__", False)

    # --- Search Methods ---

    def test_has_search_method(self):
        """R-KG8: Hybrid search (vector + keyword)."""
        cls = self._get_interface()
        assert hasattr(cls, "search")
        assert getattr(cls.search, "__isabstractmethod__", False)

    # --- Merge / Dedup ---

    def test_has_merge_entity_method(self):
        """R-KG7: Entity dedup via MERGE on insert."""
        cls = self._get_interface()
        assert hasattr(cls, "merge_entity")
        assert getattr(cls.merge_entity, "__isabstractmethod__", False)

    # --- Backup ---

    def test_has_backup_method(self):
        """R-PLAT-8: Automated backup support."""
        cls = self._get_interface()
        assert hasattr(cls, "backup")
        assert getattr(cls.backup, "__isabstractmethod__", False)

    # --- Health ---

    def test_has_health_check_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "health_check")
        assert getattr(cls.health_check, "__isabstractmethod__", False)

    # --- Method Signatures ---

    def test_create_entity_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.create_entity)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "entity_type" in params
        assert "properties" in params

    def test_create_edge_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.create_edge)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "source_id" in params
        assert "target_id" in params
        assert "relation_type" in params
        assert "properties" in params

    def test_traverse_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.traverse)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "start_entity_id" in params
        assert "max_depth" in params

    def test_search_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.search)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "query" in params

    def test_merge_entity_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.merge_entity)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "entity_type" in params
        assert "match_properties" in params
        assert "properties" in params

    # --- All methods are async ---

    def test_all_abstract_methods_are_async(self):
        """All graph operations must be async for non-blocking I/O."""
        cls = self._get_interface()
        abstract_methods = [
            name for name, method in inspect.getmembers(cls)
            if getattr(method, "__isabstractmethod__", False)
        ]
        for method_name in abstract_methods:
            method = getattr(cls, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"{method_name} must be async"
            )

    def test_interface_has_at_least_16_abstract_methods(self):
        """Full contract: entity CRUD(5) + edge CRUD(5) + traversal(3) + search(1) + merge(1) + backup(1) + health(1) = 17."""
        cls = self._get_interface()
        abstract_methods = [
            name for name, method in inspect.getmembers(cls)
            if getattr(method, "__isabstractmethod__", False)
        ]
        assert len(abstract_methods) >= 16, (
            f"Expected ≥16 abstract methods, found {len(abstract_methods)}: {abstract_methods}"
        )


class TestGraphStorageCannotBeInstantiated:
    """Ensure no concrete class sneaks through without implementing all methods."""

    def test_partial_implementation_fails(self):
        from mkg.domain.interfaces.graph_storage import GraphStorage

        class PartialStorage(GraphStorage):
            async def create_entity(self, entity_type, properties, entity_id=None):
                pass

        with pytest.raises(TypeError):
            PartialStorage()
