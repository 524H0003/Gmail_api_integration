from typing import Optional

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.GmailHistory import GmailHistory


class GmailHistoryRepo:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(
        self,
        history_id: str,
    ):
        self.db_session.execute(delete(GmailHistory))

        new_history = GmailHistory(history_id=history_id)
        self.db_session.add(new_history)

        self.db_session.commit()

    def get(self):
        history = self.db_session.query(GmailHistory).first()
        return history.history_id if history else None
