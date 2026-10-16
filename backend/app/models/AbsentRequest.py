from datetime import date
import uuid

from sqlalchemy import UUID, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.User import User
from app.types import AbsentStatus


class AbsentRequest(Base):
    __tablename__ = "AbsentRequestEntity"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    absent_type: Mapped[str] = mapped_column(String(80))

    start_date: Mapped[date] = mapped_column(Date)

    end_date: Mapped[date] = mapped_column(Date)

    reason: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default=AbsentStatus.PENDING.value)

    gmail_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    decision_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    security_code: Mapped[str | None] = mapped_column(String(6), nullable=True)

    user: Mapped[User] = relationship(
        primaryjoin="AbsentRequest.employee_id == User.id",
    )
