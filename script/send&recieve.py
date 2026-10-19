import argparse
from pathlib import Path

from tabulate import tabulate
from backend.app.schemas.Email import EmailSchema
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
    receive_parser.add_argument(
        "--limit", type=int, default=10, help="Number of emails to display"
    )

    return parser.parse_args()


def display_email_details(email: EmailSchema) -> None:
    print(f"\nFrom: {email.from_email}")
    print(f"Subject: {email.subject}")
    print(f"Date: {email.date}")
    print(f"\n{email.body}")


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
        emails = gmail.receive_emails(limit=args.limit)
        if not emails:
            print("No new emails found.")
        else:
            table_data = []
            for i, email in enumerate(emails):
                table_data.append([i + 1, email.from_email, email.subject, email.date])

            headers = ["No", "From", "Subject", "Date"]

            while True:
                try:
                    choice = int(
                        input(
                            "\nEnter email number to view details (0 to exit; -1 to show emails): "
                        )
                    )
                    if choice == 0:
                        break
                    elif choice == -1:
                        print(tabulate(table_data, headers=headers, tablefmt="grid"))
                    elif 1 <= choice <= len(emails):
                        display_email_details(emails[choice - 1])
                    else:
                        print("Invalid email number. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")


if __name__ == "__main__":
    main()
