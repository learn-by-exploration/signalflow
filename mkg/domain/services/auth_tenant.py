# mkg/domain/services/auth_tenant.py
"""AuthTenantService — JWT auth context and tenant isolation for MKG.

R-AUTH1 through R-AUTH5: Manages tenant creation, auth contexts,
permission checks, and data isolation scoping.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# Role → permitted actions mapping
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"read", "write", "delete", "manage"},
    "analyst": {"read", "write"},
    "viewer": {"read"},
}


@dataclass(frozen=True)
class AuthContext:
    """Immutable auth context for request scoping.

    Attributes:
        user_id: Authenticated user identifier.
        tenant_id: Tenant the user belongs to.
        roles: List of roles (admin, analyst, viewer).
    """
    user_id: str
    tenant_id: str
    roles: list[str] = field(default_factory=list)


class AuthTenantService:
    """Manages tenant isolation and permission checks.

    Provides auth context creation, permission checking, and scope filters
    for tenant-isolated queries.
    """

    def __init__(self) -> None:
        self._tenants: dict[str, dict[str, Any]] = {}

    def create_tenant(self, tenant_id: str, name: str) -> dict[str, Any]:
        """Create a new tenant.

        Args:
            tenant_id: Unique tenant identifier.
            name: Display name.

        Returns:
            Tenant dict.
        """
        tenant = {"id": tenant_id, "name": name}
        self._tenants[tenant_id] = tenant
        return tenant

    def create_context(
        self,
        user_id: str,
        tenant_id: str,
        roles: Optional[list[str]] = None,
    ) -> AuthContext:
        """Create an auth context for a user.

        Args:
            user_id: User identifier.
            tenant_id: Tenant identifier (must exist).
            roles: User roles.

        Returns:
            AuthContext instance.

        Raises:
            ValueError: If tenant doesn't exist.
        """
        if tenant_id not in self._tenants:
            raise ValueError(f"Unknown tenant: {tenant_id}")
        return AuthContext(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles or [],
        )

    def has_permission(self, ctx: AuthContext, action: str) -> bool:
        """Check if the auth context permits an action.

        Args:
            ctx: Auth context.
            action: Action to check (read, write, delete, manage).

        Returns:
            True if permitted.
        """
        for role in ctx.roles:
            perms = _ROLE_PERMISSIONS.get(role, set())
            if action in perms:
                return True
        return False

    def can_access_tenant(self, ctx: AuthContext, tenant_id: str) -> bool:
        """Check if the context can access a given tenant's data.

        Args:
            ctx: Auth context.
            tenant_id: Target tenant.

        Returns:
            True if the context's tenant matches the target.
        """
        return ctx.tenant_id == tenant_id

    def get_scope_filter(self, ctx: AuthContext) -> dict[str, Any]:
        """Get a query filter dict for tenant isolation.

        Args:
            ctx: Auth context.

        Returns:
            Dict with tenant_id for filtering queries.
        """
        return {"tenant_id": ctx.tenant_id}
