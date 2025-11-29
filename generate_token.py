#!/usr/bin/env python3
import secrets

def generate_token():
    """Generate a secure random token."""
    return secrets.token_hex(32)

if __name__ == '__main__':
    token = generate_token()
    print(token)
    # print(f"Generated Token: {token}")
    # print("\nAdd this to your .env file:")
    # print(f"AUTH_TOKEN={token}")
    # print("\nOr use it in your requests:")
    # print(f"Authorization: Bearer {token}")
