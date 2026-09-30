"""Power BI Service Automated Refresh Extension (Mode B).

Integrates with Power BI REST APIs via Azure Active Directory Service Principal.
Complies strictly with security and technical honesty standards:
- Reads credentials exclusively from environment variables or .env.
- If credentials are absent, provides explicit instructions without fake success messages.
"""

from dataclasses import dataclass
import logging
import os
from typing import Any
import requests

logger = logging.getLogger(__name__)


@dataclass
class RefreshStatus:
    success: bool
    status_code: int
    message: str
    details: dict[str, Any]


class PowerBIServiceRefresher:
    """Manages trigger requests to Power BI Service REST API."""

    def __init__(self):
        self.tenant_id = os.environ.get("POWERBI_TENANT_ID")
        self.client_id = os.environ.get("POWERBI_CLIENT_ID")
        self.client_secret = os.environ.get("POWERBI_CLIENT_SECRET")
        self.workspace_id = os.environ.get("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.environ.get("POWERBI_DATASET_ID")

    def is_configured(self) -> bool:
        """Check if all necessary Azure AD & Power BI Service credentials exist."""
        return bool(
            self.tenant_id
            and self.client_id
            and self.client_secret
            and self.workspace_id
            and self.dataset_id
        )

    def trigger_dataset_refresh(self) -> RefreshStatus:
        """Issue an asynchronous refresh trigger to Power BI Service."""
        if not self.is_configured():
            msg = (
                "Power BI Service credentials not configured in environment. "
                "For local analysis, use Mode A (Power BI Desktop connected to data/exports/network_metrics.csv). "
                "To enable cloud refresh, configure POWERBI_TENANT_ID, POWERBI_CLIENT_ID, etc. in .env."
            )
            return RefreshStatus(
                success=False,
                status_code=401,
                message=msg,
                details={"configured": False}
            )

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        body = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }

        try:
            token_resp = requests.post(token_url, data=body, timeout=10)
            if token_resp.status_code != 200:
                return RefreshStatus(
                    success=False,
                    status_code=token_resp.status_code,
                    message=f"Azure AD OAuth authentication failed: {token_resp.text}",
                    details={"error": token_resp.text}
                )

            access_token = token_resp.json().get("access_token")
            refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            resp = requests.post(refresh_url, headers=headers, json={"notifyOption": "NoNotification"}, timeout=10)
            if resp.status_code in (200, 202):
                return RefreshStatus(
                    success=True,
                    status_code=resp.status_code,
                    message="Power BI Service dataset refresh successfully triggered.",
                    details={"status": "ACCEPTED"}
                )
            else:
                return RefreshStatus(
                    success=False,
                    status_code=resp.status_code,
                    message=f"Power BI API returned error: {resp.text}",
                    details={"response": resp.text}
                )
        except Exception as exc:
            return RefreshStatus(
                success=False,
                status_code=500,
                message=f"Network error contacting Power BI API: {exc}",
                details={"exception": str(exc)}
            )
