import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger("resq_siren.notify")


async def send_push(device_token: str, title: str, body: str) -> None:
    if not settings.fcm_server_key:
        logger.warning("FCM_SERVER_KEY not set — skipping push to %s: %s", device_token, title)
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://fcm.googleapis.com/fcm/send",
            headers={"Authorization": f"key={settings.fcm_server_key}"},
            json={"to": device_token, "notification": {"title": title, "body": body}},
        )


async def send_sms(to_number: str, message: str) -> None:
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number):
        logger.warning("TWILIO_* not set — skipping SMS to %s: %s", to_number, message)
        return

    def _send() -> None:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(to=to_number, from_=settings.twilio_from_number, body=message)

    await asyncio.to_thread(_send)


async def send_email(to_address: str, subject: str, body: str) -> None:
    if not (settings.smtp_host and settings.smtp_username and settings.smtp_password and settings.smtp_from):
        logger.warning("SMTP_* not set — skipping email to %s: %s", to_address, subject)
        return

    def _send() -> None:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_address
        msg.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(msg)

    await asyncio.to_thread(_send)
