import base64
from email.message import EmailMessage
from typing import List, Dict, Any
from urllib.parse import quote
from googleapiclient.errors import HttpError

from app.utils.Google import google
from app.core.config import settings
from app.schemas.Google import EmailWatchResponse
from app.schemas.Email import EmailSchema


class Gmail:
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    pubsub_oidc_topic: str = ""

    def __init__(self):
        self.service = None

        if not settings.pubsub_oidc_topic:
            raise KeyError("Missing PUBSUB_OIDC_TOPIC environment value")
        self.pubsub_oidc_topic = settings.pubsub_oidc_topic

    def _get_service(self):
        if not self.service:
            google.authenticate(self.SCOPES)
            self.service = google.build("gmail", "v1")
        return self.service

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

    def receive_emails(self, start_history_id: str) -> List[EmailSchema]:
        service = self._get_service()

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

            emails = []
            for msg_id in message_dict.keys():
                email = self._get_email_details(msg_id)
                if email:
                    emails.append(email)

            return emails

        except HttpError as error:
            if error.resp.status in (400, 404):
                print(f"startHistoryId {start_history_id} is invalid or expired.")
            else:
                print(f"Error receiving emails: {error}")
            return []

    def _get_email_details(self, message_id: str) -> EmailSchema:
        """
        Get detailed information about a specific email.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email details
        """
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

            # Extract email body
            body = self._get_email_body(message["payload"])

            return EmailSchema(
                message_id=message_id,
                subject=subject,
                from_email=from_email,
                body=body,
            )
        except HttpError as error:
            print(f"Error getting email details: {error}")
            return None

    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from payload.

        Args:
            payload: Email message payload

        Returns:
            Email body text
        """
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
        """
        Decode email body from base64.

        Args:
            body: Email body dictionary

        Returns:
            Decoded body text
        """
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
