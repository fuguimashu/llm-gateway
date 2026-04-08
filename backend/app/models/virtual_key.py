from datetime import datetime

from sqlalchemy import Boolean, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VirtualKey(Base):
    __tablename__ = "virtual_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    models: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated, null = all
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def allowed_models(self) -> list[str] | None:
        """None means all models allowed."""
        if not self.models:
            return None
        return [m.strip() for m in self.models.split(",") if m.strip()]
