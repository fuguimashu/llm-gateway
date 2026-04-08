# LLM Gateway

**English** | [中文](README.zh-CN.md)

A minimal, self-hosted LLM proxy with an OpenAI-compatible API. Built as an auditable replacement for LiteLLM after the [March 2026 supply-chain attack](https://github.com/BerriAI/litellm/issues/9354) (v1.82.7–v1.82.8).

**Design goals:** small enough to read in an afternoon (~2500 lines of application code), no hidden network calls at import time, no build-time code execution, zero external service dependencies.

---

## Features

| Capability | Details |
|---|---|
| **Unified API** | Single `/v1/chat/completions` endpoint, OpenAI-compatible |
| **Providers** | OpenAI, Anthropic, Ollama (and any OpenAI-compatible endpoint) |
| **Streaming** | Upstream always streamed; client can request streaming or buffered |
| **Virtual Keys** | Issue scoped `sk-` API keys with optional per-model whitelists |
| **Fallback** | Priority-ordered provider list; auto-skips models in cooldown |
| **Health tracking** | Passive: 3 consecutive failures → 30 s cooldown, no pinging |
| **Request logs** | SQLite: timestamp, model, tokens, latency, status |
| **Dashboard** | Next.js 15 UI — stats, key management, log browser, model health |

**Not included by design:** load balancing, cost tracking, caching, image generation, function calling, multi-tenancy.

---

## Quick Start

### Docker Compose (recommended)

```bash
# 1. Clone
git clone https://github.com/fuguimashu/llm-gateway.git
cd llm-gateway

# 2. Create config
cp backend/config.yaml.example config.yaml
# Edit config.yaml — add your API keys and models

# 3. Create env file
cp .env.example .env
# Edit .env — set MASTER_KEY to something strong

# 4. Create data directory
mkdir -p data

# 5. Start
docker compose up -d

# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
```

Open `http://localhost:3000`, enter your `MASTER_KEY`, and you're in.

### Local Development

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and edit config
cp config.yaml.example config.yaml

# Run
MASTER_KEY=dev uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local if backend isn't at http://localhost:8000

pnpm install   # or npm install
pnpm dev
```

---

## Configuration

All configuration lives in `config.yaml`. Environment variables override `settings` values.

```yaml
models:
  - id: "openai/gpt-4o"        # identifier used by clients
    provider: "openai"          # openai | anthropic | ollama
    model_name: "gpt-4o"        # actual model name sent to provider
    api_key: "sk-..."
    priority: 0                 # lower = higher priority for fallback

  - id: "anthropic/claude-sonnet-4-6"
    provider: "anthropic"
    model_name: "claude-sonnet-4-6"
    api_key: "sk-ant-..."
    priority: 0

  - id: "ollama/llama3.2"
    provider: "ollama"
    model_name: "llama3.2"
    base_url: "http://localhost:11434"
    priority: 2

settings:
  master_key: "your-master-key"
  database_url: "sqlite:///./data/llm_gateway.db"
  health_fail_threshold: 3      # consecutive failures before cooldown
  health_cooldown_seconds: 30   # seconds to wait after threshold hit
  request_timeout: 120          # upstream request timeout in seconds
```

### Environment Variable Overrides

| Variable | Overrides |
|---|---|
| `MASTER_KEY` | `settings.master_key` |
| `DATABASE_URL` | `settings.database_url` |
| `CONFIG_PATH` | path to config.yaml (default: `config.yaml`) |
| `NEXT_PUBLIC_API_URL` | backend URL as seen by the browser |

---

## API Reference

All endpoints accept `Authorization: Bearer <key>` where `<key>` is either your master key or a virtual key.

### Chat Completions

```
POST /v1/chat/completions
```

OpenAI-compatible. The `model` field must match a configured model `id`.

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

Streaming:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-4o", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

### Models

```
GET /v1/models
```

Lists all active models with health status. OpenAI-compatible format.

### Virtual Keys

All key management endpoints require the master key.

```bash
# List keys
GET /v1/keys

# Create key (all models)
POST /v1/keys
{"name": "My App"}

# Create key (model whitelist)
POST /v1/keys
{"name": "Restricted App", "models": "openai/gpt-4o,openai/gpt-4o-mini"}

# Deactivate key
DELETE /v1/keys/{key_id}

# Re-activate key
POST /v1/keys/{key_id}/activate
```

### Logs

```bash
# All logs (paginated)
GET /v1/logs?page=1&page_size=50

# Filtered
GET /v1/logs?model=openai/gpt-4o&status=error

# Health check
GET /health
```

---

## Using with OpenAI SDK

Point the SDK at your gateway — no other changes needed:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-your-virtual-key",
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:8000/v1",
  apiKey: "sk-your-virtual-key",
});
```

---

## Fallback & Health Checking

The gateway tracks model health **passively** — only based on actual request outcomes, never by pinging providers.

```
Request arrives
  └─ Find candidates matching requested model (by id)
       └─ Sort by priority (ascending)
            └─ Skip models in cooldown
                 └─ Try first available
                      ├─ Success → reset failure count, return response
                      └─ Failure (connect/timeout/5xx) → increment failure count
                           ├─ count < threshold → try next candidate
                           └─ count >= threshold → enter cooldown (30s), try next
```

After cooldown expires, the model becomes eligible again automatically. A single success resets the failure count.

---

## Architecture

```
Client
  │  Bearer sk-xxx
  ▼
FastAPI  (/v1/chat/completions)
  │
  ├─ auth.py          ← validate virtual key, check model whitelist
  ├─ proxy_service.py ← select provider, fallback loop
  │    ├─ health_checker.py  ← in-memory failure tracking
  │    └─ logger.py          ← async SQLite write
  │
  └─ providers/
       ├─ openai.py      ← OpenAI / Ollama / compatible endpoints
       └─ anthropic.py   ← format translation (OpenAI ↔ Anthropic SSE)
```

**Key design decisions:**

- Upstream requests are **always streaming** (`httpx` async byte iteration), even when the client requests non-streaming. This avoids buffering large responses in memory.
- The health checker is **purely in-memory** — it resets on restart. This is intentional: a fresh start should give all models a clean slate.
- API keys are stored as-is in SQLite. For production use with sensitive keys, consider encrypting the database or using a secrets manager to inject keys via environment variables instead of config.yaml.

---

## Security Notes

- **Master key**: use a long random string (`openssl rand -hex 32`). It controls everything.
- **Virtual keys**: issue one per client application. Revoke individually without affecting others.
- **config.yaml**: contains provider API keys — keep it out of version control (already in `.gitignore` template below).
- **SQLite file**: contains request logs and key metadata — restrict file permissions in production.
- **CORS**: defaults to `*` for local use. Set `CORS_ORIGINS` in `.env` for production.
- **Network exposure**: in production, run behind a reverse proxy (nginx/Caddy) with TLS.

Recommended `.gitignore` additions:

```
.env
config.yaml
data/
*.db
```

---

## Project Structure

```
llm-gateway/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # YAML + env config loader
│   │   ├── database.py          # SQLAlchemy + SQLite
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routes/              # API route handlers
│   │   ├── services/            # Business logic (auth, proxy, health, logger)
│   │   └── providers/           # LLM provider adapters
│   ├── requirements.txt
│   ├── Dockerfile
│   └── config.yaml.example
├── frontend/
│   ├── app/                     # Next.js 15 App Router pages
│   ├── components/              # React components
│   ├── lib/                     # API client + utilities
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Dependency Audit

The backend has 8 direct dependencies — all well-established, no telemetry, no auto-update behavior:

| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.115.6 | HTTP framework |
| uvicorn | 0.32.1 | ASGI server |
| sqlalchemy | 2.0.36 | ORM + SQLite |
| httpx | 0.27.2 | Async HTTP client |
| pydantic | 2.10.3 | Data validation |
| pydantic-settings | 2.6.1 | Settings management |
| python-dotenv | 1.0.1 | .env loading |
| pyyaml | 6.0.2 | YAML config parsing |

To audit for known vulnerabilities:

```bash
pip install pip-audit
pip-audit -r backend/requirements.txt
```

---

## License

MIT
