from __future__ import annotations

import os
import socket
import traceback
from datetime import datetime
from typing import Iterable

import msal
import requests
from dotenv import load_dotenv

GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
REQUEST_TIMEOUT_SECONDS = 30


def require_environment_variable(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set.")
    return value


def parse_recipients(raw_recipients: str) -> list[str]:
    """Convert a comma-separated recipient string into a clean list."""
    recipients = [address.strip() for address in raw_recipients.split(",")]
    recipients = [address for address in recipients if address]

    if not recipients:
        raise RuntimeError("EMAIL_RECIPIENTS does not contain a valid address.")

    return recipients


def get_graph_access_token(
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> str:
    """Acquire an app-only Microsoft Graph access token using MSAL."""
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret,
    )

    token_result = app.acquire_token_for_client(scopes=GRAPH_SCOPE)
    access_token = token_result.get("access_token")

    if not access_token:
        error = token_result.get("error", "unknown_error")
        description = token_result.get(
            "error_description",
            "Microsoft Entra ID did not return an access token.",
        )
        raise RuntimeError(f"Graph authentication failed: {error}: {description}")

    return access_token


def send_graph_email(
    access_token: str,
    sender_email: str,
    recipients: Iterable[str],
    subject: str,
    body: str,
) -> None:
    """Send a plain-text email with Microsoft Graph."""
    endpoint = f"{GRAPH_BASE_URL}/users/{sender_email}/sendMail"

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body,
            },
            "toRecipients": [
                {"emailAddress": {"address": address}}
                for address in recipients
            ],
        },
        "saveToSentItems": True,
    }

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 202:
        raise RuntimeError(
            "Microsoft Graph sendMail failed with status "
            f"{response.status_code}: {response.text}"
        )


def build_message(success: bool, started_at: datetime, details: str) -> tuple[str, str]:
    """Build the subject and body for the notification email."""
    finished_at = datetime.now().astimezone()
    status = "SUCCESS" if success else "FAILED"
    subject_prefix = os.getenv("EMAIL_SUBJECT_PREFIX", "Canvas Quarter Grades")
    subject = f"{subject_prefix} - {status}"

    body = (
        f"Status: {status}\n"
        f"Computer: {socket.gethostname()}\n"
        f"Started: {started_at.isoformat(timespec='seconds')}\n"
        f"Finished: {finished_at.isoformat(timespec='seconds')}\n\n"
        f"{details}"
    )

    return subject, body


def main() -> int:
    """Run Step 5, then email either its success message or stack trace."""
    load_dotenv()
    started_at = datetime.now().astimezone()

    try:
        # Import inside the try block so import-time failures are captured too.
        import Step5CanvasActiveEnrollments

        Step5CanvasActiveEnrollments.main()
        pipeline_succeeded = True
        details = (
            "The Canvas grade passback job completed without an error.\n"
            "The table dbo.canvas_quarter_grades was updated successfully."
        )
    except Exception:
        pipeline_succeeded = False
        details = (
            "The Canvas grade passback job encountered an error.\n\n"
            "Stack trace:\n"
            f"{traceback.format_exc()}"
        )

    try:
        tenant_id = require_environment_variable("AZURE_TENANT_ID")
        client_id = require_environment_variable("AZURE_CLIENT_ID")
        client_secret = require_environment_variable("AZURE_CLIENT_SECRET")
        sender_email = require_environment_variable("GRAPH_SENDER_EMAIL")
        recipients = parse_recipients(
            require_environment_variable("EMAIL_RECIPIENTS")
        )

        subject, body = build_message(
            success=pipeline_succeeded,
            started_at=started_at,
            details=details,
        )

        access_token = get_graph_access_token(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        send_graph_email(
            access_token=access_token,
            sender_email=sender_email,
            recipients=recipients,
            subject=subject,
            body=body,
        )
        print(f"Notification email sent: {subject}")

    except Exception:
        email_error_trace = traceback.format_exc()
        print("The notification email could not be sent.")
        print(email_error_trace)

        if not pipeline_succeeded:
            print("Canvas grade passback job failure:")
            print(details)

        return 2

    return 0 if pipeline_succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
