from __future__ import annotations

import asyncio
import json
import os
from decimal import Decimal, InvalidOperation
from typing import Any

from providers import (
    MobileMoneyProvider,
    PaymentProviderError,
    PaymentRequest,
    get_client,
)

APP_IDENTIFIER = "com.katale.mobile-money"
APP_VERSION = "1.0.0"
APP_BASE_URL = os.environ.get("MOBILE_MONEY_APP_URL", "http://127.0.0.1:8001").rstrip("/")

TRANSACTION_QUERY = """
subscription {
  event {
    ... on TransactionInitializeSession {
      merchantReference
      action { amount currency actionType }
      data
      customerIpAddress
      sourceObject { __typename ... on Checkout { id } ... on Order { id } }
    }
    ... on TransactionProcessSession {
      merchantReference
      action { amount currency actionType }
      data
      customerIpAddress
      sourceObject { __typename ... on Checkout { id } ... on Order { id } }
    }
  }
}
"""


def _json_response(status: int, payload: dict[str, Any]) -> list[bytes]:
    return [json.dumps(payload).encode("utf-8")]


def _provider_from_data(data: Any) -> MobileMoneyProvider:
    if isinstance(data, dict):
        value = data.get("provider") or os.environ.get("MOBILE_MONEY_PROVIDER", "mtn")
    else:
        value = os.environ.get("MOBILE_MONEY_PROVIDER", "mtn")
    try:
        return MobileMoneyProvider(str(value).lower())
    except ValueError as error:
        raise PaymentProviderError("provider must be either 'mtn' or 'airtel'.") from error


def _phone_from_data(data: Any) -> str:
    if isinstance(data, dict):
        for key in ("phone", "phoneNumber", "msisdn", "mobileNumber"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    raise PaymentProviderError(
        "Mobile-money payment data must include phone, phoneNumber, msisdn, or mobileNumber."
    )


def _payment_request(payload: dict[str, Any]) -> PaymentRequest:
    action = payload.get("action") or {}
    data = payload.get("data") or {}
    try:
        amount = Decimal(str(action["amount"]))
    except (KeyError, InvalidOperation) as error:
        raise PaymentProviderError("Saleor payment payload has an invalid amount.") from error
    currency = str(action.get("currency") or "UGX")
    reference = str(payload.get("merchantReference") or "")
    if not reference:
        raise PaymentProviderError("Saleor payment payload has no merchant reference.")
    return PaymentRequest(
        amount=amount,
        currency=currency,
        phone_number=_phone_from_data(data),
        reference=reference,
        description=str(data.get("description") or "Katale order payment"),
    )


def _result(status: str) -> str:
    status = status.upper()
    if status in {"SUCCESSFUL", "SUCCESS", "TS"}:
        return "CHARGE_SUCCESS"
    if status in {"FAILED", "FAILURE", "TF"}:
        return "CHARGE_FAILURE"
    return "CHARGE_ACTION_REQUIRED"


async def _handle_transaction(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    try:
        payment = _payment_request(payload)
        provider = _provider_from_data(payload.get("data"))
        client = get_client(provider)
        status = await asyncio.to_thread(client.request_to_pay, payment)
        return 200, {
            "result": _result(status.status),
            "pspReference": status.reference,
            "amount": str(payment.amount),
            "data": {
                "provider": provider.value,
                "reference": status.reference,
                "status": status.status,
            },
            "message": status.message,
        }
    except PaymentProviderError as error:
        return 200, {
            "result": "CHARGE_FAILURE",
            "pspReference": None,
            "message": str(error),
        }


async def application(scope, receive, send):
    if scope["type"] != "http":
        return

    method = scope["method"]
    path = scope["path"]
    if method == "GET" and path == "/healthz":
        status, payload = 200, {"status": "ok", "provider": "mtn-and-airtel-uganda"}
    elif method == "GET" and path in {"/manifest", "/api/manifest"}:
        status, payload = 200, {
            "id": APP_IDENTIFIER,
            "identifier": APP_IDENTIFIER,
            "version": APP_VERSION,
            "name": "Katale MTN and Airtel Money",
            "about": "Uganda mobile-money payments for MTN MoMo and Airtel Money.",
            "permissions": ["MANAGE_PAYMENTS"],
            "appUrl": f"{APP_BASE_URL}/configuration",
            "homepageUrl": APP_BASE_URL,
            "webhooks": [
                {
                    "identifier": "transaction-initialize-session",
                    "name": "Transaction initialize session",
                    "syncEvents": ["TRANSACTION_INITIALIZE_SESSION"],
                    "asyncEvents": [],
                    "query": TRANSACTION_QUERY,
                    "targetUrl": f"{APP_BASE_URL}/webhooks/transaction",
                },
                {
                    "identifier": "transaction-process-session",
                    "name": "Transaction process session",
                    "syncEvents": ["TRANSACTION_PROCESS_SESSION"],
                    "asyncEvents": [],
                    "query": TRANSACTION_QUERY,
                    "targetUrl": f"{APP_BASE_URL}/webhooks/transaction",
                },
            ],
        }
    elif method == "GET" and path == "/configuration":
        status, payload = 200, {
            "provider": os.environ.get("MOBILE_MONEY_PROVIDER", "mtn"),
            "environment": "sandbox",
            "country": "UG",
            "currency": "UGX",
            "message": "Configure provider credentials through environment variables.",
        }
    elif method == "POST" and path == "/webhooks/transaction":
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            status, response = 400, {"message": "Request body must be valid JSON."}
        else:
            status, response = await _handle_transaction(payload)
        headers = [(b"content-type", b"application/json")]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send(
            {
                "type": "http.response.body",
                "body": _json_response(status, response)[0],
                "more_body": False,
            }
        )
        return
    else:
        status, payload = 404, {"message": "Not found."}

    response_body = _json_response(status, payload)[0]
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": response_body, "more_body": False})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:application",
        host=os.environ.get("MOBILE_MONEY_HOST", "127.0.0.1"),
        port=int(os.environ.get("MOBILE_MONEY_PORT", "8001")),
        reload=False,
    )
