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
    )

    return Config(models=models, settings=settings)


# Singleton loaded at import time
config = load_config()
