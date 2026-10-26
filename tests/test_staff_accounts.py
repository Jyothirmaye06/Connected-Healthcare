import pytest

from src.authentication import AuthenticatedUser
from src.staff_accounts import (
    create_staff_account,
    set_staff_account_status,
    authenticate_staff_account,
)

ADMIN = AuthenticatedUser("admin", "admin", ())
STAFF_PASSWORD = "TestStaffPassword123!"


def test_admin_can_create_pending_staff_account(temp_db_path):
    create_staff_account(
        "staff_one", STAFF_PASSWORD, 1, ADMIN, db_path=temp_db_path
    )
    assert authenticate_staff_account(
        "staff_one", STAFF_PASSWORD, db_path=temp_db_path
    ) is None


def test_non_admin_cannot_create_staff_account(temp_db_path):
    staff = AuthenticatedUser("staff_one", "staff", (1,))

    with pytest.raises(PermissionError):
        create_staff_account(
            "another_staff", STAFF_PASSWORD, 1, staff, db_path=temp_db_path
        )


def test_admin_can_activate_and_suspend_account(temp_db_path):
    create_staff_account(
        "staff_one", STAFF_PASSWORD, 1, ADMIN, db_path=temp_db_path
    )

    set_staff_account_status(
        "staff_one", "active", ADMIN, db_path=temp_db_path
    )

    user = authenticate_staff_account(
        "staff_one", STAFF_PASSWORD, db_path=temp_db_path
    )
    assert user is not None
    assert user.role == "staff"
    assert user.hospital_ids == (1,)

    set_staff_account_status(
        "staff_one", "suspended", ADMIN, db_path=temp_db_path
    )

    assert authenticate_staff_account(
        "staff_one", STAFF_PASSWORD, db_path=temp_db_path
    ) is None


def test_wrong_password_is_rejected(temp_db_path):
    create_staff_account(
        "staff_one", STAFF_PASSWORD, 1, ADMIN, db_path=temp_db_path
    )
    set_staff_account_status(
        "staff_one", "active", ADMIN, db_path=temp_db_path
    )

    assert authenticate_staff_account(
        "staff_one", "WrongPassword123!", db_path=temp_db_path
    ) is None


def test_duplicate_username_is_rejected(temp_db_path):
    create_staff_account(
        "staff_one", STAFF_PASSWORD, 1, ADMIN, db_path=temp_db_path
    )

    with pytest.raises(ValueError, match="already exists"):
        create_staff_account(
            "STAFF_ONE", STAFF_PASSWORD, 1, ADMIN, db_path=temp_db_path
        )


def test_invalid_hospital_is_rejected(temp_db_path):
    with pytest.raises(ValueError, match="does not exist"):
        create_staff_account(
            "staff_one", STAFF_PASSWORD, 999, ADMIN, db_path=temp_db_path
        )
