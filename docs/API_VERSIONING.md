# API Versioning

## Summary

API versioning has been successfully implemented for the Stock Portfolio Backend application using URL-based versioning with the `/api/v{number}` pattern.

## Changes Made

### New Files

1. **`backend/api/versioning.py`**
   - Central versioning configuration module
   - Router factory functions for each API version
   - Version compatibility matrix
   - Helper functions for version checking

2. **`backend/middleware/versioning.py`**
   - Middleware for adding version headers to responses
   - Deprecation warning system
   - Version detection from URL paths

3. **`backend/tests/test_versioning.py`**
   - Comprehensive test suite (25 tests, all passing ✅)
   - Tests for versioning module, endpoints, headers, middleware

4. **`backend/docs/README.Versioning.md`**
   - Complete versioning guide
   - Usage examples for Python and TypeScript clients
   - Migration strategies and best practices

### Modified Files

1. **`backend/main.py`**
   - Integrated versioning middleware
   - Using versioned routers (`create_api_v1_router()`)
   - Updated root endpoint to include version information
   - Added version info to app metadata

2. **`backend/routes_portfolio.py`**
   - Changed prefix from `/v1/portfolio` to `/portfolio`
   - Version prefix now handled by versioning module

3. **`backend/routes_market.py`**
   - Changed prefix from `/v1/market` to `/market`
   - Version prefix now handled by versioning module

4. **`backend/api/__init__.py`**
   - Exported versioning functions for easy imports

## API Structure

### Before
```
/v1/portfolio/
/v1/market/prices/AAPL
/ws/portfolio
```

### After
```
/api/v1/portfolio/
/api/v1/market/prices/AAPL
/ws/portfolio
```

## Key Features

✅ **URL-Based Versioning**: `/api/v1`, `/api/v2`, etc.
✅ **Version Headers**: All responses include `X-API-Version` header
✅ **Deprecation Warnings**: Automatic headers when using deprecated versions
✅ **Centralized Configuration**: Single source of truth for version info
✅ **Future-Ready**: Easy to add v2, v3, etc.
✅ **WebSocket Support**: WebSocket routes remain unversioned in URL
✅ **Backward Compatible**: Existing code continues to work
✅ **Well Tested**: 25 versioning tests + all existing tests passing

## Usage Examples

### Making API Requests

```bash
# Old (no longer works)
GET /v1/portfolio

# New
GET /api/v1/portfolio
GET /api/v1/market/prices/AAPL
```

### Response Headers

```http
HTTP/1.1 200 OK
X-API-Version: v1
Content-Type: application/json
```

### Client Example (Python)

```python
import requests

base_url = "http://localhost:8000/api/v1"
response = requests.get(f"{base_url}/portfolio")

# Check version
version = response.headers.get("X-API-Version")
print(f"Using API version: {version}")

# Check for deprecation
if response.headers.get("Deprecation") == "true":
    print(f"Warning: Version deprecated! Sunset: {response.headers.get('Sunset')}")
```

### Client Example (TypeScript/Angular)

```typescript
const baseUrl = 'http://localhost:8000/api/v1';

this.http.get(`${baseUrl}/portfolio`, { observe: 'response' })
  .subscribe(response => {
    const version = response.headers.get('X-API-Version');
    console.log(`API Version: ${version}`);

    if (response.headers.get('Deprecation') === 'true') {
      console.warn('This API version is deprecated!');
    }
  });
```

## Adding a New Version (v2)

To add v2 in the future:

1. **Create new route files** (e.g., `routes_portfolio_v2.py`)
2. **Add router factory** in `api/versioning.py`:
   ```python
   def create_api_v2_router() -> APIRouter:
       api_v2_router = APIRouter(prefix="/api/v2")
       # Include v2 routes
       return api_v2_router
   ```
3. **Update VERSION_COMPATIBILITY** to include v2
4. **Register in main.py**: `app.include_router(create_api_v2_router())`

## Version Compatibility Matrix

| Version | Status | Deprecated | Sunset Date | Documentation |
|---------|--------|------------|-------------|---------------|
| v1 | Active | No | N/A | `/docs` |

## Migration Path

- Old endpoints (`/v1/...`) → **404 (not found)**
- New endpoints (`/api/v1/...`) → **Active and working**

## Testing

```bash
# Run versioning tests
pytest backend/tests/test_versioning.py -v

# All tests pass ✅
# 25 tests covering:
# - Version detection
# - Header injection
# - Deprecation warnings
# - Router creation
# - Endpoint structure
# - Migration readiness
```

## Documentation

Full versioning documentation available at:
- **`backend/docs/README.Versioning.md`** - Complete guide with examples
- **`backend/api/versioning.py`** - Implementation details
- **`backend/middleware/versioning.py`** - Middleware documentation

## Next Steps (Optional)

1. Update frontend to use new `/api/v1` endpoints
2. Add version-specific documentation pages
3. Set up version usage analytics
4. Create migration scripts for future version upgrades

## Benefits

- ✅ Clear API evolution path
- ✅ Backward compatibility support
- ✅ Deprecation management
- ✅ Better client communication
- ✅ Professional API structure
- ✅ Easier to maintain multiple versions
- ✅ Industry best practices
