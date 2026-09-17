import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger("resq_siren.emergency.summary")

GEMINI_MODEL = "gemini-2.5-flash"


def _template_summary(symptom_label: str, severity: str, location: str, notes: str | None, reported_at: datetime) -> str:
    parts = [
        f"Chief complaint: {symptom_label}.",
        f"Severity: {severity}.",
        f"Reported at {location}, {reported_at.strftime('%H:%M')}.",
    ]
    if notes:
        parts.append(f"Caller notes: {notes}")
    return " ".join(parts)


def _prompt(symptom_label: str, severity: str, location: str, notes: str | None, reported_at: datetime) -> str:
    return (
        "Write a 2-3 sentence emergency-department handoff brief for the receiving hospital, "
        "based only on the following caller-reported intake. Be concise and clinical, do not "
        "invent details not given below.\n\n"
        f"Chief complaint category: {symptom_label}\n"
        f"Triage severity: {severity}\n"
        f"Reported location: {location}\n"
        f"Reported at: {reported_at.strftime('%H:%M')}\n"
        f"Caller notes: {notes or 'none provided'}"
    )


async def _gemini_summary(prompt: str) -> str | None:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = await client.aio.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip() if response.text else None


async def generate_patient_summary(
    *, symptom_label: str, severity: str, location: str, notes: str | None, reported_at: datetime
) -> str:
    """Short ER handoff brief from the structured intake. Uses Gemini if
    GEMINI_API_KEY is set; otherwise falls back to a deterministic template —
    so the flow never blocks on a missing or failing credential, same
    resilience pattern as routing/notify. No Anthropic/Claude dependency.
    """
    if settings.gemini_api_key:
        try:
            summary = await _gemini_summary(_prompt(symptom_label, severity, location, notes, reported_at))
            if summary:
                return summary
        except Exception:
            logger.exception("Gemini patient-summary generation failed — falling back to template")
    else:
        logger.info("GEMINI_API_KEY not set — using template patient summary")

    return _template_summary(symptom_label, severity, location, notes, reported_at)
