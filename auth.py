"""
EduOS AI — Authentication & RBAC Library
==========================================
Pure utility module. No Streamlit, no database calls, no side effects.
Designed to be imported by both the Streamlit app and (later) FastAPI.

Responsibilities:
  - Password hashing and verification (bcrypt)
  - JWT access token issuance and verification
  - Role-Based Access Control (RBAC) permission table
  - Data-scoping helpers (filter records to what a role may see)

Roles:
  admin   — full access to all school data and operations
  teacher — attendance, timetable, assigned students, relevant alerts/analytics
  student — own record only (attendance, GPA, fee status, timetable)
  parent  — linked child's record only (attendance, fee, timetable, alerts)

JWT payload shape:
  {
    "sub":        str   — user_id (primary key in users table)
    "role":       str   — admin | teacher | student | parent
    "linked_id":  str | None — student_id for student/parent; teacher_id for teacher
    "exp":        int   — Unix timestamp expiry
    "iat":        int   — Unix timestamp issued-at
  }
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import jwt
from dotenv import load_dotenv

from env_config import get_missing_vars

load_dotenv()

logger = logging.getLogger("EduOS_Auth")
logger.setLevel(logging.INFO)

# ── Configuration ─────────────────────────────────────────────────────────────

_JWT_SECRET: str = os.getenv("JWT_SECRET_KEY", "").strip()
_JWT_ALGORITHM: str = "HS256"
_TOKEN_EXPIRY_HOURS: int = 8  # session length

if not _JWT_SECRET:
    logger.warning(
        "JWT_SECRET_KEY is not set in .env. "
        "Authentication will not work. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )


def is_auth_configured() -> bool:
    """Returns True when JWT_SECRET_KEY is set (required for login)."""
    return bool(_JWT_SECRET)


def get_auth_config_errors() -> list:
    """Returns a list of missing auth-related env var names (no secret values)."""
    return get_missing_vars(for_auth=True)

# ── Custom exceptions ─────────────────────────────────────────────────────────

class AuthError(Exception):
    """Raised for authentication failures (wrong password, missing user)."""

class TokenError(Exception):
    """Raised for JWT validation failures (expired, tampered, missing)."""

class PermissionError(Exception):
    """Raised when a role attempts an operation it is not permitted to perform."""


# ── Password utilities ────────────────────────────────────────────────────────

def hash_password(plaintext: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a random salt.
    Returns the hash as a UTF-8 string suitable for database storage.
    Never stores or logs the plaintext password.
    """
    if not plaintext:
        raise ValueError("Password must not be empty.")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plaintext.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    Returns True if they match, False otherwise.
    Constant-time comparison — safe against timing attacks.
    """
    if not plaintext or not hashed:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT utilities ─────────────────────────────────────────────────────────────

def issue_token(user_id: str, role: str, linked_id: Optional[str] = None) -> str:
    """
    Issues a signed JWT access token for the given user.

    Args:
        user_id:   Primary key from the users table.
        role:      One of: admin, teacher, student, parent.
        linked_id: student_id (for student/parent) or teacher_id (for teacher).

    Returns:
        Signed JWT string.

    Raises:
        ValueError if JWT_SECRET_KEY is not configured.
    """
    if not _JWT_SECRET:
        raise ValueError("JWT_SECRET_KEY is not configured. Cannot issue tokens.")

    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub":       user_id,
        "role":      role,
        "linked_id": linked_id,
        "iat":       int(now.timestamp()),
        "exp":       int((now + timedelta(hours=_TOKEN_EXPIRY_HOURS)).timestamp()),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifies and decodes a JWT access token.

    Returns:
        Decoded payload dict with keys: sub, role, linked_id, iat, exp.

    Raises:
        TokenError on expiry, invalid signature, or malformed token.
    """
    if not _JWT_SECRET:
        raise TokenError("JWT_SECRET_KEY is not configured.")
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenError("Session has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise TokenError(f"Invalid token: {e}")


# ── RBAC permission table ─────────────────────────────────────────────────────
#
# Each entry: permission_key -> set of roles that hold it.
# Use require_permission() to enforce at the call site.
#
# Naming convention: <resource>:<action>
#   resource = students | teachers | timetable | documents | alerts | analytics | copilot
#   action   = read_all | read_own | write | manage

_PERMISSIONS: Dict[str, set] = {
    # ── Students ──────────────────────────────────────────────
    "students:read_all":        {"admin", "teacher"},
    "students:read_own":        {"student", "parent"},
    "students:write":           {"admin"},

    # ── Teachers ──────────────────────────────────────────────
    "teachers:read_all":        {"admin"},
    "teachers:read_own":        {"teacher"},
    "teachers:write":           {"admin"},

    # ── Timetable ─────────────────────────────────────────────
    "timetable:read_all":       {"admin", "teacher"},
    "timetable:read_own":       {"student", "parent"},
    "timetable:write":          {"admin"},

    # ── Documents ─────────────────────────────────────────────
    "documents:read_all":       {"admin"},
    "documents:write":          {"admin"},

    # ── Alerts ────────────────────────────────────────────────
    "alerts:read_all":          {"admin"},
    "alerts:read_own":          {"teacher", "student", "parent"},
    "alerts:write":             {"admin", "teacher"},

    # ── Analytics / Insights ──────────────────────────────────
    "analytics:read_all":       {"admin"},
    "analytics:read_summary":   {"teacher"},

    # ── Staffing ──────────────────────────────────────────────
    "staffing:read":            {"admin"},

    # ── AI Copilot ────────────────────────────────────────────
    "copilot:use":              {"admin", "teacher"},

    # ── Attendance write ──────────────────────────────────────
    "attendance:write":         {"admin", "teacher"},

    # ── Fee write ─────────────────────────────────────────────
    "fee:write":                {"admin", "parent"},
}


def has_permission(role: str, permission: str) -> bool:
    """Returns True if the given role holds the specified permission."""
    return role in _PERMISSIONS.get(permission, set())


def require_permission(role: str, permission: str) -> None:
    """
    Raises PermissionError if the role does not hold the permission.
    Use this as a guard at the start of any protected operation.
    """
    if not has_permission(role, permission):
        raise PermissionError(
            f"Role '{role}' does not have permission '{permission}'."
        )


def get_role_permissions(role: str) -> List[str]:
    """Returns all permissions held by a given role (for display/audit)."""
    return sorted(perm for perm, roles in _PERMISSIONS.items() if role in roles)


# ── Data-scoping helpers ──────────────────────────────────────────────────────
# These filter raw DB lists to only what the authenticated user may see.
# They are the enforcement point for "no student can see another student's data".

def scope_students(
    students: List[Dict[str, Any]],
    role: str,
    linked_id: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Returns the subset of student records the role is allowed to see.

    - admin / teacher : all records
    - student         : only the record whose id == linked_id
    - parent          : only the record whose id == linked_id (their child)
    """
    if role in ("admin", "teacher"):
        return students
    if role in ("student", "parent") and linked_id:
        return [s for s in students if s.get("id") == linked_id]
    return []


def scope_alerts(
    alerts: List[Dict[str, Any]],
    role: str,
    linked_id: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Returns the subset of alerts the role is allowed to see.

    - admin   : all alerts
    - teacher : alerts not tied to a specific student (timetable, staffing)
    - student / parent : only alerts where student_id == linked_id
    """
    if role == "admin":
        return alerts
    if role == "teacher":
        return [a for a in alerts if not a.get("student_id")]
    if role in ("student", "parent") and linked_id:
        return [a for a in alerts if a.get("student_id") == linked_id]
    return []


def scope_timetable(
    timetable: List[Dict[str, Any]],
    role: str,
    linked_id: Optional[str],
    students: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Returns the timetable slots the role is allowed to see.

    - admin / teacher : full timetable
    - student / parent: slots for the student's class only
    """
    if role in ("admin", "teacher"):
        return timetable
    if role in ("student", "parent") and linked_id:
        student = next((s for s in students if s.get("id") == linked_id), None)
        if student:
            student_class = student.get("class", "")
            return [t for t in timetable if t.get("class_name") == student_class]
    return timetable  # fallback: show all if class unknown


# ── Role display helpers ──────────────────────────────────────────────────────

ROLE_LABELS: Dict[str, str] = {
    "admin":   "School Administrator",
    "teacher": "Teacher",
    "student": "Student",
    "parent":  "Parent",
}

ROLE_ICONS: Dict[str, str] = {
    "admin":   "🏫",
    "teacher": "👩‍🏫",
    "student": "🎓",
    "parent":  "👨‍👩‍👧",
}
