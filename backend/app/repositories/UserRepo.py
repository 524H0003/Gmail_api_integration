from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.User import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.session.scalar(stmt)

    def create(
        self,
        username: str,
        name: str,
        email: str,
        hashed_password: str,
    ) -> User:
        new_user = User(
            username=username, email=email, hashed_password=hashed_password, name=name
        )

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        return new_user
