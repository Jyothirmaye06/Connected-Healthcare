"""
Unit tests for data validation module.
Verifies rejection of negative numbers, invalid types, and malformed submissions.
"""

import pytest
from src.data_validation import (
    validate_integer,
    validate_hospital_id,
    validate_holiday,
    sanitize_special_event,
    validate_observation_payload,
    ValidationError,
)


def test_validate_integer_success():
    assert validate_integer(10, "Field") == 10
    assert validate_integer("25", "Field") == 25
    assert validate_integer(0, "Field", min_value=0) == 0


def test_validate_integer_negative_raises():
    with pytest.raises(ValidationError, match="cannot be less than 0"):
        validate_integer(-5, "Field", min_value=0)


def test_validate_integer_max_value_exceeded():
    with pytest.raises(ValidationError, match="cannot exceed 100"):
        validate_integer(150, "Field", min_value=0, max_value=100)


def test_validate_integer_invalid_type_raises():
    with pytest.raises(ValidationError, match="must be a valid whole number"):
        validate_integer("abc", "Field")


def test_validate_hospital_id():
    valid_ids = [1, 2, 3]
    assert validate_hospital_id(2, valid_ids) == 2
    with pytest.raises(ValidationError, match="does not match any registered hospital"):
        validate_hospital_id(999, valid_ids)


def test_validate_holiday():
    assert validate_holiday(0) == 0
    assert validate_holiday(1) == 1
    with pytest.raises(ValidationError):
        validate_holiday(2)


def test_sanitize_special_event():
    assert sanitize_special_event(None) == "None"
    assert sanitize_special_event("") == "None"
    assert sanitize_special_event("  Emergency  ") == "Emergency"


def test_validate_observation_payload_valid():
    payload = {
        "hospital_id": 1,
        "people_waiting": 30,
        "waiting_minutes": 45,
        "new_patients": 5,
        "discharged_patients": 4,
        "emergency_cases": 1,
        "holiday": 0,
        "special_event": "None",
    }
    validated = validate_observation_payload(payload, valid_hospital_ids=[1, 2])
    assert validated["people_waiting"] == 30
    assert validated["hospital_id"] == 1


def test_validate_observation_payload_missing_field():
    payload = {
        "hospital_id": 1,
        "people_waiting": 30,
    }
    with pytest.raises(ValidationError, match="Missing required payload field"):
        validate_observation_payload(payload, valid_hospital_ids=[1, 2])
