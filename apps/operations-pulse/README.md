# Katale Operations Pulse

This is a Saleor app extension that adds a live Operations Pulse widget to the
Dashboard home page using the `HOMEPAGE_WIDGETS` mount introduced in Saleor 3.23.

The Dashboard sends the Saleor GraphQL URL and a short-lived app/user access token
to the widget with a `POST` request. The app uses that token to read order, product,
and customer totals; no Saleor credentials are stored by this app.

## Run locally

```powershell
Set-Location apps\operations-pulse
python app.py
```

The manifest is available at:

```text
http://127.0.0.1:8002/api/manifest
```

Install that manifest in Saleor with the `appInstall` mutation, then open the
Dashboard home page. The installing user must have the permissions declared in the
manifest.
