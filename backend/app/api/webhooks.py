from base64 import b64decode
from json import JSONDecodeError, loads

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas.Google import PubSubEnvelope
from backend.app.utils.Gmail import gmail
from backend.app.db.session import get_db_session, SessionFactory
from backend.app.repositories.GmailHistoryRepo import GmailHistoryRepo
from backend.app.repositories.AbsentRequestRepo import AbsentRequestRepo
from backend.app.schemas.Email import EmailSchema

router = APIRouter(prefix="/webhooks")


def process_emails_background(history_id: str):
    with SessionFactory() as session:
        history_id_db = GmailHistoryRepo(session)
        emails = gmail.receive_emails_by_history_id(history_id_db.get())
        if emails:
            history_id_db.create(history_id)

            repo = AbsentRequestRepo(session)
            repo.processing_emails(emails)


@router.post("/gmail", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_webhook(
    envelope: PubSubEnvelope,
    background_tasks: BackgroundTasks,
):
    try:
        notification = loads(b64decode(envelope.message.data))
        history_id = notification["historyId"]

        background_tasks.add_task(process_emails_background, history_id)

    except (KeyError, ValueError, JSONDecodeError) as error:
        raise HTTPException(
            status_code=400, detail="Invalid Gmail notification"
        ) from error
