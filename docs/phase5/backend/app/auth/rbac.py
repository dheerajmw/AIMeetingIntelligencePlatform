from __future__ import annotations

from ..db.models import WorkspaceRole

ROLE_RANK = {
    WorkspaceRole.VIEWER: 0,
    WorkspaceRole.MEMBER: 1,
    WorkspaceRole.ADMIN: 2,
    WorkspaceRole.OWNER: 3,
}


def role_at_least(role: WorkspaceRole, minimum: WorkspaceRole) -> bool:
    return ROLE_RANK[role] >= ROLE_RANK[minimum]


def can_read(role: WorkspaceRole) -> bool:
    return role_at_least(role, WorkspaceRole.VIEWER)


def can_write(role: WorkspaceRole) -> bool:
    return role_at_least(role, WorkspaceRole.MEMBER)


def can_admin(role: WorkspaceRole) -> bool:
    return role_at_least(role, WorkspaceRole.ADMIN)


def can_delete_workspace(role: WorkspaceRole) -> bool:
    return role == WorkspaceRole.OWNER
