#!/usr/bin/env python3
"""
Set or reset the BotPanel admin password.

Generates a bcrypt hash suitable for the .env file.

Usage:
  Interactive:      python3 set_password.py
  Non-interactive:  BOTPANEL_PASSWORD=mysecret python3 set_password.py
"""

import os
import sys
import getpass
import secrets

from passlib.hash import bcrypt


def main():
    password = os.environ.get("BOTPANEL_PASSWORD", "").strip()

    if not password:
        if not sys.stdin.isatty():
            print("ERROR: No password provided. Set BOTPANEL_PASSWORD env var.", file=sys.stderr)
            sys.exit(1)
        password = getpass.getpass("Enter new admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("ERROR: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 4:
        print("ERROR: Password must be at least 4 characters.", file=sys.stderr)
        sys.exit(1)

    pw_hash = bcrypt.hash(password)
    secret_key = secrets.token_hex(32)

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    # Read existing .env or start fresh
    lines = []
    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Update or add keys
    keys_to_set = {
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD_HASH": pw_hash,
        "SECRET_KEY": secret_key,
    }
    existing_keys = set()
    new_lines = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in keys_to_set:
            new_lines.append(f"{key}={keys_to_set[key]}\n")
            existing_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in keys_to_set.items():
        if key not in existing_keys:
            new_lines.append(f"{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    os.chmod(env_path, 0o600)

    print(f"Password set for user 'admin'.")
    print(f".env updated at {env_path}")
    print(f"ADMIN_PASSWORD_HASH={pw_hash}")


if __name__ == "__main__":
    main()
