from __future__ import annotations

import base64
from typing import Any

import httpx

from ...config import settings
from .stub import stub_action_item_refs, stub_summary_ref


class IntegrationError(Exception):
    pass


def _require(*values: str | None, names: list[str]) -> None:
    missing = [name for name, val in zip(names, values) if not val]
    if missing:
        raise IntegrationError(f"Missing configuration: {', '.join(missing)}")


def export_action_items_to_jira(meeting_title: str, action_items: list[dict[str, Any]]) -> list[str]:
    if settings.integrations_stub_mode:
        return stub_action_item_refs("jira", action_items)
    _require(
        settings.jira_base_url,
        settings.jira_email,
        settings.jira_api_token,
        settings.jira_project_key,
        names=["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"],
    )

    auth = base64.b64encode(f"{settings.jira_email}:{settings.jira_api_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    base = settings.jira_base_url.rstrip("/")
    created_keys: list[str] = []

    with httpx.Client(timeout=30.0) as client:
        for item in action_items:
            title = item.get("title") or item.get("action") or "Action item"
            desc = item.get("description") or ""
            owner = item.get("owner") or "Not identified"
            due = item.get("due_date") or item.get("deadline") or "Not identified"
            evidence = item.get("evidence_quote") or "Not identified"

            payload = {
                "fields": {
                    "project": {"key": settings.jira_project_key},
                    "summary": f"[Meeting] {title}",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": (
                                            f"Meeting: {meeting_title}\n"
                                            f"Owner: {owner}\n"
                                            f"Due date: {due}\n"
                                            f"Evidence: {evidence}\n\n"
                                            f"{desc}"
                                        ),
                                    }
                                ],
                            }
                        ],
                    },
                    "issuetype": {"name": "Task"},
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", headers=headers, json=payload)
            if r.status_code >= 400:
                raise IntegrationError(f"Jira export failed ({r.status_code}): {r.text}")
            key = r.json().get("key")
            if key:
                created_keys.append(key)
    return created_keys


def export_action_items_to_linear(meeting_title: str, action_items: list[dict[str, Any]]) -> list[str]:
    if settings.integrations_stub_mode:
        return stub_action_item_refs("linear", action_items)
    _require(settings.linear_api_key, settings.linear_team_id, names=["LINEAR_API_KEY", "LINEAR_TEAM_ID"])

    token = settings.linear_api_key.strip()
    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    created_ids: list[str] = []

    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier }
      }
    }
    """

    with httpx.Client(timeout=30.0) as client:
        for item in action_items:
            title = item.get("title") or item.get("action") or "Action item"
            desc = (
                f"Meeting: {meeting_title}\n"
                f"Owner: {item.get('owner') or 'Not identified'}\n"
                f"Due date: {item.get('due_date') or item.get('deadline') or 'Not identified'}\n"
                f"Evidence: {item.get('evidence_quote') or 'Not identified'}\n\n"
                f"{item.get('description') or ''}"
            )
            variables = {
                "input": {
                    "teamId": settings.linear_team_id,
                    "title": f"[Meeting] {title}",
                    "description": desc,
                }
            }
            r = client.post(
                "https://api.linear.app/graphql",
                headers=headers,
                json={"query": mutation, "variables": variables},
            )
            if r.status_code >= 400:
                raise IntegrationError(f"Linear export failed ({r.status_code}): {r.text}")
            data = r.json()
            if data.get("errors"):
                raise IntegrationError(f"Linear export failed: {data['errors']}")
            issue = (((data.get("data") or {}).get("issueCreate") or {}).get("issue") or {})
            ref = issue.get("identifier") or issue.get("id")
            if ref:
                created_ids.append(str(ref))
    return created_ids


def export_action_items_to_trello(meeting_title: str, action_items: list[dict[str, Any]]) -> list[str]:
    if settings.integrations_stub_mode:
        return stub_action_item_refs("trello", action_items)
    _require(
        settings.trello_api_key,
        settings.trello_token,
        settings.trello_list_id,
        names=["TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_LIST_ID"],
    )

    created_ids: list[str] = []
    with httpx.Client(timeout=30.0) as client:
        for item in action_items:
            title = item.get("title") or item.get("action") or "Action item"
            desc = (
                f"Meeting: {meeting_title}\n"
                f"Owner: {item.get('owner') or 'Not identified'}\n"
                f"Due date: {item.get('due_date') or item.get('deadline') or 'Not identified'}\n"
                f"Evidence: {item.get('evidence_quote') or 'Not identified'}\n\n"
                f"{item.get('description') or ''}"
            )
            params = {
                "key": settings.trello_api_key,
                "token": settings.trello_token,
                "idList": settings.trello_list_id,
                "name": f"[Meeting] {title}",
                "desc": desc,
            }
            r = client.post("https://api.trello.com/1/cards", params=params)
            if r.status_code >= 400:
                raise IntegrationError(f"Trello export failed ({r.status_code}): {r.text}")
            card_id = r.json().get("id")
            if card_id:
                created_ids.append(str(card_id))
    return created_ids


def send_summary_to_slack(meeting_title: str, summary: str, action_items: list[dict[str, Any]]) -> str:
    if settings.integrations_stub_mode:
        return stub_summary_ref("slack")
    _require(settings.slack_webhook_url, names=["SLACK_WEBHOOK_URL"])

    actions_txt = "\n".join(
        f"• {(a.get('title') or a.get('action') or 'Action')} — owner: {a.get('owner') or 'Not identified'}"
        for a in action_items[:20]
    ) or "No action items."

    payload = {
        "text": f"Meeting summary: {meeting_title}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"Summary — {meeting_title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": summary[:2800]}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action items*\n{actions_txt}"}},
        ],
    }

    with httpx.Client(timeout=20.0) as client:
        r = client.post(settings.slack_webhook_url, json=payload)
        if r.status_code >= 400:
            raise IntegrationError(f"Slack export failed ({r.status_code}): {r.text}")
    return "slack_message_sent"


def send_summary_email(
    meeting_title: str,
    summary: str,
    action_items: list[dict[str, Any]],
    *,
    to_email: str | None = None,
) -> str:
    if settings.integrations_stub_mode:
        return stub_summary_ref("email")
    import smtplib
    from email.message import EmailMessage

    # SMTP_TO can be omitted if we send to the current user (passed in at runtime).
    _require(settings.smtp_host, settings.smtp_from, names=["SMTP_HOST", "SMTP_FROM"])
    resolved_to = (to_email or settings.smtp_to or "").strip()
    if not resolved_to:
        raise IntegrationError("Missing configuration: SMTP_TO (or provide email_to).")

    actions_txt = "\n".join(
        f"- {(a.get('title') or a.get('action') or 'Action')} (owner: {a.get('owner') or 'Not identified'})"
        for a in action_items
    ) or "No action items."

    msg = EmailMessage()
    msg["Subject"] = f"Meeting summary — {meeting_title}"
    msg["From"] = settings.smtp_from
    msg["To"] = resolved_to
    msg.set_content(f"{summary}\n\nAction items:\n{actions_txt}")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_user and settings.smtp_password:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return f"email_sent:{resolved_to}"
