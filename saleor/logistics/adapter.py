from collections.abc import Mapping
from typing import Any

from django.conf import settings

from ..core.http_client import HTTPClient


class LogisticsGraphQLAdapter:
    """Vendor-neutral GraphQL-over-HTTPS logistics adapter."""

    def __init__(self, endpoint: str | None = None, token: str | None = None):
        self.endpoint = endpoint or settings.LOGISTICS_GRAPHQL_ENDPOINT
        self.token = token or settings.LOGISTICS_GRAPHQL_TOKEN

    def execute(
        self, query: str, variables: Mapping[str, Any], idempotency_key: str
    ) -> dict[str, Any]:
        if not self.endpoint:
            raise RuntimeError("LOGISTICS_GRAPHQL_ENDPOINT is not configured.")

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
            raise RuntimeError(f"Logistics GraphQL request failed: {payload['errors']}")
        return payload.get("data", {})
