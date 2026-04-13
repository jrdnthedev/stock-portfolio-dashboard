"""JWT authentication middleware and utilities for API security.

This module provides JWT-based authentication with token generation, validation,
and route protection capabilities.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from backend.config import settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for extracting tokens from Authorization header
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password (UTF-8 decoded string)

    Note:
        bcrypt has a 72-byte limit. The password is automatically truncated
        at the byte level before hashing.
    """
    # Convert password to bytes and truncate to 72 bytes if needed
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as UTF-8 string for database storage
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against (UTF-8 string)

    Returns:
        bool: True if password matches, False otherwise

    Note:
        bcrypt has a 72-byte limit. The password is automatically truncated
        at the byte level before verification.
    """
    # Convert password to bytes and truncate to 72 bytes if needed
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Convert hashed password back to bytes for bcrypt
    hashed_bytes = hashed_password.encode("utf-8")

    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        # Invalid hash format
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time delta

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "user@example.com", "role": "admin"})
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})

    # Encode JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time delta

    Returns:
        str: Encoded JWT refresh token

    Example:
        >>> token = create_refresh_token({"sub": "user@example.com"})
    """
    to_encode = data.copy()

    # Set expiration time (longer for refresh tokens)
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",  # Mark as refresh token
        }
    )

    # Encode JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        dict[str, Any]: Decoded token payload

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise AuthenticationError(f"Invalid or expired token: {e}") from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """
    Extract and validate the current user from JWT token.

    This dependency can be used to protect routes requiring authentication.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        dict[str, Any]: User information from token payload

    Raises:
        HTTPException: If authentication fails

    Example:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['sub']}"}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)

        # Validate token type (ensure it's not a refresh token)
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type - refresh token cannot be used for authentication",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract user identifier
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload - missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_active_user(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Validate that the current user is active.

    Args:
        current_user: User data from get_current_user dependency

    Returns:
        dict[str, Any]: Active user information

    Raises:
        HTTPException: If user is inactive

    Example:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_active_user)):
            return {"message": f"Hello active user {user['sub']}"}
    """
    # Check if user is disabled (if 'disabled' field exists)
    if current_user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return current_user


def require_role(required_role: str) -> Any:
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Role required to access the route

    Returns:
        Dependency function that validates user role

    Example:
        @app.get("/admin")
        async def admin_route(user: dict = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}
    """

    async def role_checker(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        user_role = current_user.get("role")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions - requires role: {required_role}",
            )
        return current_user

    return role_checker


def require_any_role(required_roles: list[str]) -> Any:
    """
    Dependency factory for multi-role access control.

    Args:
        required_roles: List of roles that can access the route

    Returns:
        Dependency function that validates user has any of the required roles

    Example:
        @app.get("/moderator")
        async def mod_route(user: dict = Depends(require_any_role(["admin", "moderator"]))):
            return {"message": "Access granted"}
    """

    async def role_checker(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions - requires one of: {', '.join(required_roles)}",
            )
        return current_user

    return role_checker


class JWTMiddleware:
    """
    Optional middleware for logging JWT authentication events.

    This middleware is optional and provides centralized logging for authentication
    events. It doesn't replace the need for using authentication dependencies
    on protected routes.
    """

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """
        Process request and log authentication status.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive channel
            send: ASGI send channel
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create Request object to access headers
        request = Request(scope, receive=receive)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = decode_token(token)
                logger.debug(
                    f"JWT authentication: user={payload.get('sub')}, path={request.url.path}"
                )
            except AuthenticationError:
                logger.debug(f"Invalid JWT token attempted on path={request.url.path}")

        await self.app(scope, receive, send)
