from datetime import date
import html
from pathlib import Path
import secrets
from string import Template
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.AbsentRequest import AbsentRequest
from app.types import AbsentStatus
from app.utils.Gmail import gmail
from app.core.config import settings
from app.schemas.User import UserInfo
from app.schemas.Email import EmailSchema


class AbsentRequestRepo:
    manager_email: str = ""
    sender_email: str = ""
    email_template: str = ""

    def __init__(self, db_session: Session):
        self.db_session = db_session

        if not settings.manager_email:
            raise KeyError("Missing MANAGER_EMAIL environment value")
        self.manager_email = settings.manager_email

        if not settings.sender_email:
            raise KeyError("Missing SENDER_EMAIL environment value")
        self.sender_email = settings.sender_email

        if not settings.email_template_file:
            raise KeyError("Missing EMAIL_TEMPLATE_FILE environment value")
        self.email_template_file = settings.email_template_file

    def _build_mail(self, employee: UserInfo, request: AbsentRequest):
        values = {
            "employee_name": html.escape(employee.name),
            "employee_email": html.escape(employee.email),
            "absent_type": html.escape(request.absent_type),
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "reason": html.escape(request.reason),
        }

        approve_mailto = html.escape(
            gmail.build_mailto(
                self.sender_email,
                str(request.id),
                f"{AbsentStatus.APPROVED} {request.security_code}",
            ),
            quote=True,
        )
        reject_mailto = html.escape(
            gmail.build_mailto(
                self.sender_email,
                str(request.id),
                f"{AbsentStatus.REJECTED} {request.security_code}",
            ),
            quote=True,
        )

        template_path = Path(self.email_template_file)
        if not template_path.is_absolute():
            template_path = Path(__file__).resolve().parents[2] / template_path
        template = Template(template_path.read_text(encoding="utf-8"))

        return template.safe_substitute(
            **values,
            request_id=str(request.id),
            approve_mailto=approve_mailto,
            reject_mailto=reject_mailto,
        )

    def create(
        self,
        employee: UserInfo,
        absent_type: str,
        start_date: date,
        end_date: date,
        reason: str,
    ) -> AbsentRequest:
        security_code = secrets.token_hex(3).upper()

        new_request = AbsentRequest(
            employee_id=employee.id,
            absent_type=absent_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            security_code=security_code,
        )

        self.db_session.add(new_request)
        self.db_session.commit()
        self.db_session.refresh(new_request)

        message_id = gmail.send_email(
            self.manager_email,
            f"Absent request from {employee.name}",
            self._build_mail(employee, new_request),
        )["message_id"]

        new_request.gmail_message_id = message_id

        self.db_session.add(new_request)
        self.db_session.commit()
        self.db_session.refresh(new_request)

        return new_request

    def get_absent_request_by_id(self, request_id: str) -> Optional[AbsentRequest]:
        return self.db_session.get(AbsentRequest, request_id)

    def get_absent_requests_by_employee(
        self, employee_id: uuid.UUID, status: Optional[AbsentStatus] = None
    ) -> List[AbsentRequest]:
        query = (
            select(AbsentRequest)
            .order_by(AbsentRequest.created_at.desc())
            .where(AbsentRequest.employee_id == employee_id)
        )

        if status:
            query = query.where(AbsentRequest.status == status.value)

        return self.db_session.execute(query).scalars().all()

    def processing_emails(self, emails: list[EmailSchema]):
        for email in emails:
            try:
                if not email.from_email == settings.manager_email:
                    continue

                request = self.get_absent_request_by_id(email.subject)

                if not request:
                    raise LookupError(f"Request not found: {email.subject}")

                gmail.mark_as_read(email.message_id)

                body = email.body.strip()
                [status, security_code] = body.split(" ")

                if not security_code == request.security_code:
                    raise ValueError(f"Invalid security code: {email.subject}")

                if not request.status == AbsentStatus.PENDING:
                    raise ValueError("Invalid request")

                self.update_absent_request_status(request.id, status, email.message_id)

            except Exception as e:
                print(e)
                continue

    def update_absent_request_status(
        self,
        request_id: uuid.UUID,
        status: str,
        decision_message_id: Optional[str] = None,
    ) -> AbsentRequest:
        request = self.get_absent_request_by_id(str(request_id))
        if not request:
            raise LookupError("Request not found")

        request.status = status
        if decision_message_id:
            request.decision_message_id = decision_message_id

        self.db_session.commit()
        self.db_session.refresh(request)

        return request
