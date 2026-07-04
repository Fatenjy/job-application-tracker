import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import settings
from app.models.job import Job

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"
MAX_JOBS_PER_MESSAGE = 15


def job_matches_keywords(job: Job, keywords: list[str]) -> bool:
    """A job matches if any keyword appears in its title or tags."""
    haystack = job.title.lower() + " " + " ".join(job.tags or []).lower()
    return any(keyword in haystack for keyword in keywords)


def send_email(subject: str, text_body: str, html_body: str) -> bool:
    """Send one email via SMTP (STARTTLS). Returns True on success."""
    if not (settings.smtp_host and settings.smtp_user and settings.notify_email_to):
        return False
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_user
    message["To"] = settings.notify_email_to
    message.set_content(text_body)
    # Mail clients render the HTML part; the plain-text part is the fallback.
    message.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        return True
    except Exception:
        logger.exception("email notification failed")
        return False


def send_telegram(text: str) -> bool:
    """Send one Telegram message. Returns True on success."""
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        return False
    response = httpx.post(
        f"{TELEGRAM_API}/bot{settings.telegram_bot_token}/sendMessage",
        json={
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    if response.status_code != 200:
        logger.error("telegram send failed: %s %s", response.status_code, response.text)
        return False
    return True


def notify_new_jobs(jobs: list[Job]) -> int:
    """Notify about new jobs matching the configured keywords, through every
    configured channel (email and/or Telegram). Returns matched-job count."""
    keywords = settings.keywords_list
    if not keywords:
        return 0
    matching = [job for job in jobs if job_matches_keywords(job, keywords)]
    if not matching:
        return 0
    shown = matching[:MAX_JOBS_PER_MESSAGE]
    extra = len(matching) - len(shown)

    subject = f"{len(matching)} nouvelle(s) offre(s) d'emploi pour toi"

    text_lines = [subject, ""]
    html_lines = [f"<h3>{subject}</h3><ul>"]
    for job in shown:
        location = f" — {job.location}" if job.location else ""
        text_lines.append(f"- {job.title} | {job.company}{location}\n  {job.url}")
        html_lines.append(
            f'<li><a href="{job.url}">{job.title}</a> — {job.company}{location}</li>'
        )
    html_lines.append("</ul>")
    if extra > 0:
        text_lines.append(f"... et {extra} de plus dans l'API.")
        html_lines.append(f"<p>... et {extra} de plus dans l'API.</p>")

    sent_email = send_email(subject, "\n".join(text_lines), "".join(html_lines))
    sent_telegram = send_telegram("\n".join(text_lines))
    if not (sent_email or sent_telegram):
        logger.info("no notification channel configured or all failed")
        return 0
    return len(matching)
