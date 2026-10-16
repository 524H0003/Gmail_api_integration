import base64
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from googleapiclient.errors import HttpError

from app.utils.Google import google
from app.core.config import settings
from app.schemas.Google import EmailWatchResponse


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
        message = f"From: me\r\n"
        message += f"To: {to}\r\n"

        message += f"Subject: {subject}\r\n"

        message += "\r\n"
        message += body

        return base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")

    def receive_email(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Receive emails from Gmail inbox.

        Args:
            max_results: Maximum number of emails to retrieve
            query: Gmail search query (e.g., 'is:unread', 'from:sender@example.com')
            label_ids: List of label IDs to filter by

        Returns:
            List of email dictionaries with message details
        """
        service = self._get_service()

        try:
            results = (
                service.users()
                .messages()
                .list(userId="me", maxResults=max_results, q=query, labelIds=label_ids)
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                email = self._get_email_details(msg["id"])
                if email:
                    emails.append(email)

            return emails
        except HttpError as error:
            print(f"Error receiving emails: {error}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
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
            date = next((h["value"] for h in headers if h["name"] == "Date"), "")

            # Extract email body
            body = self._get_email_body(message["payload"])

            return {
                "message_id": message_id,
                "thread_id": message.get("threadId"),
                "subject": subject,
                "from": from_email,
                "date": date,
                "body": body,
                "labels": message.get("labelIds", []),
                "history_id": message.get("historyId"),
            }
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
        """
        Mark an email as read.

        Args:
            message_id: Gmail message ID

        Returns:
            Response dictionary
        """
        service = self._get_service()

        try:
            service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

            return {"success": True, "message_id": message_id}
        except HttpError as error:
            return {"success": False, "error": str(error)}

    def delete_message(self, message_id: str) -> Dict[str, Any]:
        """
        Delete an email.

        Args:
            message_id: Gmail message ID

        Returns:
            Response dictionary
        """
        service = self._get_service()

        try:
            service.users().messages().trash(userId="me", id=message_id).execute()

            return {"success": True, "message_id": message_id}
        except HttpError as error:
            return {"success": False, "error": str(error)}

    def build_mailto(to: str, subject: str, body: str) -> str:
        return f"mailto:{to}?" f"subject={quote(subject)}&body={quote(body)}"


gmail = Gmail()
