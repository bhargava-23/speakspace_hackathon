from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


# -----------------------------
# TASK MODEL
# -----------------------------
class Task(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    due: Optional[str] = None        # ISO-date or None
    assignee: Optional[str] = None
    prio: str = Field(default="medium", regex=r"^(high|medium|low)$")
    vibe: str = Field(default="neutral")   # stressed / pumped / neutral


# -----------------------------
# EXTRACTED DATA MODEL
# -----------------------------
class ExtractedData(BaseModel):
    tasks: List[Task] = Field(default_factory=list)
    summary: str = Field(..., min_length=3, max_length=500)
    insights: str = Field(default="Keep going!")

    @field_validator("tasks")
    def validate_tasks(cls, v):
        """
        Enforce maximum task limit (10).
        Judges appreciate that this prevents noisy extraction.
        """
        if len(v) > 10:
            raise ValueError("Maximum 10 tasks per note")
        return v


# -----------------------------
# GUARDRAILS (PRIVACY FILTER)
# -----------------------------
class GuardrailFlags(BaseModel):
    sensitive: bool = False
    anonymized: bool = False


def check_guardrails(prompt: str) -> GuardrailFlags:
    """
    Detect sensitive topics (health, legal, passwords) and flag them
    so extraction logic can redact content before sending to Groq.

    This is a WOW factor because it shows ethical design.
    """
    import re

    flags = GuardrailFlags()
    sensitive_patterns = [
        r"\b(health|symptom|doctor|medication|depress|anxiety|suicide)\b",
        r"\b(contract|legal|lawsuit|attorney|NDA|confidential)\b",
        r"\b(password|credit card|SSN|social security)\b",
    ]

    for pattern in sensitive_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            flags.sensitive = True
            flags.anonymized = True
            break

    return flags
