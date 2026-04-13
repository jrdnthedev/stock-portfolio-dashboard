# JWT Middleware - Quick Start Guide

## Installation Steps

### 1. Install Dependencies

```powershell
cd backend
pip install python-jose[cryptography] passlib[bcrypt]
```

### 2. Generate Secret Key

Generate a secure secret key for JWT signing:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Update .env File

Add JWT configuration to your `.env` file (or create one from `.env.example`):

```env
# JWT Authentication
JWT_SECRET_KEY=your-generated-secret-key-from-step-2
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**⚠️ CRITICAL**: Never commit your actual `JWT_SECRET_KEY` to version control!

### 4. Verify Installation

Run the tests to verify everything is working:

```powershell
pytest tests/test_auth.py -v
```

## What Was Added

### Core Files

1. **`middleware/auth.py`** - JWT authentication middleware and utilities
   - Password hashing with bcrypt
   - Token generation (access & refresh)
   - Token validation
   - Route protection dependencies
   - Role-based access control

2. **`routes_auth_example.py`** - Example auth routes
   - User registration
   - Login with tokens
   - Token refresh
   - Get current user profile
   - Logout

3. **`tests/test_auth.py`** - Comprehensive test suite
   - Password hashing tests
   - Token creation/validation tests
   - Authentication dependency tests
   - Role-based access tests

4. **`docs/README.Auth.md`** - Complete documentation
   - Usage examples
   - API integration guide
   - Security best practices
   - Client-side examples (Python, JavaScript, cURL)

### Updated Files

1. **`config.py`** - Added JWT settings
2. **`requirements.txt`** - Added python-jose and passlib
3. **`.env.example`** - Added JWT environment variables

## Usage Examples

### Protect an Existing Route

```python
# Before
@router.get("/portfolio")
async def list_portfolios(db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).all()
    return portfolios

# After - Require authentication
from middleware.auth import get_current_user

@router.get("/portfolio")
async def list_portfolios(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only authenticated users can access
    # Use user['sub'] (email) to filter by user
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_email == user['sub']
    ).all()
    return portfolios
```

### Require Admin Role

```python
from middleware.auth import require_role

@router.delete("/admin/portfolios/{portfolio_id}")
async def delete_any_portfolio(
    portfolio_id: str,
    user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    # Only admin users can access
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    db.delete(portfolio)
    db.commit()
    return {"message": "Portfolio deleted"}
```

### Test with cURL

```bash
# 1. Login (when you implement the login endpoint)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Response: {"access_token":"eyJ...","refresh_token":"eyJ..."}

# 2. Use token to access protected endpoint
curl http://localhost:8000/api/v1/portfolio \
  -H "Authorization: Bearer eyJ..."
```

## Next Steps

### Option 1: Use Example Routes (Quick Start)

1. Copy `routes_auth_example.py` to `routes_auth.py`
2. Add user table to your database models
3. Update the TODO sections with your database logic
4. Register the router in `main.py`:
   ```python
   from backend.routes_auth import router as auth_router
   app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
   ```

### Option 2: Build Custom Implementation

1. Create your own auth routes based on the example
2. Implement your user model and repository
3. Add password reset, email verification, etc.

### Recommended: Add to Existing Routes

1. **Portfolio Routes**: Protect with `get_current_user`
2. **Market Routes**: Optional auth (public data)
3. **Admin Routes**: Protect with `require_role("admin")`

Example for `routes_portfolio.py`:
```python
from middleware.auth import get_current_active_user

# At the top of the file
router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
    dependencies=[Depends(get_current_active_user)]  # Protect all routes
)

# Or protect individual routes
@router.post("/")
async def create_portfolio(
    data: PortfolioCreate,
    user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # User information available in 'user' dict
    # Associate portfolio with user
    new_portfolio = Portfolio(
        name=data.name,
        user_email=user['sub'],  # Store user email
        ...
    )
```

## Security Checklist

- [ ] Generated secure `JWT_SECRET_KEY` (32+ characters)
- [ ] Updated `.env` file with secret key
- [ ] `.env` is in `.gitignore` (don't commit secrets!)
- [ ] Installed python-jose and passlib
- [ ] Tests passing (`pytest tests/test_auth.py`)
- [ ] Using HTTPS in production
- [ ] Token expiration times are reasonable (30 min access, 7 day refresh)
- [ ] Implemented user database model
- [ ] Protected sensitive routes with auth dependencies

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'jose'
```
**Solution**: Install dependencies
```powershell
pip install python-jose[cryptography] passlib[bcrypt]
```

### Token Validation Fails
- Check `JWT_SECRET_KEY` matches between token creation and validation
- Verify token hasn't expired
- Ensure token type is correct (access vs refresh)

### 401 Unauthorized
- Verify Authorization header format: `Bearer <token>`
- Check token hasn't expired
- Ensure token is valid and not corrupted

## Documentation

See `docs/README.Auth.md` for complete documentation including:
- Detailed API examples
- Client integration guides
- Security best practices
- Error handling
- Advanced usage patterns

## Support

If you have questions or issues:
1. Check `docs/README.Auth.md` for detailed documentation
2. Review `routes_auth_example.py` for implementation examples
3. Run `pytest tests/test_auth.py -v` to verify setup
4. Check middleware/auth.py docstrings for function documentation
