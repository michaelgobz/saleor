from __future__ import annotations

import base64
import os
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

import requests


class MobileMoneyProvider(StrEnum):
    AIRTEL = "airtel"
    MTN = "mtn"


class PaymentProviderError(RuntimeError):
    """Raised when a mobile-money provider rejects or cannot process a request."""


@dataclass(frozen=True)
class PaymentRequest:
    amount: Decimal
    currency: str
    phone_number: str
    reference: str
    description: str


@dataclass(frozen=True)
class PaymentStatus:
    reference: str
    status: str
    message: str
    raw_response: dict[str, Any]


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    timeout: float = 15,
) -> dict[str, Any]:
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            json=json_data,
            data=data,
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise PaymentProviderError(f"Mobile-money provider request failed: {error}") from error

    if not response.ok:
        raise PaymentProviderError(
            f"Mobile-money provider returned HTTP {response.status_code}: {response.text[:512]}"
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise PaymentProviderError("Mobile-money provider returned invalid JSON.") from error

    if not isinstance(payload, dict):
        raise PaymentProviderError("Mobile-money provider returned an invalid response shape.")

    return payload


def _normalise_uganda_phone(phone_number: str) -> str:
    digits = "".join(character for character in phone_number if character.isdigit())
    if digits.startswith("0"):
        digits = f"256{digits[1:]}"
    elif digits.startswith("7"):
        digits = f"256{digits}"
    if len(digits) != 12 or not digits.startswith("2567"):
        raise PaymentProviderError("Use a valid Uganda mobile number, for example 2567XXXXXXXX.")
    return digits


class MtnUgandaClient:
    def __init__(self) -> None:
        self.base_url = os.environ.get(
            "MTN_MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com"
        ).rstrip("/")
        self.subscription_key = os.environ.get("MTN_MOMO_SUBSCRIPTION_KEY", "")
        self.api_user = os.environ.get("MTN_MOMO_API_USER", "")
        self.api_key = os.environ.get("MTN_MOMO_API_KEY", "")
        self.target_environment = os.environ.get("MTN_MOMO_TARGET_ENVIRONMENT", "sandbox")

    def _headers(self) -> dict[str, str]:
        if not all((self.subscription_key, self.api_user, self.api_key)):
            raise PaymentProviderError(
                "MTN MoMo requires MTN_MOMO_SUBSCRIPTION_KEY, MTN_MOMO_API_USER, "
                "and MTN_MOMO_API_KEY."
            )
        credentials = base64.b64encode(
            f"{self.api_user}:{self.api_key}".encode("utf-8")
        ).decode("ascii")
        return {
            "Authorization": f"Basic {credentials}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

    def _access_token(self) -> str:
        payload = _request_json(
            "POST",
            f"{self.base_url}/collection/token/",
            headers={
                **self._headers(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise PaymentProviderError("MTN MoMo did not return an access token.")
        return token

    def request_to_pay(self, payment: PaymentRequest) -> PaymentStatus:
        reference = payment.reference or str(uuid.uuid4())
        _request_json(
            "POST",
            f"{self.base_url}/collection/v1_0/requesttopay",
            headers={
                **self._headers(),
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
                "X-Reference-Id": reference,
                "X-Target-Environment": self.target_environment,
            },
            json_data={
                "amount": str(payment.amount),
                "currency": payment.currency,
                "externalId": reference,
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": _normalise_uganda_phone(payment.phone_number),
                },
                "payerMessage": payment.description[:160],
                "payeeNote": payment.description[:160],
            },
        )
        return self.status(reference)

    def status(self, reference: str) -> PaymentStatus:
        payload = _request_json(
            "GET",
            f"{self.base_url}/collection/v1_0/requesttopay/{reference}",
            headers={
                **self._headers(),
                "Authorization": f"Bearer {self._access_token()}",
                "X-Target-Environment": self.target_environment,
            },
        )
        status = str(payload.get("status", "PENDING")).upper()
        return PaymentStatus(
            reference=reference,
            status=status,
            message=str(payload.get("reason", status)),
            raw_response=payload,
        )


class AirtelUgandaClient:
    def __init__(self) -> None:
        self.base_url = os.environ.get(
            "AIRTEL_MONEY_BASE_URL", "https://openapiuat.airtel.africa"
        ).rstrip("/")
        self.client_id = os.environ.get("AIRTEL_MONEY_CLIENT_ID", "")
        self.client_secret = os.environ.get("AIRTEL_MONEY_CLIENT_SECRET", "")
        self.country = os.environ.get("AIRTEL_MONEY_COUNTRY", "UG")
        self.currency = os.environ.get("AIRTEL_MONEY_CURRENCY", "UGX")

    def _access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            raise PaymentProviderError(
                "Airtel Money requires AIRTEL_MONEY_CLIENT_ID and "
                "AIRTEL_MONEY_CLIENT_SECRET."
            )
        payload = _request_json(
            "POST",
            f"{self.base_url}/auth/oauth2/token",
            headers={"Content-Type": "application/json", "Accept": "*/*"},
            json_data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise PaymentProviderError("Airtel Money did not return an access token.")
        return token

    def request_to_pay(self, payment: PaymentRequest) -> PaymentStatus:
        reference = payment.reference or str(uuid.uuid4())
        payload = _request_json(
            "POST",
            f"{self.base_url}/merchant/v1/payments/",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
                "Accept": "*/*",
                "X-Country": self.country,
                "X-Currency": self.currency,
            },
            json_data={
                "reference": reference,
                "subscriber": {
                    "country": self.country,
                    "currency": self.currency,
                    "msisdn": _normalise_uganda_phone(payment.phone_number),
                },
                "transaction": {
                    "amount": str(payment.amount),
                    "country": self.country,
                    "currency": self.currency,
                    "id": reference,
                },
            },
        )
        return self._status_from_response(reference, payload)

    def status(self, reference: str) -> PaymentStatus:
        payload = _request_json(
            "GET",
            f"{self.base_url}/standard/v1/payments/{reference}",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Accept": "*/*",
                "X-Country": self.country,
                "X-Currency": self.currency,
            },
        )
        return self._status_from_response(reference, payload)

    @staticmethod
    def _status_from_response(reference: str, payload: dict[str, Any]) -> PaymentStatus:
        transaction = payload.get("data", {}).get("transaction", {})
        status = str(transaction.get("status", payload.get("status", "PENDING"))).upper()
        return PaymentStatus(
            reference=reference,
            status=status,
            message=str(transaction.get("message", payload.get("message", status))),
            raw_response=payload,
        )


def get_client(provider: MobileMoneyProvider):
    if provider is MobileMoneyProvider.MTN:
        return MtnUgandaClient()
    return AirtelUgandaClient()
