from datetime import datetime, timedelta

import pytest

from src.authentication import (
    authenticate,
    create_password_hash,
    resolve_authenticated_user,
    user_can_access_hospital,
)
from src.data_access import get_connection
from src.data_validation import ValidationError, validate_integer
from src.staff_portal import (
    AuthorizationError,
    get_observation_audit,
    submit_staff_observation,
)


def make_user(username, role, hospital_ids=()):
    salt, password_hash = create_password_hash("correct-horse-battery-staple")
    return {
        "role": role,
        "hospital_ids": list(hospital_ids),
        "password_salt": salt,
        "password_hash": password_hash,
    }


def observation_payload(hospital_id=1):
    return {
        "hospital_id": hospital_id,
        "people_waiting": 25,
        "waiting_minutes": 40,
        "new_patients": 5,
        "discharged_patients": 3,
        "emergency_cases": 1,
        "holiday": 0,
        "special_event": "",
        "recorded_at": datetime.now() - timedelta(minutes=1),
    }


def test_password_hash_authenticates_without_plaintext():
    users = {"staffer": make_user("staffer", "staff", [1])}

    authenticated = authenticate("staffer", "correct-horse-battery-staple", users)

    assert authenticated is not None
    assert authenticated.role == "staff"
    assert authenticate("staffer", "wrong-password", users) is None
    assert "correct-horse-battery-staple" not in str(users)


def test_bad_account_configuration_fails_closed():
    assert resolve_authenticated_user("admin", {"admin": {"role": "admin"}}) is None
    malformed_scope = {
        "admin": {
            **make_user("admin", "admin", [1]),
            "hospital_ids": [1.5],
        }
    }
    assert resolve_authenticated_user("admin", malformed_scope) is None


def test_staff_hospital_scope_is_enforced_before_write(temp_db_path):
    staff_user = authenticate("staffer", "correct-horse-battery-staple", {
        "staffer": make_user("staffer", "staff", [1])
    })
    assert staff_user is not None
    conn = get_connection(temp_db_path)
    try:
        before = conn.execute("SELECT COUNT(*) FROM hospital_crowd").fetchone()[0]
    finally:
        conn.close()

    with pytest.raises(AuthorizationError):
        submit_staff_observation(staff_user, observation_payload(hospital_id=2), temp_db_path)

    conn = get_connection(temp_db_path)
    try:
        after = conn.execute("SELECT COUNT(*) FROM hospital_crowd").fetchone()[0]
        audit_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='observation_audit'"
        ).fetchone()
    finally:
        conn.close()
    assert after == before
    assert audit_exists is None
    assert user_can_access_hospital(staff_user, 1)
    assert not user_can_access_hospital(staff_user, 2)


def test_authorized_submission_and_audit_are_written_atomically(temp_db_path):
    staff_user = authenticate("staffer", "correct-horse-battery-staple", {
        "staffer": make_user("staffer", "staff", [1])
    })
    assert staff_user is not None

    result = submit_staff_observation(staff_user, observation_payload(), temp_db_path)
    audit = get_observation_audit(staff_user, temp_db_path)

    assert result["observation_id"] > 0
    assert result["hospital_id"] == 1
    assert len(audit) == 1
    assert audit.iloc[0]["actor_username"] == "staffer"
    assert audit.iloc[0]["action"] == "insert"


def test_anonymous_cannot_submit_or_read_audit(temp_db_path):
    with pytest.raises(AuthorizationError):
        submit_staff_observation(None, observation_payload(), temp_db_path)
    with pytest.raises(AuthorizationError):
        get_observation_audit(None, temp_db_path)


def test_invalid_and_future_staff_observations_are_rejected(temp_db_path):
    staff_user = authenticate("staffer", "correct-horse-battery-staple", {
        "staffer": make_user("staffer", "staff", [1])
    })
    assert staff_user is not None

    invalid_count = observation_payload()
    invalid_count["people_waiting"] = 501
    with pytest.raises(ValidationError):
        submit_staff_observation(staff_user, invalid_count, temp_db_path)

    future_timestamp = observation_payload()
    future_timestamp["recorded_at"] = datetime.now() + timedelta(days=1)
    with pytest.raises(ValueError, match="cannot be in the future"):
        submit_staff_observation(staff_user, future_timestamp, temp_db_path)

    conn = get_connection(temp_db_path)
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM hospital_crowd"
        ).fetchone()[0] == 15
    finally:
        conn.close()


@pytest.mark.parametrize("invalid", [1.5, float("nan"), float("inf"), True, "2.25"])
def test_validate_integer_rejects_non_integral_or_boolean_values(invalid):
    with pytest.raises(ValidationError):
        validate_integer(invalid, "People waiting")
