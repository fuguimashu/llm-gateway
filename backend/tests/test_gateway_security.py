import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

ENV_KEYS = ("CONFIG_PATH", "MASTER_KEY", "DATABASE_URL", "CORS_ORIGINS")


def clear_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@contextmanager
def load_backend(config_template: str, env_overrides: dict[str, str] | None = None):
    temp_dir = Path(tempfile.mkdtemp(prefix="llm-gateway-test-"))
    db_path = temp_dir / "gateway.db"
    config_path = temp_dir / "config.yaml"
    config_path.write_text(
        config_template.format(db_url=f"sqlite:///{db_path.as_posix()}"),
        encoding="utf-8",
    )

    previous_env = {key: os.environ.get(key) for key in ENV_KEYS}
    try:
        os.environ["CONFIG_PATH"] = str(config_path)
        for key in ENV_KEYS:
            if key != "CONFIG_PATH":
                os.environ.pop(key, None)
        for key, value in (env_overrides or {}).items():
            os.environ[key] = value

        clear_app_modules()

        from app.database import engine, init_db
        from app.main import app
        from app.services.logger import flush_logs

        init_db()
        yield app, engine, flush_logs
    finally:
        try:
            clear_app_modules()
        finally:
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            shutil.rmtree(temp_dir, ignore_errors=True)


class SSEStubServer:
    def __init__(self):
        self.requests: list[dict] = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._build_handler())
        self.base_url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def _build_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                outer.requests.append(json.loads(body))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                chunks = [
                    'data: {"id":"x","object":"chat.completion.chunk","created":0,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}\n\n',
                    'data: {"id":"x","object":"chat.completion.chunk","created":0,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}\n\n',
                    "data: [DONE]\n\n",
                ]
                for chunk in chunks:
                    self.wfile.write(chunk.encode())
                    self.wfile.flush()

            def log_message(self, format, *args):
                return None

        return Handler

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()


class GatewaySecurityTests(unittest.TestCase):
    def test_unknown_model_returns_404_without_fallback(self):
        with SSEStubServer() as stub:
            config = f"""
models:
  - id: "openai/gpt-4o"
    provider: "openai"
    model_name: "gpt-4o"
    api_key: "test"
    base_url: "{stub.base_url}"
settings:
  master_key: "master"
  database_url: "{{db_url}}"
  request_timeout: 5
"""
            with load_backend(config) as (app, engine, flush_logs):
                try:
                    with TestClient(app) as client:
                        created = client.post(
                            "/v1/keys",
                            headers={"Authorization": "Bearer master"},
                            json={"name": "limited", "models": "missing/model"},
                        )
                        key = created.json()["key"]

                        response = client.post(
                            "/v1/chat/completions",
                            headers={"Authorization": f"Bearer {key}"},
                            json={
                                "model": "missing/model",
                                "messages": [{"role": "user", "content": "hello"}],
                                "stream": False,
                            },
                        )
                    flush_logs()
                finally:
                    engine.dispose()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(stub.requests, [])

    def test_models_endpoint_requires_auth_and_filters_virtual_key_models(self):
        config = """
models:
  - id: "openai/gpt-4o"
    provider: "openai"
    model_name: "gpt-4o"
    api_key: "test"
  - id: "openai/gpt-4o-mini"
    provider: "openai"
    model_name: "gpt-4o-mini"
    api_key: "test"
settings:
  master_key: "master"
  database_url: "{db_url}"
"""
        with load_backend(config) as (app, engine, flush_logs):
            try:
                with TestClient(app) as client:
                    anonymous = client.get("/v1/models")
                    created = client.post(
                        "/v1/keys",
                        headers={"Authorization": "Bearer master"},
                        json={"name": "limited", "models": "openai/gpt-4o"},
                    )
                    key = created.json()["key"]
                    limited = client.get(
                        "/v1/models",
                        headers={"Authorization": f"Bearer {key}"},
                    )
                    master = client.get(
                        "/v1/models",
                        headers={"Authorization": "Bearer master"},
                    )
                flush_logs()
            finally:
                engine.dispose()

        self.assertEqual(anonymous.status_code, 401)
        self.assertEqual([item["id"] for item in limited.json()["data"]], ["openai/gpt-4o"])
        self.assertEqual(len(master.json()["data"]), 2)

    def test_cors_origins_env_is_enforced(self):
        config = """
models: []
settings:
  master_key: "master"
  database_url: "{db_url}"
"""
        with load_backend(config, {"CORS_ORIGINS": "https://good.example"}) as (app, engine, flush_logs):
            try:
                with TestClient(app) as client:
                    allowed = client.get("/health", headers={"Origin": "https://good.example"})
                    blocked = client.get("/health", headers={"Origin": "https://evil.example"})
                flush_logs()
            finally:
                engine.dispose()

        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "https://good.example")
        self.assertIsNone(blocked.headers.get("access-control-allow-origin"))

    def test_anthropic_text_blocks_are_preserved(self):
        config = """
models: []
settings:
  master_key: "master"
  database_url: "{db_url}"
"""
        with load_backend(config) as (_, engine, _):
            try:
                from app.providers.anthropic import _to_anthropic_payload
                from app.schemas.chat import ChatCompletionRequest

                request = ChatCompletionRequest(
                    model="anthropic/claude",
                    messages=[
                        {"role": "system", "content": "sys"},
                        {"role": "user", "content": [{"type": "text", "text": "hello"}]},
                    ],
                )
                payload = _to_anthropic_payload(request)
            finally:
                engine.dispose()

        self.assertEqual(payload["messages"][0]["content"], [{"type": "text", "text": "hello"}])

    def test_logger_flush_persists_records(self):
        config = """
models: []
settings:
  master_key: "master"
  database_url: "{db_url}"
"""
        with load_backend(config) as (_, engine, flush_logs):
            try:
                from app.database import SessionLocal
                from app.models.request_log import RequestLog
                from app.services.logger import LogEntry, write_log

                write_log(
                    LogEntry(
                        request_id="req-1",
                        model="openai/gpt-4o",
                        status="success",
                        total_tokens=3,
                    )
                )
                flush_logs()

                db = SessionLocal()
                try:
                    count = db.query(RequestLog).count()
                finally:
                    db.close()
            finally:
                engine.dispose()

        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
