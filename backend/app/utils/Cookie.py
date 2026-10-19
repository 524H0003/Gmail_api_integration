from fastapi import Request, Response
from backend.app.core.config import settings


class Cookie:
    access_token_cookie_key: str = "access_token"

    access_token_expire_minutes: int = 0

    response: Response

    request: Request

    def __init__(self, request: Request, response: Response):
        self.response = response
        self.request = request
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.access_token_cookie_key = settings.access_token_cookie_key

    def set_access_token(self, value: str):
        self.response.set_cookie(
            key=self.access_token_cookie_key,
            value=value,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=self.access_token_expire_minutes * 60,
        )

    def get_access_token(self):
        return self.request.cookies.get(self.access_token_cookie_key)

    def clear(self):
        self.response.delete_cookie(self.access_token_cookie_key)
