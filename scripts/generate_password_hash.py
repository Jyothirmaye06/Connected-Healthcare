"""Interactively generate a PBKDF2 password salt/hash for Streamlit secrets."""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.authentication import create_password_hash


def main() -> None:
    password = getpass.getpass("New account password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    salt, password_hash = create_password_hash(password)
    print("\nAdd these values to the matching user section in .streamlit/secrets.toml:")
    print(f'password_salt = "{salt}"')
    print(f'password_hash = "{password_hash}"')


if __name__ == "__main__":
    main()
