# API Versioning Guide

## Overview

The Stock Portfolio API uses URL-based versioning to ensure backward compatibility and provide a clear upgrade path for clients. All API endpoints are versioned using the `/api/v{number}` prefix.

## Current Version

**Current Version**: `v1` (1.0.0)

**Base URL**: `/api/v1`

## Versioning Strategy

### URL-Based Versioning

We use URL-based versioning because it's:
- **Explicit**: Version is clearly visible in the URL
- **Cache-friendly**: Different versions can be cached separately
- **Easy to test**: Simple to test multiple versions side-by-side
- **Developer-friendly**: Clear which version you're using

### Version Format

```
/api/{version}/{resource}/{endpoint}
```

Examples:
- `/api/v1/portfolio/1234`
- `/api/v1/market/prices/AAPL`
- `/api/v1/portfolio/1234/holdings`

## Available Versions

| Version | Status | Base URL | Documentation | Sunset Date |
|---------|--------|----------|---------------|-------------|
| v1 | Active | `/api/v1` | `/docs` | N/A |

## Using Versioned APIs

### Making Requests

```bash
# Portfolio endpoints
GET /api/v1/portfolio
GET /api/v1/portfolio/{id}
POST /api/v1/portfolio

# Market data endpoints
GET /api/v1/market/prices/{ticker}
GET /api/v1/market/tickers
GET /api/v1/market/fundamentals/{ticker}
```

### Response Headers

All API responses include versioning headers:

```http
HTTP/1.1 200 OK
X-API-Version: v1
Content-Type: application/json
```

For deprecated versions, additional headers are included:

```http
HTTP/1.1 200 OK
X-API-Version: v1
Deprecation: true
Sunset: 2027-12-31
Warning: 299 - "API version v1 is deprecated and will be removed on 2027-12-31"
Link: </docs>; rel="documentation"
```

## Version Lifecycle

### 1. Active
- Fully supported and maintained
- Receives bug fixes and security updates
- Recommended for all new integrations

### 2. Deprecated
- Still functional but not recommended for new integrations
- Receives only critical security fixes
- Sunset date announced
- Deprecation headers included in responses

### 3. Sunset
- Version is removed from the API
- All requests return 410 Gone
- Clients must upgrade to a newer version

## Upgrade Path

When a new API version is released:

1. **Announcement**: New version announced with migration guide
2. **Parallel Support**: Old and new versions run side-by-side (minimum 6 months)
3. **Deprecation**: Old version marked as deprecated (3 months before sunset)
4. **Sunset**: Old version removed from API

### Migration Timeline Example

```
Month 0: v2 released, v1 still active
Month 6: v1 marked as deprecated
Month 9: v1 sunset date announced (Month 12)
Month 12: v1 removed, only v2 available
```

## Breaking vs Non-Breaking Changes

### Non-Breaking Changes (Patch/Minor)
These changes don't require a new API version:
- Adding new optional fields to requests
- Adding new fields to responses
- Adding new endpoints
- Fixing bugs
- Performance improvements

### Breaking Changes (Major)
These changes require a new API version:
- Removing or renaming fields
- Changing field types
- Removing endpoints
- Changing authentication methods
- Changing business logic behavior
- Making optional fields required

## WebSocket Versioning

WebSocket connections are not versioned in the URL path but use protocol versioning:

```javascript
// WebSocket endpoint (URL doesn't change)
ws://localhost:8000/ws/portfolio?client_id=123

// Message format includes version
{
  "version": "v1",
  "type": "subscribe",
  "payload": { "portfolio_id": "uuid" }
}
```

## Version Detection

### Automatic Version Header

The API automatically adds version information to all responses:

```python
import requests

response = requests.get("http://localhost:8000/api/v1/portfolio")
print(response.headers.get("X-API-Version"))  # Output: v1
```

### Root Endpoint

Query the root endpoint to discover available versions:

```bash
GET /
```

Response:
```json
{
  "message": "Stock Portfolio API",
  "status": "running",
  "version": "1.0.0",
  "available_versions": ["v1"],
  "documentation": "/docs"
}
```

## Client Implementation Examples

### Python Client

```python
import requests

class PortfolioClient:
    def __init__(self, base_url: str, version: str = "v1"):
        self.base_url = base_url
        self.version = version
        self.api_base = f"{base_url}/api/{version}"

    def get_portfolios(self):
        response = requests.get(f"{self.api_base}/portfolio")

        # Check for deprecation
        if response.headers.get("Deprecation") == "true":
            print(f"Warning: API version {self.version} is deprecated")
            print(f"Sunset date: {response.headers.get('Sunset')}")

        return response.json()

# Usage
client = PortfolioClient("http://localhost:8000", version="v1")
portfolios = client.get_portfolios()
```

### TypeScript/Angular Client

```typescript
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class PortfolioApiService {
  private baseUrl = 'http://localhost:8000';
  private version = 'v1';
  private apiBase = `${this.baseUrl}/api/${this.version}`;

  constructor(private http: HttpClient) {}

  getPortfolios(): Observable<any> {
    return this.http.get(`${this.apiBase}/portfolio`, { observe: 'response' })
      .pipe(
        tap(response => {
          const apiVersion = response.headers.get('X-API-Version');
          const deprecated = response.headers.get('Deprecation');

          if (deprecated === 'true') {
            const sunsetDate = response.headers.get('Sunset');
            console.warn(
              `API version ${apiVersion} is deprecated.`,
              `Sunset date: ${sunsetDate}`
            );
          }
        })
      );
  }
}
```

## Adding a New Version

To add a new API version (e.g., v2):

### 1. Create New Route Files

```bash
backend/routes_portfolio_v2.py
backend/routes_market_v2.py
```

### 2. Update Versioning Module

```python
# backend/api/versioning.py

from backend.routes_market_v2 import router as market_router_v2
from backend.routes_portfolio_v2 import router as portfolio_router_v2

def create_api_v2_router() -> APIRouter:
    """Create and configure the API v2 router."""
    api_v2_router = APIRouter(prefix="/api/v2")

    api_v2_router.include_router(
        market_router_v2,
        tags=["v2-market"],
    )
    api_v2_router.include_router(
        portfolio_router_v2,
        tags=["v2-portfolio"],
    )

    return api_v2_router

# Update VERSION_COMPATIBILITY
VERSION_COMPATIBILITY = {
    "v1": {
        "min_client_version": "1.0.0",
        "deprecated": True,  # Mark v1 as deprecated
        "sunset_date": "2027-06-30",
        "documentation_url": "/docs",
    },
    "v2": {
        "min_client_version": "2.0.0",
        "deprecated": False,
        "sunset_date": None,
        "documentation_url": "/docs/v2",
    },
}
```

### 3. Register in Main App

```python
# backend/main.py

from backend.api.versioning import create_api_v1_router, create_api_v2_router

# Include versioned API routers
api_v1 = create_api_v1_router()
api_v2 = create_api_v2_router()

app.include_router(api_v1)
app.include_router(api_v2)
```

## Best Practices

### For API Developers

1. **Never break existing versions**: Once released, a version's API contract is frozen
2. **Document all changes**: Maintain a changelog for each version
3. **Provide migration guides**: Help clients upgrade to new versions
4. **Test all versions**: Ensure old versions continue to work during parallel support
5. **Use semantic versioning**: Follow semver for version numbers (MAJOR.MINOR.PATCH)

### For API Consumers

1. **Always specify version**: Don't rely on default version behavior
2. **Monitor deprecation headers**: Watch for deprecation warnings
3. **Plan upgrades**: Don't wait until sunset to upgrade
4. **Test new versions early**: Try new versions in staging before production
5. **Handle version errors gracefully**: Implement fallback logic for version changes

## Monitoring and Analytics

Track version usage to make informed decisions:

```python
# Example: Log version usage
logger.info(
    "API request",
    extra={
        "version": version,
        "endpoint": request.url.path,
        "client_ip": request.client.host,
    }
)
```

## FAQ

### Q: What happens if I don't specify a version?
A: You must specify a version in the URL path. Unversioned endpoints will return 404.

### Q: Can I use multiple versions in the same application?
A: Yes! You can use different versions for different features during migration.

### Q: How long are deprecated versions supported?
A: Minimum 6 months of parallel support, with at least 3 months' notice before sunset.

### Q: What if I find a bug in a deprecated version?
A: Critical security fixes are backported. Feature bugs require upgrading to the current version.

### Q: Can I request features in old versions?
A: No. New features are only added to the current version.

## Resources

- API Documentation: `/docs`
- Changelog: `/CHANGELOG.md`
- Migration Guides: `/docs/migrations/`
- Support: GitHub Issues

## Version History

| Version | Release Date | Sunset Date | Status | Notes |
|---------|-------------|-------------|--------|-------|
| v1 | 2026-04-12 | N/A | Active | Initial release |
