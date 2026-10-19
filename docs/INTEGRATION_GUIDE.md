# Prompt Security: Comprehensive Integration Guide

**Prompt Security for Organizational Large Language Models: A Dual-Layer Prompt Injection Detection and Response Security Framework**

This guide provides technical specifications, architectural diagrams, and step-by-step instructions for integrating external client applications, agent frameworks, and microservices with the **Prompt Security Gateway**.

---

## 1. Architectural Overview

Prompt Security functions as an **in-line security proxy** positioning itself between external AI client applications and downstream Large Language Models (LLMs).

```
   ┌────────────────────────────────────────────────────────┐
   │            External Client Applications                │
   │  (OpenAI SDK, LangChain, Open WebUI, REST Service)     │
   └───────────────────────────┬────────────────────────────┘
                               │ POST /api/v1/chat/completions
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │          Prompt Security Gateway Middleware            │
   │                                                        │
   │  1. Inbound Security (Layer 1):                        │
   │     - Rule Heuristics (40% weight)                     │
   │     - DistilBERT Classifier (60% weight, cutoff 0.38)  │
   │     - Decision: ALLOW or BLOCK                         │
   │                                                        │
   │     [If BLOCK: Stops execution; LLM NEVER invoked]     │
   │                                                        │
   │  2. Downstream LLM Dispatch (if ALLOW):                │
   │     - Local Simulation Engine (offline demo-gpt-4o)    │
   │     - Ollama Local LLM (http://localhost:11434/v1)     │
   │     - OpenAI Cloud Provider (api.openai.com/v1)        │
   │                                                        │
   │  3. Outbound Security (Layer 2):                       │
   │     - Secret & Canary Leakage Detection                │
   │     - PII & Credential Masking                         │
   │     - System Prompt Exfiltration Interception          │
   │     - Decision: SAFE, MASK, or BLOCK                   │
   │                                                        │
   │  4. Delivery & Telemetry:                              │
   │     - Logs incident to database (GW- prefix)           │
   │     - Returns standard OpenAI Chat Completion JSON     │
   └───────────────────────────┬────────────────────────────┘
                               │ Verified Safe Output
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │               End User / Application                   │
   └────────────────────────────────────────────────────────┘
```

---

## 2. Gateway Endpoints & Protocols

| Endpoint Path | Method | Security Enforcement | Request / Response Format |
| :--- | :--- | :--- | :--- |
| `/api/v1/chat/completions` | `POST` | Dual-Layer (L1 Inbound + L2 Outbound) | OpenAI Chat Completion JSON |
| `/v1/chat/completions` | `POST` | Dual-Layer (L1 Inbound + L2 Outbound) | OpenAI Root Compatibility Alias |
| `/api/external-demo/chat` | `POST` | Dual-Layer + Telemetry Pipeline | Playground JSON |
| `/api/integration/status` | `GET` | Public Gateway & Downstream Metadata | Status JSON (No secrets exposed) |
| `/api/integration/test-connection` | `POST` | Connectivity & Health Verification | Healthcheck JSON |

### Response Headers
Every gateway response returns security audit metadata in HTTP headers:
- `X-Request-ID`: Unique tracking identifier (`GW-XXXXXXXX`).
- `X-Prompt-Security-Verdict`: Overall transaction verdict (`ALLOW`, `BLOCK`, `PROTECTED_BLOCK`, `REDACTED`).
- `X-Prompt-Security-L1`: Layer 1 screening decision (`ALLOW` or `BLOCK`).
- `X-Prompt-Security-L2`: Layer 2 egress inspection decision (`SAFE`, `MASK`, `BLOCK`, or `NOT_EXECUTED`).

---

## 3. Policy: Streaming Prohibited by Design

Prompt Security explicitly rejects streaming requests (`stream=true`) with **HTTP 400 Bad Request**:

```json
{
  "error": {
    "message": "Streaming is not supported: Prompt Security enforces complete Layer 2 response inspection before egress. Please set stream=false in your client configuration.",
    "type": "invalid_request_error",
    "param": "stream",
    "code": "streaming_disabled_by_policy"
  }
}
```

### Security Rationale
Streaming uninspected tokens directly to an end user's terminal or web interface violates egress response protection. If an LLM leaks an enterprise API key, canary credential, or database password mid-generation, streaming immediately transmits the secret before Layer 2 can inspect or redact it. Prompt Security guarantees that all responses are completely scanned and sanitized before any bytes reach the client.

---

## 4. Supported Integration Methods

### Method 1: Python OpenAI SDK
To protect any existing Python script or service using the `openai` package, change the `base_url`:

```python
from openai import OpenAI

# Point client to Prompt Security Gateway
client = OpenAI(
    base_url="http://localhost:5000/api/v1",
    api_key="none"  # Or your GATEWAY_API_KEY if configured in .env
)

response = client.chat.completions.create(
    model="demo-gpt-4o",  # or your downstream model name
    messages=[
        {"role": "user", "content": "Explain multi-factor authentication security benefits."}
    ],
    stream=False  # Required by Layer 2 security policy
)

print(response.choices[0].message.content)
```

---

### Method 2: LangChain & LlamaIndex

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:5000/api/v1",
    api_key="none",
    model="demo-gpt-4o",
    streaming=False
)

response = llm.invoke("Summarize organizational password hygiene.")
print(response.content)
```

---

### Method 3: Local AI & Ollama (Zero Cloud Fees)
To use local Ollama models (`llama3.2`, `mistral`, `codellama`) running on `http://localhost:11434`:

1. Configure `.env` in the Prompt Security project:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434/v1
   OLLAMA_MODEL=llama3.2
   ```
2. Start your local Ollama server:
   ```bash
   ollama run llama3.2
   ```
3. Route your client requests to Prompt Security Gateway (`http://localhost:5000/api/v1`). The gateway screens inbound prompts, dispatches allowed requests to Ollama, inspects Ollama's response with Layer 2, and returns sanitized answers.

---

### Method 4: Custom REST Microservices (cURL / Fetch)

```bash
curl -X POST "http://localhost:5000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "demo-gpt-4o",
    "messages": [
      {"role": "user", "content": "Explain multi-factor authentication."}
    ],
    "stream": false
  }'
```

**Node.js (Fetch):**
```javascript
const response = await fetch("http://localhost:5000/api/v1/chat/completions", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "demo-gpt-4o",
    messages: [{ role: "user", content: "Explain multi-factor authentication." }],
    stream: false
  })
});
const data = await response.json();
console.log(data.choices[0].message.content);
```

---

### Method 5: Browser Extension
The included browser extension (`browser_extension/`) provides client-side protection directly in web browsers:
- Monitors input textareas on ChatGPT (`chatgpt.com`), Claude (`claude.ai`), and Google Gemini (`gemini.google.com`).
- Intercepts user submissions before they are sent to the web AI service.
- Dispatches prompt text to `http://localhost:5000/detect`.
- If an injection is detected, warns the user or blocks submission in the browser DOM.

---

## 5. Security & Authentication Configuration

Authentication on the Prompt Security Gateway is controlled via the `GATEWAY_API_KEY` environment variable in `.env`:

```bash
# Optional: Enforce Bearer token authentication on the Gateway
GATEWAY_API_KEY=your_secure_random_key_here
```

- **When `GATEWAY_API_KEY` is set:** Clients must provide `Authorization: Bearer <GATEWAY_API_KEY>`. Missing or incorrect keys receive `HTTP 401 Unauthorized`.
- **When `GATEWAY_API_KEY` is empty (default):** Gateway runs in open development/internal network mode.

---

## 6. Standalone External Client Application Demo

To demonstrate gateway integration without opening the Prompt Security web interface, a standalone sample client is provided at `examples/external_client_app.py`.

### Automated CLI Verification
```bash
./.venv/bin/python examples/external_client_app.py
```
Executes Scenarios A, B, and C against the running gateway and reports the verdict for each stage.

### Interactive Terminal Mode
```bash
./.venv/bin/python examples/external_client_app.py --interactive
```

### Standalone Web Application (Port 8080)
```bash
./.venv/bin/python examples/external_client_app.py --web --port 8080
```
Launches an Acme Enterprise AI Assistant web application at `http://localhost:8080`. Users can test prompts through a third-party application UI and observe real-time gateway protection.

---

## 7. Security Dashboard & Channel Tracking

All gateway transactions are persistently logged to the SQLite database and visible in the **Security Dashboard** (`/dashboard`):
- Filter by channel: **Gateway API (`GW-`)**, **Playground Demo (`EXT-`)**, or **Internal Analyzer (`REQ-`)**.
- Filter by Layer 1 decision (`ALLOW` / `BLOCK`).
- Filter by Layer 2 decision (`SAFE` / `MASK` / `BLOCK`).
