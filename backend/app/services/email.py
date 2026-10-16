import re
import uuid

COMMAND_PATTERN = re.compile(r"\b(APPROVE|REJECT)\s+([A-Z0-9]{6})\b", re.IGNORECASE)


def parse_decision(text: str) -> tuple[str, uuid.UUID, str] | None:
    """
    Parse decision from email text. Only checks the first non-empty line of the
    message body (after subject) to avoid matching commands in quoted original email.
    Also extracts security_code from the email body.
    """
    # Split into lines, skip subject line (first line), find first non-empty body line
    lines = text.splitlines()
    if len(lines) < 2:
        return None

    # Get the first non-empty line after subject (the actual reply content)
    for line in lines[1:]:
        line = line.strip()
        if line:
            match = COMMAND_PATTERN.search(line)
            if match:
                decision = match.group(1).lower()
                security_code = match.group(2)
                subject_line = lines[0] if len(lines) > 0 else ""
                request_id_match = re.search(r"[a-f0-9-]{36}", subject_line)
                if request_id_match:
                    request_id = request_id_match.group(0)
                    return decision, uuid.UUID(request_id), security_code
            break  # Only check the first non-empty line
    return None
