"""
Data validation and sanity checking module for Connected Healthcare.
Ensures observation inputs are within valid bounds, non-negative,
and free of schema violations.
"""

from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
import pandas as pd


class ValidationError(ValueError):
    """Raised when user input or data violates sanity rules."""
    pass


def validate_integer(
    value: Any,
    field_name: str,
    min_value: int = 0,
    max_value: Optional[int] = None
) -> int:
    """Validates that a value can be converted to an integer within bounds."""
    if isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a valid whole number (integer).")
    try:
        numeric_value = Decimal(str(value).strip())
        if not numeric_value.is_finite() or numeric_value != numeric_value.to_integral_value():
            raise ValidationError(f"{field_name} must be a valid whole number (integer).")
        int_val = int(numeric_value)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid whole number (integer).")

    if int_val < min_value:
        raise ValidationError(f"{field_name} cannot be less than {min_value}.")

    if max_value is not None and int_val > max_value:
        raise ValidationError(f"{field_name} cannot exceed {max_value}.")

    return int_val


def validate_hospital_id(hospital_id: Any, valid_ids: List[int]) -> int:
    """Validates that hospital_id exists in the database."""
    h_id = validate_integer(hospital_id, "Hospital ID", min_value=1)
    if h_id not in valid_ids:
        raise ValidationError(f"Hospital ID {h_id} does not match any registered hospital.")
    return h_id


def validate_holiday(holiday: Any) -> int:
    """Validates holiday flag (0 for No, 1 for Yes)."""
    h_val = validate_integer(holiday, "Holiday flag", min_value=0, max_value=1)
    return h_val


def sanitize_special_event(event: Optional[str]) -> str:
    """Sanitizes special event string, defaulting to 'None'."""
    if not event or not str(event).strip():
        return "None"
    cleaned = str(event).strip()
    return cleaned[:50]  # Cap length for safety


def validate_observation_payload(
    payload: Dict[str, Any],
    valid_hospital_ids: List[int]
) -> Dict[str, Any]:
    """
    Validates complete observation submission payload before database insertion.
    """
    required_keys = [
        "hospital_id",
        "people_waiting",
        "waiting_minutes",
        "new_patients",
        "discharged_patients",
        "emergency_cases",
        "holiday",
        "special_event",
    ]
    for key in required_keys:
        if key not in payload:
            raise ValidationError(f"Missing required payload field: '{key}'.")

    validated = {
        "hospital_id": validate_hospital_id(payload["hospital_id"], valid_hospital_ids),
        "people_waiting": validate_integer(payload["people_waiting"], "People waiting", min_value=0, max_value=500),
        "waiting_minutes": validate_integer(payload["waiting_minutes"], "Waiting minutes", min_value=0, max_value=720),
        "new_patients": validate_integer(payload["new_patients"], "New patients", min_value=0, max_value=200),
        "discharged_patients": validate_integer(payload["discharged_patients"], "Discharged patients", min_value=0, max_value=200),
        "emergency_cases": validate_integer(payload["emergency_cases"], "Emergency cases", min_value=0, max_value=50),
        "holiday": validate_holiday(payload["holiday"]),
        "special_event": sanitize_special_event(payload.get("special_event")),
    }
    return validated


def check_dataframe_health(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs data quality sanity checks on a dataframe of observations."""
    report = {
        "total_records": len(df),
        "missing_counts": df.isnull().sum().to_dict(),
        "has_missing": df.isnull().sum().sum() > 0,
        "duplicate_timestamps": 0,
        "negative_values": {},
    }
    if "hospital" in df.columns and "recorded_at" in df.columns:
        report["duplicate_timestamps"] = int(df.duplicated(subset=["hospital", "recorded_at"]).sum())

    num_cols = ["people_waiting", "waiting_minutes", "new_patients", "discharged_patients", "emergency_cases"]
    for col in num_cols:
        if col in df.columns:
            report["negative_values"][col] = int((df[col] < 0).sum())

    return report
