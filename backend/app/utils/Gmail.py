import base64
from email.message import EmailMessage
import threading
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from googleapiclient.errors import HttpError

from backend.app.utils.Google import google
from backend.app.core.config import settings
from backend.app.schemas.Google import EmailWatchResponse
from backend.app.schemas.Email import EmailSchema
from email.utils import parsedate_to_datetime


class Gmail:
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    pubsub_oidc_topic: str = ""

    def __init__(self):
        self._local = threading.local()  # <-- Tạo thread-local storage

        if not settings.pubsub_oidc_topic:
            raise KeyError("Missing PUBSUB_OIDC_TOPIC environment value")
        self.pubsub_oidc_topic = settings.pubsub_oidc_topic

    def _get_service(self):
        if not hasattr(self._local, "service") or self._local.service is None:
            google.authenticate(self.SCOPES)
            self._local.service = google.build("gmail", "v1")
        return self._local.service

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        service = self._get_service()

        message = {
            "raw": self._create_message(
                to=to,
                subject=subject,
                body=body,
            )
        }

        try:
            message = (
                service.users().messages().send(userId="me", body=message).execute()
            )

            return {
                "success": True,
                "message_id": message["id"],
                "thread_id": message.get("threadId"),
            }
        except HttpError as error:
            return {"success": False, "error": str(error)}

    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> str:
        message = EmailMessage()
        message["To"] = to
        message["From"] = "me"
        message["Subject"] = subject
        message.add_alternative(body, subtype="html")

        return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")

    def _get_emails(self, message_dict: Dict[str, Dict]) -> List[EmailSchema]:
        emails = []
        for msg_id in message_dict.keys():
            detail = self._get_email_details(msg_id)
            if detail is not None:
                emails.append(detail)
        return emails

    def receive_emails(self, limit: int) -> List[EmailSchema]:
        service = self._get_service()
        response = (
            service.users().messages().list(userId="me", maxResults=limit).execute()
        )
        return self._get_emails(
            {msg["id"]: msg for msg in response.get("messages", [])}
        )

    def receive_emails_by_history_id(
        self, start_history_id: Optional[str] = None
    ) -> List[EmailSchema]:
        service = self._get_service()

        if not start_history_id:
            emails = self.receive_emails(10)

            start_history_id = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=emails[-1].message_id,
                    format="minimal",
                )
                .execute()
                .get("historyId")
            )

        try:
            history_response = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=start_history_id,
                    historyTypes=["messageAdded"],
                )
                .execute()
            )

            histories = history_response.get("history", [])

            message_dict = {}
            for history in histories:
                messages_added = history.get("messagesAdded", [])
                for message_item in messages_added:
                    msg = message_item.get("message")
                    if msg and "id" in msg:
                        message_dict[msg["id"]] = msg

            return self._get_emails(message_dict)

        except HttpError as error:
            if error.resp.status in (400, 404):
                print(f"startHistoryId {start_history_id} is invalid or expired.")
            else:
                print(f"Error receiving emails: {error}")
            return []

    def _get_email_details(self, message_id: str) -> EmailSchema:
        service = self._get_service()

        try:
            message = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = message["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            from_email = next((h["value"] for h in headers if h["name"] == "From"), "")
            date_str = next((h["value"] for h in headers if h["name"] == "Date"), "")
            date = parsedate_to_datetime(date_str) if date_str else None

            # Extract email body
            body = self._get_email_body(message["payload"])

            return EmailSchema(
                message_id=message_id,
                subject=subject,
                from_email=from_email,
                body=body,
                date=date,
            )
        except HttpError as error:
            print(f"Error getting email details: {error}")
            return None

    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        if "parts" in payload:
            # Handle multipart messages
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    return self._decode_body(part["body"])
                elif part["mimeType"] == "text/html":
                    return self._decode_body(part["body"])
        elif payload["mimeType"] == "text/plain":
            return self._decode_body(payload["body"])
        elif payload["mimeType"] == "text/html":
            return self._decode_body(payload["body"])

        return ""

    def _decode_body(self, body: Dict[str, Any]) -> str:
        if "data" in body:
            data = body["data"].replace("-_", "+").replace("_", "/")
            return base64.urlsafe_b64decode(data).decode("utf-8")
        return ""

    def watch_email(self) -> EmailWatchResponse:
        """
        https://developers.google.com/workspace/gmail/api/guides/push?authuser=1#watch-request
        """
        service = self._get_service()

        try:
            watch_response = (
                service.users()
                .watch(
                    userId="me",
                    body={"labelIds": ["INBOX"], "topicName": self.pubsub_oidc_topic},
                )
                .execute()
            )

            return EmailWatchResponse(**watch_response, success=True)
        except HttpError as error:
            return EmailWatchResponse(success=False, error=str(error))

    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        service = self._get_service()

        try:
            service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

            return {"success": True, "message_id": message_id}
        except HttpError as error:
            return {"success": False, "error": str(error)}

    def delete_message(self, message_id: str) -> Dict[str, Any]:
        service = self._get_service()

        try:
            service.users().messages().trash(userId="me", id=message_id).execute()

            return {"success": True, "message_id": message_id}
        except HttpError as error:
            return {"success": False, "error": str(error)}

    def build_mailto(self, to: str, subject: str, body: str) -> str:
        return f"mailto:{to}?" f"subject={quote(subject)}&body={quote(body)}"


gmail = Gmail()
