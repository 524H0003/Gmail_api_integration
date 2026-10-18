from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GmailHistory(Base):
    __tablename__ = "GmailHistoryEntity"

    history_id: Mapped[str] = mapped_column(String(200), nullable=False)
