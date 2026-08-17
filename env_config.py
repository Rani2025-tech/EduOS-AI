"""
EduOS AI — Environment Configuration Validation
================================================
Central helper for detecting missing or invalid environment variables.
Never logs or returns secret values — only whether each variable is set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class EnvVarSpec:
    name: str
    required_for_db: bool = False
    required_for_auth: bool = False
    required_for_ai: bool = False
    hint: str = ""


ENV_SPECS: List[EnvVarSpec] = [
    EnvVarSpec(
        name="SUPABASE_URL",
        required_for_db=True,
        hint="Supabase Dashboard → Settings → API → Project URL",
    ),
    EnvVarSpec(
        name="SUPABASE_KEY",
        required_for_db=True,
        hint="Supabase anon/public key (SUPABASE_ANON_KEY is also accepted)",
    ),
    EnvVarSpec(
        name="JWT_SECRET_KEY",
        required_for_auth=True,
        hint='Generate: python -c "import secrets; print(secrets.token_hex(32))"',
    ),
    EnvVarSpec(
        name="GROQ_API_KEY",
        required_for_ai=True,
        hint="https://console.groq.com → API Keys",
    ),
]


def _is_set(name: str) -> bool:
    if name == "SUPABASE_KEY":
        return bool(
            os.getenv("SUPABASE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
    return bool(os.getenv(name, "").strip())


def get_missing_vars(*, for_db: bool = False, for_auth: bool = False, for_ai: bool = False) -> List[str]:
    """Returns names of unset variables for the requested capability group."""
    missing: List[str] = []
    for spec in ENV_SPECS:
        if for_db and spec.required_for_db and not _is_set(spec.name):
            missing.append(spec.name)
        if for_auth and spec.required_for_auth and not _is_set(spec.name):
            missing.append(spec.name)
        if for_ai and spec.required_for_ai and not _is_set(spec.name):
            missing.append(spec.name)
    return missing


def get_env_report() -> Dict[str, Dict[str, object]]:
    """
    Returns a safe status report for each tracked variable.
    Values are never included — only ``set: True/False``.
    """
    report: Dict[str, Dict[str, object]] = {}
    for spec in ENV_SPECS:
        report[spec.name] = {
            "set": _is_set(spec.name),
            "required_for_db": spec.required_for_db,
            "required_for_auth": spec.required_for_auth,
            "required_for_ai": spec.required_for_ai,
            "hint": spec.hint,
        }
    return report


def format_env_summary() -> str:
    """Human-readable summary safe to print (no secret values)."""
    lines: List[str] = []
    for spec in ENV_SPECS:
        status = "set" if _is_set(spec.name) else "MISSING"
        flags: List[str] = []
        if spec.required_for_db:
            flags.append("db")
        if spec.required_for_auth:
            flags.append("auth")
        if spec.required_for_ai:
            flags.append("ai")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f"  {spec.name}: {status}{flag_str}")
    return "\n".join(lines)


def validate_supabase_url(url: str) -> Optional[str]:
    """Returns an error message if the URL format looks wrong, else None."""
    if not url:
        return "SUPABASE_URL is not set."
    if not url.startswith("https://"):
        return "SUPABASE_URL must start with https://"
    if "supabase.co" not in url and "localhost" not in url:
        return "SUPABASE_URL does not look like a Supabase project URL."
    if "<project-ref>" in url:
        return "SUPABASE_URL still contains the placeholder <project-ref>."
    return None
