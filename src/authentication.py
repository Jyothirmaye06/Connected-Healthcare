"""Fail-closed authentication helpers for local Streamlit deployments."""

from dataclasses import dataclass
import hashlib
import hmac
import secrets
from typing import Any, Mapping, Optional, Tuple

PBKDF2_ITERATIONS = 600_000
ALLOWED_ROLES = {"staff", "admin"}


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    role: str
    hospital_ids: Tuple[int, ...]


def create_password_hash(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """Returns a random salt and PBKDF2-HMAC-SHA256 password hash as hex strings."""
    if len(password) < 12:
        raise ValueError("Passwords must contain at least 12 characters.")
    password_salt = salt or secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt,
        PBKDF2_ITERATIONS,
    )
    return password_salt.hex(), password_hash.hex()


def _configured_user(username: str, users: Mapping[str, Any]) -> Optional[AuthenticatedUser]:
    raw_user = users.get(username)
    if not isinstance(raw_user, Mapping):
        return None
    try:
        configured_salt = bytes.fromhex(raw_user["password_salt"])
        configured_hash = bytes.fromhex(raw_user["password_hash"])
    except (KeyError, TypeError, ValueError):
        return None
    if len(configured_salt) < 16 or len(configured_hash) != hashlib.sha256().digest_size:
        return None
    role = raw_user.get("role")
    if role not in ALLOWED_ROLES:
        return None
    raw_hospital_ids = raw_user.get("hospital_ids", [])
    if not isinstance(raw_hospital_ids, (list, tuple)):
        return None
    try:
        if any(isinstance(value, bool) or not isinstance(value, int) for value in raw_hospital_ids):
            return None
        hospital_ids = tuple(sorted(set(raw_hospital_ids)))
    except (TypeError, ValueError):
        return None
    if any(hospital_id <= 0 for hospital_id in hospital_ids):
        return None
    return AuthenticatedUser(username, role, hospital_ids)


def authenticate(
    username: str,
    password: str,
    users: Mapping[str, Any],
) -> Optional[AuthenticatedUser]:
    """Authenticates against configured salted PBKDF2 password hashes."""
    user = _configured_user(username, users)
    if user is None:
        return None
    record = users[username]
    try:
        salt = bytes.fromhex(record["password_salt"])
        expected_hash = bytes.fromhex(record["password_hash"])
    except (KeyError, TypeError, ValueError):
        return None
    if len(salt) < 16 or len(expected_hash) != hashlib.sha256().digest_size:
        return None
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    if not hmac.compare_digest(actual_hash, expected_hash):
        return None
    return user


def resolve_authenticated_user(
    username: Optional[str],
    users: Mapping[str, Any],
) -> Optional[AuthenticatedUser]:
    """Resolves the current session identity from server-configured account data."""
    if not username:
        return None
    return _configured_user(username, users)


def user_can_access_hospital(user: AuthenticatedUser, hospital_id: int) -> bool:
    """Administrators may access all facilities; staff are scoped to configured IDs."""
    return user.role == "admin" or (
        user.role == "staff" and hospital_id in user.hospital_ids
    )


def user_has_role(user: Optional[AuthenticatedUser], required_role: str) -> bool:
    """Checks a role requirement without trusting UI visibility as authorization."""
    if user is None:
        return False
    if required_role == "staff":
        return user.role in {"staff", "admin"}
    return user.role == required_role
