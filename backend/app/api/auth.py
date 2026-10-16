from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.db.session import get_db_session
from app.repositories.UserRepo import UserRepository
from app.schemas.User import UserInfo, UserLogin
from app.utils.Auth import auth
from sqlalchemy.orm import Session
from app.utils.Cookie import Cookie

router = APIRouter(prefix="/auth")


@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(
    payload: UserLogin,
    request: Request,
    response: Response,
    db_session: Session = Depends(get_db_session),
):
    user_repo = UserRepository(db_session)

    user = user_repo.get_by_username(payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Username not found"
        )

    if not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credential"
        )

    cookie = Cookie(request, response)

    cookie.set_access_token(auth.jwt_encode({"userId": user.id}))


@router.get("/me", response_model=UserInfo)
def current_user(
    request: Request, response: Response, db_session: Session = Depends(get_db_session)
):
    cookie = Cookie(request, response)

    userId = auth.jwt_decode(cookie.get_access_token())["userId"]

    if not userId:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid jwt"
        )

    user_repo = UserRepository(db_session)

    user = user_repo.get_by_id(userId)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Username not found"
        )

    return UserInfo(**user)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response):
    cookie = Cookie(request, response)

    cookie.clear()
