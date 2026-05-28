from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db.models import User, Workspace, WorkspaceMember, WorkspaceRole


def ensure_default_workspace(db: Session) -> Workspace:
    workspace = db.execute(select(Workspace).where(Workspace.slug == settings.default_workspace_slug)).scalar_one_or_none()
    if workspace:
        return workspace

    workspace = Workspace(
        slug=settings.default_workspace_slug,
        name="Default Workspace",
        data_region=settings.default_data_region,
        retention_days=settings.default_retention_days,
        max_meetings_per_month=settings.default_max_meetings_per_month,
        max_llm_tokens_per_month=settings.default_max_llm_tokens_per_month,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def ensure_dev_user(db: Session, *, email: str, display_name: str, workspace: Workspace, role: WorkspaceRole) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(email=email, display_name=display_name)
        db.add(user)
        db.commit()
        db.refresh(user)

    member = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
    ).scalar_one_or_none()
    if not member:
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role))
        db.commit()
    return user


def bootstrap(db: Session) -> None:
    workspace = ensure_default_workspace(db)
    ensure_dev_user(
        db,
        email="admin@example.com",
        display_name="Admin User",
        workspace=workspace,
        role=WorkspaceRole.OWNER,
    )
    ensure_dev_user(
        db,
        email="member@example.com",
        display_name="Member User",
        workspace=workspace,
        role=WorkspaceRole.MEMBER,
    )
