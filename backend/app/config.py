"""Configuration management: loads config.yaml + environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ModelConfig:
    id: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = True
    priority: int = 0


@dataclass
class Settings:
    master_key: str = "changeme"
    database_url: str = "sqlite:///./llm_gateway.db"
    health_fail_threshold: int = 3
    health_cooldown_seconds: int = 30
    request_timeout: int = 120
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    models: list[ModelConfig] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)


def load_config() -> Config:
    config_path = Path(os.getenv("CONFIG_PATH", "config.yaml"))

    if not config_path.exists():
        # Try example file for development
        example = config_path.parent / "config.yaml.example"
        if example.exists():
            config_path = example
        else:
            return Config()

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    models = []
    for m in raw.get("models", []):
        # Environment variable override: API keys can be set via env
        api_key = m.get("api_key") or os.getenv(
            f"PROVIDER_API_KEY_{m['id'].upper().replace('/', '_').replace('-', '_')}"
        )
        models.append(
            ModelConfig(
                id=m["id"],
                provider=m["provider"],
                model_name=m["model_name"],
                api_key=api_key,
                base_url=m.get("base_url"),
                is_active=m.get("is_active", True),
                priority=m.get("priority", 0),
            )
        )

    s = raw.get("settings", {})
    settings = Settings(
        master_key=os.getenv("MASTER_KEY", s.get("master_key", "changeme")),
        database_url=os.getenv("DATABASE_URL", s.get("database_url", "sqlite:///./llm_gateway.db")),
        health_fail_threshold=s.get("health_fail_threshold", 3),
        health_cooldown_seconds=s.get("health_cooldown_seconds", 30),
        request_timeout=s.get("request_timeout", 120),
        cors_origins=_parse_cors_origins(
            os.getenv("CORS_ORIGINS"),
            s.get("cors_origins"),
        ),
    )

    return Config(models=models, settings=settings)


def _parse_cors_origins(env_value: str | None, raw_value: object) -> list[str]:
    if env_value:
        parsed = [origin.strip() for origin in env_value.split(",") if origin.strip()]
        if parsed:
            return parsed

    if isinstance(raw_value, list):
        parsed = [str(origin).strip() for origin in raw_value if str(origin).strip()]
        if parsed:
            return parsed

    if isinstance(raw_value, str):
        parsed = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        if parsed:
            return parsed

    return ["*"]


# Singleton loaded at import time
config = load_config()
