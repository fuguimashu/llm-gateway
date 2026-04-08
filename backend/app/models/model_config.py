from datetime import datetime

from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModelConfigDB(Base):
    """Persisted model configuration (synced from config.yaml at startup)."""

    __tablename__ = "model_configs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
