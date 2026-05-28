from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.dependencies import AuthContext, get_auth_context
from ..auth.jwt_tokens import create_access_token
from ..auth.oidc import OidcError, authorization_url, exchange_code_for_profile, oidc_configured
from ..config import settings
from ..db.models import User, Workspace, WorkspaceMember, WorkspaceRole
from ..db.session import get_db
from ..enterprise.audit import write_audit
from ..enterprise.seed import ensure_default_workspace, ensure_dev_user

router = APIRouter(prefix="/auth", tags=["auth"])


class DevLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    workspace_slug: str = "default"


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    workspace_id: int
    workspace_slug: str
    role: str
    user_email: str
    user_display_name: str


class WorkspaceInfo(BaseModel):
    id: int
    slug: str
    name: str
    data_region: str
    role: str


class MeResponse(BaseModel):
    user_id: int
    email: str
    display_name: str
    workspace: WorkspaceInfo
    workspaces: list[WorkspaceInfo]


class OidcStartResponse(BaseModel):
    authorization_url: str
    state: str


class OidcCallbackRequest(BaseModel):
    code: str
    state: str
    workspace_slug: str = "default"


@router.post("/dev-login", response_model=AuthTokenResponse)
def dev_login(body: DevLoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    if not settings.dev_auth_enabled:
        raise HTTPException(status_code=403, detail="Dev login is disabled")

    workspace = db.execute(select(Workspace).where(Workspace.slug == body.workspace_slug)).scalar_one_or_none()
    if not workspace:
        workspace = ensure_default_workspace(db)

    user = ensure_dev_user(
        db,
        email=body.email,
        display_name=body.email.split("@")[0].title(),
        workspace=workspace,
        role=WorkspaceRole.MEMBER,
    )
    member = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
    ).scalar_one()

    token = create_access_token(
        user_id=user.id,
        workspace_id=workspace.id,
        role=member.role.value,
        email=user.email,
    )
    write_audit(
        db,
        workspace_id=workspace.id,
        user_id=user.id,
        action="auth.dev_login",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
    )
    return AuthTokenResponse(
        access_token=token,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
        role=member.role.value,
        user_email=user.email,
        user_display_name=user.display_name,
    )


@router.get("/me", response_model=MeResponse)
def me(auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> MeResponse:
    memberships = db.execute(
        select(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == auth.user.id)
    ).all()

    workspaces: list[WorkspaceInfo] = []
    for member, workspace in memberships:
        workspaces.append(
            WorkspaceInfo(
                id=workspace.id,
                slug=workspace.slug,
                name=workspace.name,
                data_region=workspace.data_region,
                role=member.role.value,
            )
        )

    return MeResponse(
        user_id=auth.user.id,
        email=auth.user.email,
        display_name=auth.user.display_name,
        workspace=WorkspaceInfo(
            id=auth.workspace.id,
            slug=auth.workspace.slug,
            name=auth.workspace.name,
            data_region=auth.workspace.data_region,
            role=auth.role.value,
        ),
        workspaces=workspaces,
    )


@router.get("/oidc/start", response_model=OidcStartResponse)
def oidc_start(redirect_uri: Optional[str] = None) -> OidcStartResponse:
    if not oidc_configured():
        raise HTTPException(status_code=501, detail="OIDC not configured (set OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET)")
    state = secrets.token_urlsafe(16)
    return OidcStartResponse(authorization_url=authorization_url(state, redirect_uri), state=state)


@router.post("/oidc/callback", response_model=AuthTokenResponse)
def oidc_callback(body: OidcCallbackRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    try:
        profile = exchange_code_for_profile(body.code)
    except OidcError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    email = profile.get("email")
    sub = profile.get("sub")
    name = profile.get("name") or profile.get("preferred_username") or email
    if not email or not sub:
        raise HTTPException(status_code=400, detail="OIDC profile missing email or sub")

    workspace = db.execute(select(Workspace).where(Workspace.slug == body.workspace_slug)).scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    user = db.execute(select(User).where(User.external_subject == sub)).scalar_one_or_none()
    if not user:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(email=email, display_name=name or email, external_subject=sub)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.external_subject = sub
        user.display_name = name or user.display_name
        db.add(user)
        db.commit()

    member = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not member:
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.MEMBER))
        db.commit()
        member = db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.user_id == user.id,
            )
        ).scalar_one()

    token = create_access_token(
        user_id=user.id,
        workspace_id=workspace.id,
        role=member.role.value,
        email=user.email,
    )
    write_audit(
        db,
        workspace_id=workspace.id,
        user_id=user.id,
        action="auth.oidc_login",
        resource_type="user",
        resource_id=str(user.id),
    )
    return AuthTokenResponse(
        access_token=token,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
        role=member.role.value,
        user_email=user.email,
        user_display_name=user.display_name,
    )
