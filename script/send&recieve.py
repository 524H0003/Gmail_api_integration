import argparse
from pathlib import Path
from backend.app.utils.Gmail import gmail
from backend.app.core.config import settings


def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    response = gmail.send_email(
        to=recipient,
        subject=subject,
        body=body,
    )
    if response["success"]:
        return str(response["message_id"])
    else:
        raise Exception(response["error"])


def receive_emails(
    start_history_id: str,
) -> list:
    emails = gmail.receive_emails(start_history_id)
    return emails


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gmail API tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Send email command
    send_parser = subparsers.add_parser("send", help="Send an email")
    send_parser.add_argument(
        "recipient", help="Email address that receives the message"
    )
    send_parser.add_argument("--subject", default="Hello World", help="Email subject")
    send_parser.add_argument("--body", default="Hello World!", help="Email body")

    # Receive emails command
    receive_parser = subparsers.add_parser("receive", help="Receive emails")
    receive_parser.add_argument("start_history_id", help="Start history ID")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not Path(settings.google_credentials_path).exists():
        raise SystemExit(
            f"OAuth client file not found: {settings.google_credentials_path}\n"
            "See script/README.md for setup instructions."
        )

    if args.command == "send":
        message_id = send_email(
            recipient=args.recipient,
            subject=args.subject,
            body=args.body,
        )
        print(f"Email sent successfully. Gmail message id: {message_id}")
    elif args.command == "receive":
        emails = receive_emails(args.start_history_id)
        print(f"Received {len(emails)} emails")


if __name__ == "__main__":
    main()
