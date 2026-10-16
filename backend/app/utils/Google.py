import os
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from app.core.config import settings
from googleapiclient.discovery import build
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class Google:
    def __init__(self):
        self.credentials_path = settings.google_credentials_path
        self.creds: Optional[Credentials] = None

    def authenticate(self, SCOPES: list[str]) -> Credentials:
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        return self.creds

    def build(self, *args: P.args, **kwargs: P.kwargs):
        kwargs_dict = dict(kwargs)
        kwargs_dict["credentials"] = self.creds

        return build(*args, **kwargs_dict)


google = Google()
