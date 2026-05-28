from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

import httpx

from ..config import settings


class OidcError(Exception):
    pass


def oidc_configured() -> bool:
    return bool(settings.oidc_issuer and settings.oidc_client_id and settings.oidc_client_secret)


def authorization_url(state: str, redirect_uri: Optional[str] = None) -> str:
    if not oidc_configured():
        raise OidcError("OIDC is not configured")
    redirect = redirect_uri or settings.oidc_redirect_uri
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect,
        "state": state,
    }
    base = settings.oidc_issuer.rstrip("/")
    return f"{base}/authorize?{urlencode(params)}"


def exchange_code_for_profile(code: str, redirect_uri: Optional[str] = None) -> dict:
    if not oidc_configured():
        raise OidcError("OIDC is not configured")

    redirect = redirect_uri or settings.oidc_redirect_uri
    base = settings.oidc_issuer.rstrip("/")
    token_url = f"{base}/token"
    userinfo_url = f"{base}/userinfo"

    with httpx.Client(timeout=30.0) as client:
        token_resp = client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code >= 400:
            raise OidcError(f"Token exchange failed: {token_resp.text}")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise OidcError("No access_token in OIDC response")

        profile_resp = client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_resp.status_code >= 400:
            raise OidcError(f"Userinfo failed: {profile_resp.text}")
        return profile_resp.json()
