from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from sqlalchemy.orm import Session

from ...config import settings
from ...db.models import ExportStatus, IntegrationExport, Meeting, MeetingStatus
from .providers import (
    IntegrationError,
    export_action_items_to_jira,
    export_action_items_to_linear,
    export_action_items_to_trello,
    send_summary_email,
    send_summary_to_slack,
)

Provider = Literal["jira", "linear", "trello", "slack", "email"]
ExportKind = Literal["action_items", "summary"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _meeting_title(meeting: Meeting) -> str:
    return meeting.title or meeting.original_filename


def _action_items(insights: dict) -> list[dict[str, Any]]:
    return list(insights.get("action_items") or [])


def _summary(insights: dict) -> str:
    return (insights.get("executive_summary") or "No summary available.").strip()


def run_export(
    db: Session,
    meeting: Meeting,
    provider: Provider,
    export_kind: ExportKind,
    force: bool = False,
    *,
    email_to: Optional[str] = None,
) -> IntegrationExport:
    if meeting.status != MeetingStatus.READY or not meeting.insights_json:
        raise IntegrationError("Meeting is not ready for export.")

    idempotency_key = f"{meeting.id}:{provider}:{export_kind}"
    existing = (
        db.query(IntegrationExport)
        .filter(IntegrationExport.idempotency_key == idempotency_key)
        .one_or_none()
    )
    if existing and existing.status == ExportStatus.SUCCESS and not force:
        return existing

    if existing:
        record = existing
        record.status = ExportStatus.PENDING
        record.error_message = None
        record.external_ref = None
        record.details_json = None
        record.updated_at = _utcnow()
    else:
        record = IntegrationExport(
            meeting_id=meeting.id,
            provider=provider,
            export_kind=export_kind,
            idempotency_key=idempotency_key,
            status=ExportStatus.PENDING,
        )
        db.add(record)
    db.commit()
    db.refresh(record)

    title = _meeting_title(meeting)
    insights = meeting.insights_json
    actions = _action_items(insights)

    try:
        if export_kind == "action_items":
            if not actions:
                raise IntegrationError("No action items to export.")
            if provider == "jira":
                refs = export_action_items_to_jira(title, actions)
            elif provider == "linear":
                refs = export_action_items_to_linear(title, actions)
            elif provider == "trello":
                refs = export_action_items_to_trello(title, actions)
            else:
                raise IntegrationError(f"Provider '{provider}' does not support action item export.")
            record.external_ref = ",".join(refs[:5])
            record.details_json = {"created_count": len(refs), "refs": refs}
            if settings.integrations_stub_mode:
                record.details_json["mode"] = "stub"
        else:
            summary = _summary(insights)
            if provider == "slack":
                ref = send_summary_to_slack(title, summary, actions)
            elif provider == "email":
                ref = send_summary_email(title, summary, actions, to_email=email_to)
            else:
                raise IntegrationError(f"Provider '{provider}' does not support summary export.")
            record.external_ref = ref
            record.details_json = {"summary_chars": len(summary)}
            if settings.integrations_stub_mode:
                record.details_json["mode"] = "stub"

        record.status = ExportStatus.SUCCESS
        record.error_message = None
        record.updated_at = _utcnow()
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    except Exception as e:
        record.status = ExportStatus.FAILED
        record.error_message = str(e)
        record.updated_at = _utcnow()
        db.add(record)
        db.commit()
        db.refresh(record)
        raise


def list_exports(db: Session, meeting_id: int) -> list[IntegrationExport]:
    return (
        db.query(IntegrationExport)
        .filter(IntegrationExport.meeting_id == meeting_id)
        .order_by(IntegrationExport.created_at.desc())
        .all()
    )
