from __future__ import annotations

import html
import json
import os
from typing import Any
from urllib import error, request
from urllib.parse import parse_qs

APP_IDENTIFIER = "com.katale.operations-pulse"
APP_VERSION = "1.0.0"
APP_BASE_URL = os.environ.get(
    "OPERATIONS_PULSE_APP_URL", "http://127.0.0.1:8002"
).rstrip("/")

METRICS_QUERY = """
query OperationsPulseMetrics {
  orders(first: 1) { totalCount }
  products(first: 1) { totalCount }
  customers(first: 1) { totalCount }
}
"""


def _json_response(status: int, payload: dict[str, Any]) -> tuple[int, bytes]:
    return status, json.dumps(payload).encode("utf-8")


def _manifest() -> dict[str, Any]:
    return {
        "id": APP_IDENTIFIER,
        "version": APP_VERSION,
        "name": "Katale Operations Pulse",
        "about": "Live commerce and operations metrics on the Saleor Dashboard home page.",
        "homepageUrl": APP_BASE_URL,
        "appUrl": APP_BASE_URL,
        "permissions": ["MANAGE_ORDERS", "MANAGE_PRODUCTS", "MANAGE_USERS"],
        "extensions": [
            {
                "label": "Operations Pulse",
                "mount": "HOMEPAGE_WIDGETS",
                "target": "WIDGET",
                "permissions": ["MANAGE_ORDERS", "MANAGE_PRODUCTS", "MANAGE_USERS"],
                "url": "/widget",
                "options": {
                    "homeWidgetTarget": {
                        "method": "POST",
                        "fullscreen": False,
                    }
                },
            }
        ],
    }


async def _read_body_async(receive: Any) -> bytes:
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body"):
            return body


def _form_value(form: dict[str, list[str]], key: str) -> str:
    values = form.get(key, [])
    return values[0] if values else ""


def _fetch_metrics(api_url: str, access_token: str) -> dict[str, int]:
    payload = json.dumps({"query": METRICS_QUERY}).encode("utf-8")
    api_request = request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"JWT {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=10) as response:
            result = json.loads(response.read())
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load Saleor metrics: {exc}") from exc

    if result.get("errors"):
        raise RuntimeError(str(result["errors"][0].get("message", "GraphQL error")))

    data = result.get("data") or {}
    return {
        "orders": int((data.get("orders") or {}).get("totalCount") or 0),
        "products": int((data.get("products") or {}).get("totalCount") or 0),
        "customers": int((data.get("customers") or {}).get("totalCount") or 0),
    }


def _widget_page(metrics: dict[str, int] | None = None, error_message: str | None = None) -> bytes:
    cards = ""
    if metrics is not None:
        cards = "".join(
            f'<div class="card"><strong>{value:,}</strong><span>{label}</span></div>'
            for label, value in (
                ("Orders", metrics["orders"]),
                ("Products", metrics["products"]),
                ("Customers", metrics["customers"]),
            )
        )
    message = (
        f'<p class="error">{html.escape(error_message)}</p>'
        if error_message
        else ""
    )
    document = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Operations Pulse</title>
    <style>
      :root {{ color-scheme: light; font-family: Inter, system-ui, sans-serif; }}
      body {{ margin: 0; padding: 18px; color: #17212b; background: #fff; }}
      h2 {{ margin: 0 0 4px; font-size: 18px; }}
      p {{ margin: 0 0 14px; color: #5b6875; font-size: 13px; }}
      .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
      .card {{ border: 1px solid #dfe5eb; border-radius: 8px; padding: 12px; }}
      strong {{ display: block; font-size: 22px; }}
      span {{ color: #5b6875; font-size: 12px; }}
      .error {{ color: #b42318; }}
    </style>
  </head>
  <body>
    <h2>Operations Pulse</h2>
    <p>Current totals from Saleor</p>
    {message}
    <div class="grid">{cards}</div>
  </body>
</html>"""
    return document.encode("utf-8")


async def application(scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope["type"] != "http":
        return

    method = scope["method"]
    path = scope["path"]
    if method == "GET" and path in {"/healthz", "/"}:
        status, body = _json_response(200, {"status": "ok", "app": APP_IDENTIFIER})
        content_type = b"application/json"
    elif method == "GET" and path in {"/manifest", "/api/manifest"}:
        status, body = _json_response(200, _manifest())
        content_type = b"application/json"
    elif method == "POST" and path == "/widget":
        raw_body = await _read_body_async(receive)
        form = parse_qs(raw_body.decode("utf-8"))
        api_url = _form_value(form, "saleorApiUrl")
        access_token = _form_value(form, "accessToken")
        try:
            if not api_url or not access_token:
                raise RuntimeError("Dashboard did not provide Saleor connection details.")
            body = _widget_page(_fetch_metrics(api_url, access_token))
        except RuntimeError as exc:
            body = _widget_page(error_message=str(exc))
        status, content_type = 200, b"text/html; charset=utf-8"
    else:
        status, body = _json_response(404, {"message": "Not found."})
        content_type = b"application/json"

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", content_type),
                (b"content-security-policy", b"frame-ancestors 'self' http://127.0.0.1:9000 http://localhost:9000"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:application",
        host=os.environ.get("OPERATIONS_PULSE_HOST", "127.0.0.1"),
        port=int(os.environ.get("OPERATIONS_PULSE_PORT", "8002")),
    )
