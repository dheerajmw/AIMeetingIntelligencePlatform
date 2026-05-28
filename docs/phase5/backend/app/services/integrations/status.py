from __future__ import annotations

from ...config import settings


def provider_configured(provider: str) -> bool:
    if provider == "jira":
        return bool(
            settings.jira_base_url
            and settings.jira_email
            and settings.jira_api_token
            and settings.jira_project_key
        )
    if provider == "linear":
        return bool(settings.linear_api_key and settings.linear_team_id)
    if provider == "trello":
        return bool(settings.trello_api_key and settings.trello_token and settings.trello_list_id)
    if provider == "slack":
        return bool(settings.slack_webhook_url)
    if provider == "email":
        # SMTP_TO can be dynamic (send to current user), so host+from is enough.
        return bool(settings.smtp_host and settings.smtp_from)
    return False


def integrations_status_payload() -> dict:
    providers = ["jira", "linear", "trello", "slack", "email"]
    return {
        "stub_mode": settings.integrations_stub_mode,
        "providers": {
            p: {
                "configured": provider_configured(p),
                "ready": settings.integrations_stub_mode or provider_configured(p),
            }
            for p in providers
        },
    }
