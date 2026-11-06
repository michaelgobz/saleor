# Katale MTN and Airtel Money app

This local Saleor payment app supports Uganda sandbox collection flows for:

- MTN MoMo Collection API
- Airtel Money Open API

The app exposes a Saleor manifest at `/api/manifest` and a synchronous transaction
webhook at `/webhooks/transaction`. Provider credentials are read from environment
variables and are never stored in the repository.

## Run locally

```powershell
Set-Location apps\mobile-money
Copy-Item .env.example .env
python app.py
```

The app listens on `http://127.0.0.1:8001` by default. Configure `MOBILE_MONEY_APP_URL`
to the URL reachable by Saleor before installing the app.

## Saleor installation

The Dashboard Explore catalog contains informational entries whose `manifestUrl` is
null, so they cannot be installed automatically on a local instance. Install this
custom app with the Saleor `appInstall` mutation using:

```text
http://127.0.0.1:8001/api/manifest
```

The app requires `MANAGE_PAYMENTS`. Configure either MTN or Airtel credentials before
processing a real sandbox payment. The checkout payment data must include a provider
(`mtn` or `airtel`) and a Uganda mobile number under `phone`, `phoneNumber`, `msisdn`,
or `mobileNumber`.

This implementation intentionally returns an action-required result while a provider
reports a pending payment. A production deployment should add a shared durable store
for provider references and provider callbacks before enabling retries across multiple
pods.
