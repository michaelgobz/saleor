from collections.abc import Mapping
from typing import Any

from django.conf import settings

from ..core.http_client import HTTPClient


class AccountingGraphQLAdapter:
    """Vendor-neutral GraphQL-over-HTTPS accounting adapter."""

    def __init__(self, endpoint: str | None = None, token: str | None = None):
        self.endpoint = endpoint or settings.ACCOUNTING_GRAPHQL_ENDPOINT
        self.token = token or settings.ACCOUNTING_GRAPHQL_TOKEN

    def execute(
        self, query: str, variables: Mapping[str, Any], idempotency_key: str
    ) -> dict[str, Any]:
        if not self.endpoint:
            raise RuntimeError("ACCOUNTING_GRAPHQL_ENDPOINT is not configured.")
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with HTTPClient.send_request(
            "POST",
            self.endpoint,
            headers=headers,
            json={"query": query, "variables": dict(variables)},
        ) as response:
            response.raise_for_status()
            payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(f"Accounting GraphQL request failed: {payload['errors']}")
        return payload.get("data", {})
