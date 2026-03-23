#!/usr/bin/env python3
"""
Set or reset the BotPanel admin password.

Usage:
  Interactive:   python3 set_password.py
  Non-interactive: BOTPANEL_PASSWORD=mysecret python3 set_password.py
"""

import os, sys, getpass

# Allow running from the install directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.auth import save_credentials

USERNAME = "admin"


def main():
    password = os.environ.get("BOTPANEL_PASSWORD", "").strip()

    if not password:
        # Interactive mode
        if not sys.stdin.isatty():
            print("ERROR: No password provided. Set BOTPANEL_PASSWORD env var for non-interactive use.", file=sys.stderr)
            sys.exit(1)
        password = getpass.getpass("Enter new admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("ERROR: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 4:
        print("ERROR: Password must be at least 4 characters.", file=sys.stderr)
        sys.exit(1)

    save_credentials(USERNAME, password)
    print(f"Password set for user '{USERNAME}'.")


if __name__ == "__main__":
    main()
