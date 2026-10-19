from base64 import b64decode
from json import JSONDecodeError, loads

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pytest import Session

from app.schemas.Google import PubSubEnvelope
from app.utils.Gmail import gmail
from app.db.session import get_db_session
from app.repositories.GmailHistoryRepo import GmailHistoryRepo
from app.repositories.AbsentRequestRepo import AbsentRequestRepo

router = APIRouter(prefix="/webhooks")


@router.post("/gmail", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_webhook(
    envelope: PubSubEnvelope,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db_session),
):
    try:
        notification = loads(b64decode(envelope.message.data))
        history_id = notification["historyId"]

        history_id_db = GmailHistoryRepo(db_session)
        emails = gmail.receive_emails(history_id_db.get() or history_id)
        if not len(emails) == 0: 
            history_id_db.create(history_id)

        absentRequestRepo = AbsentRequestRepo(db_session)

        background_tasks.add_task(absentRequestRepo.processing_emails, emails)

    except (KeyError, ValueError, JSONDecodeError) as error:
        raise HTTPException(
            status_code=400, detail="Invalid Gmail notification"
        ) from error
