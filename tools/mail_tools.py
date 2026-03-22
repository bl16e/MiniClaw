import base64
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_core.tools import tool

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    """Return an authorized Gmail service instance."""
    creds = None
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Missing Gmail credentials file: {credentials_file}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def create_message(to, subject, body_text=None, body_html=None, attachments=None):
    """Create a MIME email payload."""
    message = MIMEMultipart()
    message["to"] = to if isinstance(to, str) else ", ".join(to)
    message["subject"] = subject

    if body_html:
        body = MIMEText(body_html, "html")
    elif body_text:
        body = MIMEText(body_text, "plain")
    else:
        body = MIMEText(" ", "plain")

    message.attach(body)

    if attachments:
        for file_path in attachments:
            with open(file_path, "rb") as file:
                part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                part["Content-Disposition"] = (
                    f'attachment; filename="{os.path.basename(file_path)}"'
                )
                message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


@tool
def send_email(to, subject, body_html=None, body_text=None, attachments=None, user_id="me"):
    """Send an email using the Gmail API."""
    service = get_gmail_service()
    message = create_message(
        to=to,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        attachments=attachments,
    )

    try:
        response = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message Id: {response['id']}")
        return response
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
