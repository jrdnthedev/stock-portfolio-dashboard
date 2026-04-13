# JWT Authentication Middleware

This module provides JWT-based authentication for the Stock Portfolio API.

## Features

- **Token Generation**: Create access and refresh tokens
- **Password Hashing**: Secure bcrypt password hashing
- **Token Validation**: Automatic JWT token verification
- **Route Protection**: Dependencies for protecting endpoints
- **Role-Based Access Control**: Support for role-based permissions
- **Middleware Logging**: Optional logging for authentication events

## Installation

The required dependencies are already in `requirements.txt`:
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

## Configuration

Add JWT settings to your `.env` file:

```env
# JWT Authentication
JWT_SECRET_KEY=your-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**⚠️ IMPORTANT**: Change `JWT_SECRET_KEY` in production! Generate a secure key:
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Usage

### 1. Creating Tokens

```python
from middleware.auth import create_access_token, create_refresh_token

# Create access token
access_token = create_access_token(
    data={"sub": "user@example.com", "role": "admin"}
)

# Create refresh token
refresh_token = create_refresh_token(
    data={"sub": "user@example.com"}
)
```

### 2. Password Hashing

```python
from middleware.auth import hash_password, verify_password

# Hash a password
hashed = hash_password("my_secure_password")

# Verify password
is_valid = verify_password("my_secure_password", hashed)
```

### 3. Protecting Routes

#### Basic Authentication
```python
from fastapi import APIRouter, Depends
from middleware.auth import get_current_user

router = APIRouter()

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": f"Hello, {user['sub']}!"}
```

#### Active User Only
```python
from middleware.auth import get_current_active_user

@router.get("/active-only")
async def active_users_only(user: dict = Depends(get_current_active_user)):
    return {"message": f"Active user: {user['sub']}"}
```

#### Role-Based Access Control
```python
from middleware.auth import require_role, require_any_role

# Single role required
@router.get("/admin")
async def admin_only(user: dict = Depends(require_role("admin"))):
    return {"message": "Admin access"}

# Multiple roles allowed
@router.get("/moderator")
async def moderator_or_admin(
    user: dict = Depends(require_any_role(["admin", "moderator"]))
):
    return {"message": "Moderator or admin access"}
```

### 4. Login Endpoint Example

```python
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from middleware.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
)

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # TODO: Fetch user from database
    # user = get_user_by_email(request.email)

    # For demo purposes
    stored_password_hash = "$2b$12$..."  # From database

    # Verify password
    if not verify_password(request.password, stored_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": request.email, "role": "user"}
    )
    refresh_token = create_refresh_token(
        data={"sub": request.email}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
```

### 5. Token Refresh Endpoint

```python
from fastapi import HTTPException, status
from middleware.auth import decode_token, create_access_token, AuthenticationError

@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = decode_token(refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Create new access token
        new_access_token = create_access_token(
            data={"sub": payload["sub"]}
        )

        return {"access_token": new_access_token, "token_type": "bearer"}

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
```

### 6. Adding JWT Middleware (Optional)

Add logging middleware to `main.py`:

```python
from middleware.auth import JWTMiddleware

app = FastAPI()

# Add JWT logging middleware
app.add_middleware(JWTMiddleware)
```

**Note**: This middleware only logs authentication events. You still need to use the authentication dependencies (`get_current_user`, etc.) on your protected routes.

## Client Usage

### Making Authenticated Requests

#### Python (httpx)
```python
import httpx

# Login to get token
response = httpx.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token_data = response.json()
access_token = token_data["access_token"]

# Use token in requests
headers = {"Authorization": f"Bearer {access_token}"}
response = httpx.get(
    "http://localhost:8000/api/v1/protected",
    headers=headers
)
```

#### JavaScript/TypeScript
```typescript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access_token } = await loginResponse.json();

// Use token
const response = await fetch('http://localhost:8000/api/v1/protected', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

#### cURL
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Use token
curl http://localhost:8000/api/v1/protected \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

## Token Payload Structure

### Access Token
```json
{
  "sub": "user@example.com",
  "role": "admin",
  "exp": 1234567890,
  "iat": 1234567800
}
```

### Refresh Token
```json
{
  "sub": "user@example.com",
  "type": "refresh",
  "exp": 1234999999,
  "iat": 1234567800
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions - requires role: admin"
}
```

## Security Best Practices

1. **Always use HTTPS in production** - Tokens should never be transmitted over unencrypted connections
2. **Use strong secret keys** - Minimum 32 characters, randomly generated
3. **Short token expiration** - Access tokens should expire quickly (15-30 minutes)
4. **Store tokens securely** - Use httpOnly cookies or secure storage in clients
5. **Validate all inputs** - Always validate email, password, and user data
6. **Rate limiting** - Implement rate limiting on login endpoints
7. **Token blacklisting** - Consider implementing token revocation for logout
8. **Refresh token rotation** - Issue new refresh tokens on each refresh

## Testing

See `tests/test_auth.py` for comprehensive test examples.

## Integration with Existing Routes

To protect existing portfolio and market routes:

```python
# routes_portfolio.py
from middleware.auth import get_current_active_user

@router.get("/portfolio", dependencies=[Depends(get_current_active_user)])
async def list_portfolios(db: Session = Depends(get_db)):
    # Only authenticated users can access
    pass

# Or with user context
@router.post("/portfolio")
async def create_portfolio(
    data: PortfolioCreate,
    user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Use user['sub'] to associate portfolio with user
    pass
```

## Next Steps

1. **Install dependencies**: `pip install python-jose[cryptography] passlib[bcrypt]`
2. **Set JWT_SECRET_KEY**: Update `.env` file with a secure key
3. **Create user model**: Add User model to database
4. **Implement login/register**: Create auth routes
5. **Protect routes**: Add auth dependencies to sensitive endpoints
6. **Frontend integration**: Update Angular app to handle tokens
