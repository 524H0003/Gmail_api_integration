from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.core.config import settings
from backend.app.schemas.User import UserInfo
from backend.app.api.auth import current_user
from backend.app.schemas.AbsentRequest import AbsentRequestCreate, AbsentRequestResponsePublic
from backend.app.repositories.AbsentRequestRepo import AbsentRequestRepo

router = APIRouter(prefix="/absent-requests")


@router.post(
    "",
    response_model=AbsentRequestResponsePublic,
    status_code=status.HTTP_201_CREATED,
)
def create_absent_request(
    payload: AbsentRequestCreate,
    db_session: Session = Depends(get_db_session),
    current_user: UserInfo = Depends(current_user),
) -> AbsentRequestResponsePublic:
    if not settings.manager_email:
        raise HTTPException(status_code=500, detail="MANAGER_EMAIL is not configured")

    absentRequest_repo = AbsentRequestRepo(db_session)

    request = absentRequest_repo.create(**payload.model_dump(), employee=current_user)

    return AbsentRequestResponsePublic.model_validate(request)


@router.get("", response_model=list[AbsentRequestResponsePublic])
def list_absent_requests(
    db_session: Session = Depends(get_db_session),
    current_user: UserInfo = Depends(current_user),
) -> list[AbsentRequestResponsePublic]:
    absentRequest_repo = AbsentRequestRepo(db_session)

    return [
        AbsentRequestResponsePublic.model_validate(request)
        for request in absentRequest_repo.get_absent_requests_by_employee(
            current_user.id
        )
    ]
