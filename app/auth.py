"""
Authentication helpers: login, register, role guards.
Passwords hashed with bcrypt. No Flask/Streamlit imports — pure logic.
"""

import bcrypt
import uuid
from typing import Optional

from app.data.db import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    lock_user,
    init_user_progress,
)


# ─── Auth functions ───────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, pw_hash: str) -> bool:
    """Return True if password matches the bcrypt hash."""
    return bcrypt.checkpw(password.encode(), pw_hash.encode())


def login(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a user by email + password.
    Returns the user dict (without password_hash) or None on failure.
    """
    user = get_user_by_email(email)
    if not user:
        return None
    if not user.get("active", True):
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    # Strip password_hash from return
    return {k: v for k, v in user.items() if k != "password_hash"}


def is_email_allowed(email: str, allowed_list: list[str] | None) -> bool:
    """
    Check if email is in the allowed list.
    allowed_list can come from st.secrets or be hardcoded.
    Returns True if no whitelist is set (open registration).
    """
    if not allowed_list:
        return True  # No whitelist → open registration
    email_lower = email.lower()
    return any(
        allowed.lower() in email_lower or email_lower in allowed.lower()
        for allowed in allowed_list
    )


def register(email: str, name: str, password: str,
             role: str = "user",
             allowed_emails: list[str] | None = None) -> dict:
    """
    Create a new user account.
    Raises ValueError if email already exists or not in allowed list.
    """
    # Check whitelist
    if allowed_emails and not is_email_allowed(email, allowed_emails):
        raise ValueError(
            "Email này chưa được cấp phép đăng ký. "
            "Vui lòng liên hệ quản trị viên."
        )

    existing = get_user_by_email(email)
    if existing:
        raise ValueError(f"Tài khoản với email '{email}' đã tồn tại.")

    pw_hash = hash_password(password)
    user = create_user(email=email, name=name,
                       password_hash=pw_hash, role=role)
    # Seed empty progress row
    init_user_progress(user["id"])
    return user


def lock_account(user_id: str, locked_by: str) -> None:
    """Lock a user account (used by Gate D or expert)."""
    lock_user(user_id, locked_by=locked_by)


# ─── Role guard helpers ─────────────────────────────────────────────────────
# These require Streamlit's st.session_state; call them at the top of pages.

ROLE_HIERARCHY = {"admin": 3, "expert": 2, "user": 1}


def is_at_least(user_role: str, required_role: str) -> bool:
    """Return True if user_role meets or exceeds required_role in hierarchy."""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 999)


def get_user_from_session(session_user: Optional[dict]) -> Optional[dict]:
    """
    Validate that session_user still exists and is active in DB.
    Returns fresh user dict or None if revoked/deleted.
    """
    if not session_user:
        return None
    return get_user_by_id(session_user["id"])
