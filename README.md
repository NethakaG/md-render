# Markdown → HTML Microservice (Host + WSO2 APIM)

A tiny FastAPI service that converts Markdown to **sanitized HTML** and is exposed through **WSO2 API Manager**. This README covers the **host-only** setup: the app runs on your PC via uvicorn and WSO2 APIM forwards traffic to it.

## What this does

- Markdown → HTML using **markdown-it-py**
- Always sanitize with **bleach** to prevent XSS
- Expose via **WSO2 APIM** for a stable URL, TLS termination, throttling, and CORS.

## Architecture (host-only)

```
Client / GUI  →  WSO2 APIM Gateway (https://localhost:8243/md/1.0.0)
                                   ↘
                                    FastAPI app (http://host.docker.internal:8000)
```

- APIM terminates HTTPS, enforces throttling/CORS
- The app does the conversion + sanitization

---

## API

### Endpoint

`POST /render`

### Request (application/json)

```json
{
  "markdown": "# Hello",
  "strip_html": false
}
```

### Response (200)

```json
{
  "html": "<h1>Hello</h1>\n",
  "stats": { "chars_in": 8, "chars_out": 17 },
  "sanitized": true,
  "text": null
}
```

### Errors

- **400** invalid JSON / parse error / size limit exceeded
- **415** wrong content type
- **422** missing `markdown`
- **429** throttled by APIM policy

### Limits

- Max markdown size: **51200 bytes**
- UTF‑8 only
- Final HTML sanitized with a conservative allowlist

---

## Local development (host)

### Prereqs

- Python 3.11+
- PowerShell (or Bash)
- Docker (for WSO2 APIM container only)

### Install & run

```powershell
python -m venv .venv
# set at own risk
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run bound to all interfaces so APIM can reach it
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Quick direct test

```powershell
Invoke-RestMethod 'http://localhost:8000/render' -Method POST -ContentType 'application/json' -Body '{ "markdown": "# Hi" }'
```

---

## WSO2 API Manager (host-only wiring)

### Access the UIs (defaults)

- **Publisher**: https://localhost:9443/publisher
- **Dev Portal**: https://localhost:9443/devportal
- **Admin**: https://localhost:9443/admin  
  Login: `admin / admin` (fresh container). Accept the self‑signed cert warning.

### Create/Import the API

1. In **Publisher**, create API via **Import OpenAPI** using `openapi.yaml`.

2. Set **Context**: `md`, **Version**: `1.0.0`.

3. **Production Endpoint**: `http://host.docker.internal:8000`

4. Throttling: e.g., `2PerMin` for demo.

5. **Save → Deploy → Publish** (deploy after any change).

## Tiny web playground GUI

- File: `index.html` (already included)
- For local dev, **keep using the app directly**: `http://localhost:8000/docs`
- To test **through the gateway**, host the file so it has a real origin:
  ```powershell
  python -m http.server 5500
  ```
  Then set in `index.html`:
  ```js
  const GATEWAY_URL = "https://localhost:8243/md/1.0.0/render?pretty=1";
  ```

### CORS in APIM

Enable CORS for your GUI origin (e.g., `http://localhost:5500`):

- Methods: `POST`
- Headers: `Content-Type`
- Save → Deploy the API

---

## Troubleshooting (host-only)

- **Gateway hangs then times out**

  - Ensure uvicorn is running on `0.0.0.0:8000`
  - Endpoint must be `http://host.docker.internal:8000`
  - After changes, **Save → Deploy → Publish** in APIM

- **404 No matching resource**

  - Confirm your API has **POST /render** and the context/version are `/md/1.0.0`
  - Deploy + Publish the revision

- **415 Unsupported Media Type**

  - Send `Content-Type: application/json`

- **400 / 422 JSON errors**

  - Use single quotes around JSON in PowerShell or here-strings

- **CORS errors in GUI**
  - Add your GUI origin in APIM CORS

---

## Project files

- `main.py` — FastAPI app
- `requirements.txt` — dependencies
- `openapi.yaml` — import into WSO2 APIM (POST /render)
- `index.html` — tiny web playground GUI
- `Dockerfile` — optional (not required for host-only mode)

**What WSO2 API Manager did:**

- **Gateway URL:** Clients call `https://localhost:8243/md/1.0.0/render`. WSO2 forwards to my app.
- **Backend endpoint:** Set to `http://host.docker.internal:8000` (because the FastAPI app runs on my host via uvicorn).
- **TLS termination:** HTTPS handled at the gateway; the app stays on HTTP.
- **Throttling:** Applied a demo policy (e.g., `2PerMin`) so bursts get a `429` without reaching the app.
- **CORS at the edge:** Allowed my GUI origin (e.g., `http://localhost:5500`) and header `Content-Type` so the browser can call the API.
- **Versioning:** Context `md` + Version `1.0.0` → clean URL `/md/1.0.0/render` that I can upgrade later.
- **Lifecycle:** After changes I **Save → Deploy → Publish** to roll out safely.

## License

MIT License  
Copyright (c) 2025 Nethaka
