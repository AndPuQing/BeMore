import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import emails
from emails.template import JinjaTemplate
from jose import jwt
from mjml import mjml2html

from app.core.config import settings


def _render_template(mjml_template: str) -> str:
    if "<mjml>" in mjml_template:
        # template_name is a MJML template string
        template_str = mjml_template
    else:
        # template_name is a file name
        if not mjml_template.endswith(".mjml"):
            mjml_template = f"{mjml_template}.mjml"

        template_file = Path(settings.EMAIL_TEMPLATES_DIR) / mjml_template
        template_str = template_file.read_text()
    return mjml2html(template_str, disable_comments=True)


def get_recommend_block(**keywords) -> str:
    template_file = Path(settings.EMAIL_TEMPLATES_DIR) / "recommend_block.mjml"
    template_str = template_file.read_text()
    # replace keywords in template
    for key, value in keywords.items():
        template_str = template_str.replace(f"{{{ key }}}", value)
    return template_str


def send_email(
    email_to: str,
    subject_template: str = "",
    mjml_template: str = "",
    environment: dict[str, Any] = {},
) -> None:
    assert (
        settings.EMAILS_ENABLED
    ), "no provided configuration for email variables"
    html_template = _render_template(mjml_template)
    message = emails.Message(
        subject=JinjaTemplate(subject_template),
        html=JinjaTemplate(html_template),
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logging.info(f"send email result: {response}")


def send_test_email(email_to: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    send_email(
        email_to=email_to,
        subject_template=subject,
        mjml_template="test_email",
        environment={"project_name": settings.PROJECT_NAME, "email": email_to},
    )


async def send_reset_password_email(
    email_to: str,
    email: str,
    token: str,
) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    server_host = settings.host + ":" + str(settings.port)
    link = f"{server_host}/reset-password?token={token}"
    send_email(
        email_to=email_to,
        subject_template=subject,
        mjml_template="reset_password",
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )


def send_new_account_email(email_to: str, username: str, password: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    link = settings.host + ":" + str(settings.port)
    send_email(
        email_to=email_to,
        subject_template=subject,
        mjml_template="new_account",
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": link,
        },
    )


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        return decoded_token["email"]
    except jwt.JWTError:
        return None
