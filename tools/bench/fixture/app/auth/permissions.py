"""Roles and the actions they may perform."""

ROLES: dict[str, set[str]] = {
    "viewer": {"orders:read"},
    "clerk": {"orders:read", "orders:write"},
    "admin": {"orders:read", "orders:write", "refunds:issue", "users:manage"},
}


def can(role: str, action: str) -> bool:
    """Whether the role may perform the action; an unknown role may do nothing."""
    return action in ROLES.get(role, set())
