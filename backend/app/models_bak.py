from datetime import date, datetime
from enum import StrEnum
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base




class GmailSyncState(Base):
    last_history_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    watch_expiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
