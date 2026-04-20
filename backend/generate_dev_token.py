"""Generate a development JWT token for testing the frontend.

This script creates a valid JWT token using the same secret key
and algorithm as the backend authentication system.

Usage:
    python generate_dev_token.py

The generated token will be printed to the console and can be used
in the Angular frontend for development/testing.
"""

from datetime import UTC, datetime, timedelta

import jwt

from backend.config import settings


def generate_dev_token(user_id: str = "test-user", expires_days: int = 30) -> str:
    """
    Generate a JWT token for development/testing.

    Args:
        user_id: User identifier to include in token (default: "test-user")
        expires_days: Number of days until token expires (default: 30)

    Returns:
        str: Encoded JWT token
    """
    # Create token payload
    payload = {
        "sub": user_id,  # Subject (user identifier)
        "exp": datetime.now(UTC) + timedelta(days=expires_days),  # Expiration
        "iat": datetime.now(UTC),  # Issued at
        "type": "access",  # Token type
    }

    # Encode the token using the same secret key and algorithm as the backend
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


if __name__ == "__main__":
    print("Generating development JWT token...")
    print(f"Secret Key: {settings.jwt_secret_key[:20]}... (truncated)")
    print(f"Algorithm: {settings.jwt_algorithm}")
    print()

    # Generate token valid for 30 days
    token = generate_dev_token(user_id="dev-user", expires_days=30)

    print("Generated Token:")
    print("=" * 80)
    print(token)
    print("=" * 80)
    print()
    print("Copy this token to your Angular environment.ts file:")
    print(f"  mockToken: '{token}'")
    print()
    print("Or set it manually in the browser console:")
    print(f"  localStorage.setItem('jwt_token', '{token}')")
