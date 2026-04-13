# API Versioning Quick Reference

## 🚀 Quick Start

### Current API Version: v1

**Base URL**: `http://localhost:8000/api/v1`

## 📍 Endpoint Changes

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `/v1/portfolio` | `/api/v1/portfolio` | ✅ Active |
| `/v1/market/prices/{ticker}` | `/api/v1/market/prices/{ticker}` | ✅ Active |
| `/ws/portfolio` | `/ws/portfolio` | ✅ Unchanged |

## 💻 API Endpoints

### Portfolio API
```bash
GET    /api/v1/portfolio              # List all portfolios
GET    /api/v1/portfolio/{id}         # Get portfolio by ID
GET    /api/v1/portfolio/{id}/holdings     # Get holdings
GET    /api/v1/portfolio/{id}/performance  # Get performance
GET    /api/v1/portfolio/{id}/allocation   # Get allocation
```

### Market Data API
```bash
GET    /api/v1/market/prices/{ticker}      # Historical prices
GET    /api/v1/market/prices/{ticker}/latest  # Latest price
GET    /api/v1/market/fundamentals/{ticker}   # Company fundamentals
GET    /api/v1/market/tickers             # List all tickers
```

### System Endpoints
```bash
GET    /                  # API info & available versions
GET    /api/health       # Health check
GET    /docs             # API documentation
```

### WebSocket
```bash
WS     /ws/portfolio?client_id={id}   # Real-time portfolio updates
```

## 🔧 Response Headers

All versioned endpoints include:
```http
X-API-Version: v1
```

Deprecated versions also include:
```http
Deprecation: true
Sunset: YYYY-MM-DD
Warning: 299 - "API version v1 is deprecated..."
```

## 📝 Code Examples

### cURL
```bash
# Get portfolios
curl http://localhost:8000/api/v1/portfolio

# Get market prices
curl "http://localhost:8000/api/v1/market/prices/AAPL?from=2024-01-01&to=2024-12-31"

# Check API version
curl -I http://localhost:8000/api/v1/portfolio | grep X-API-Version
```

### Python
```python
import requests

# Make request
response = requests.get("http://localhost:8000/api/v1/portfolio")

# Check version
api_version = response.headers.get("X-API-Version")
print(f"API Version: {api_version}")

# Check if deprecated
if response.headers.get("Deprecation") == "true":
    print(f"⚠️ Warning: API deprecated! Sunset: {response.headers.get('Sunset')}")

data = response.json()
```

### TypeScript/Angular
```typescript
import { HttpClient } from '@angular/common/http';

const baseUrl = 'http://localhost:8000/api/v1';

// Make request and check headers
this.http.get(`${baseUrl}/portfolio`, { observe: 'response' })
  .subscribe(response => {
    const version = response.headers.get('X-API-Version');
    console.log(`API Version: ${version}`);

    if (response.headers.get('Deprecation') === 'true') {
      console.warn('⚠️ API version deprecated!');
    }

    const data = response.body;
  });
```

### JavaScript (Fetch)
```javascript
// Make request
const response = await fetch('http://localhost:8000/api/v1/portfolio');

// Check version
const version = response.headers.get('X-API-Version');
console.log(`API Version: ${version}`);

// Check deprecation
if (response.headers.get('Deprecation') === 'true') {
  console.warn('⚠️ API version deprecated!');
  console.log(`Sunset: ${response.headers.get('Sunset')}`);
}

const data = await response.json();
```

## 🔍 Version Discovery

### Get Available Versions
```bash
curl http://localhost:8000/
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

## 📋 Migration Checklist

When upgrading to a new version:

- [ ] Review migration guide
- [ ] Update base URL in code (`/api/v1` → `/api/v2`)
- [ ] Test in development environment
- [ ] Update integration tests
- [ ] Deploy to staging
- [ ] Monitor for errors
- [ ] Deploy to production
- [ ] Monitor version usage metrics

## ⚠️ Important Notes

1. **Always specify version**: Don't use unversioned endpoints
2. **Monitor headers**: Watch for deprecation warnings
3. **Plan upgrades**: Don't wait until sunset date
4. **Test early**: Try new versions before they're mandatory
5. **Version locking**: Pin to specific version in production

## 🆘 Troubleshooting

### 404 Not Found
- Check you're using `/api/v1/...` not `/v1/...`
- Verify endpoint exists in documentation
- Ensure HTTP method is correct (GET/POST/etc.)

### Version Header Missing
- Only `/api/v{X}/` endpoints include version header
- Root and health endpoints may not have it

### Deprecation Warning
- Update to latest version soon
- Check sunset date in `Sunset` header
- Review migration guide

## 📚 Documentation

- **Full Guide**: `/backend/docs/README.Versioning.md`
- **API Docs**: `http://localhost:8000/docs`
- **Implementation**: `/backend/api/versioning.py`

## 🧪 Testing

```bash
# Run versioning tests
pytest backend/tests/test_versioning.py -v

# Test specific endpoint
curl -v http://localhost:8000/api/v1/portfolio
```

## 📊 Version Status

| Version | Status | Deprecated | Sunset | Min Client |
|---------|--------|-----------|--------|------------|
| v1 | ✅ Active | No | N/A | 1.0.0 |

---

**Questions?** Check [README.Versioning.md](../backend/docs/README.Versioning.md) for detailed information.
