# mkg/tests/test_auth_tenant.py
"""Tests for AuthTenantService — JWT auth context and tenant isolation.

R-AUTH1 through R-AUTH5: Tenant scoping, permission checks,
data isolation, and auth context propagation.
"""

import pytest


class TestAuthTenantService:

    @pytest.fixture
    def service(self):
        from mkg.domain.services.auth_tenant import AuthTenantService
        return AuthTenantService()

    def test_create_tenant(self, service):
        tenant = service.create_tenant("tenant-1", "Acme Corp")
        assert tenant["id"] == "tenant-1"
        assert tenant["name"] == "Acme Corp"

    def test_create_auth_context(self, service):
        service.create_tenant("tenant-1", "Acme Corp")
        ctx = service.create_context(
            user_id="user-1",
            tenant_id="tenant-1",
            roles=["analyst"],
        )
        assert ctx.user_id == "user-1"
        assert ctx.tenant_id == "tenant-1"
        assert "analyst" in ctx.roles

    def test_check_permission_granted(self, service):
        service.create_tenant("tenant-1", "Acme Corp")
        ctx = service.create_context("user-1", "tenant-1", roles=["admin"])
        assert service.has_permission(ctx, "write") is True

    def test_check_permission_denied(self, service):
        service.create_tenant("tenant-1", "Acme Corp")
        ctx = service.create_context("user-1", "tenant-1", roles=["viewer"])
        assert service.has_permission(ctx, "write") is False

    def test_viewer_can_read(self, service):
        service.create_tenant("tenant-1", "Acme Corp")
        ctx = service.create_context("user-1", "tenant-1", roles=["viewer"])
        assert service.has_permission(ctx, "read") is True

    def test_tenant_isolation(self, service):
        service.create_tenant("tenant-1", "Acme")
        service.create_tenant("tenant-2", "Beta")
        ctx1 = service.create_context("user-1", "tenant-1", roles=["admin"])
        ctx2 = service.create_context("user-2", "tenant-2", roles=["admin"])
        assert not service.can_access_tenant(ctx1, "tenant-2")
        assert service.can_access_tenant(ctx1, "tenant-1")

    def test_unknown_tenant_raises(self, service):
        with pytest.raises(ValueError, match="Unknown tenant"):
            service.create_context("user-1", "nonexistent", roles=["admin"])

    def test_scope_filter(self, service):
        service.create_tenant("tenant-1", "Acme")
        ctx = service.create_context("user-1", "tenant-1", roles=["analyst"])
        scope = service.get_scope_filter(ctx)
        assert scope["tenant_id"] == "tenant-1"
