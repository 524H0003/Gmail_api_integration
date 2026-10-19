from sqlalchemy import String, Text

from backend.app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "UserEntity"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

    hashed_password: Mapped[str] = mapped_column(Text)
