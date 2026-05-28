from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db.models import User, Workspace, WorkspaceMember, WorkspaceRole
from ..db.session import get_db
from . import rbac
from .jwt_tokens import decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    workspace: Workspace
    role: WorkspaceRole


def _parse_token(credentials: Optional[HTTPAuthorizationCredentials]) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    try:
        return decode_access_token(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


def get_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    if settings.auth_disabled:
        from ..enterprise.seed import ensure_default_workspace

        workspace = ensure_default_workspace(db)
        user = db.execute(select(User).limit(1)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=500, detail="No users seeded; restart server")
        member = db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.user_id == user.id,
            )
        ).scalar_one_or_none()
        role = member.role if member else WorkspaceRole.OWNER
        return AuthContext(user=user, workspace=workspace, role=role)

    payload = _parse_token(credentials)
    user_id = int(payload["sub"])
    workspace_id = int(payload["wid"])
    role_name = payload.get("role", WorkspaceRole.MEMBER.value)

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=401, detail="Workspace not found")

    member = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    try:
        role = WorkspaceRole(role_name)
    except ValueError:
        role = member.role

    request.state.auth = AuthContext(user=user, workspace=workspace, role=role)
    return request.state.auth


def require_read(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not rbac.can_read(auth.role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return auth


def require_write(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not rbac.can_write(auth.role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return auth


def require_admin(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not rbac.can_admin(auth.role):
        raise HTTPException(status_code=403, detail="Admin role required")
    return auth
