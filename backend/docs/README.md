# Backend Documentation Index

Complete technical documentation for the Stock Portfolio Dashboard backend API.

## Table of Contents

### 🏗️ Architecture & Design
- **[Domain Architecture](README.Domains.md)** - Domain-Driven Design implementation
  - Market Data Domain (pricing, fundamentals, publishing)
  - Portfolio Domain (CRUD, performance, snapshots, alerts)
  - Event-driven architecture patterns
  - Repository pattern implementation

### 🔌 Infrastructure & Services
- **[Cache Service](README.Cache.md)** - Redis caching strategy
  - TTL management and cache key generation
  - Invalidation patterns (automatic, manual, pattern-based)
  - Get-or-set pattern and batch operations
  - Counter support and type safety

- **[Response Formatter](README.Formatter.md)** - Standardized API responses
  - Response envelope structure
  - Success and error formatting
  - Pagination support
  - Helper functions and best practices

- **[Health Monitoring](README.Health.md)** - Infrastructure health checks
  - PostgreSQL, Redis, and Kafka monitoring
  - Health check endpoints
  - Status reporting and error handling
  - Load balancer integration

- **[WebSocket Manager](README.WebSocket.md)** - Real-time communication
  - Connection lifecycle management
  - Topic-based subscriptions
  - Redis pub/sub for horizontal scaling
  - Client-server message protocols

### 🔐 Security & Authentication
- **[Authentication](README.Auth.md)** - JWT authentication implementation
  - Token generation (access & refresh)
  - Password hashing with bcrypt
  - Route protection dependencies
  - Role-based access control (RBAC)

### 📡 API Design
- **[API Versioning](README.Versioning.md)** - Versioning strategy
  - URL-based versioning
  - Version lifecycle (active, deprecated, sunset)
  - Backward compatibility
  - Migration guidelines

### 🧪 Testing
- **[Integration Testing](README.Integration.md)** - Integration test setup
  - Testcontainers configuration
  - Database fixtures
  - Test organization
  - Running integration tests

## Quick Links

### Getting Started
1. Read the [main README](../README.md) for setup instructions
2. Review [Domain Architecture](README.Domains.md) for overall structure
3. Check [Authentication](README.Auth.md) for securing endpoints

### Implementation Guides
- **Adding caching**: [Cache Service](README.Cache.md)
- **Formatting responses**: [Response Formatter](README.Formatter.md)
- **Real-time updates**: [WebSocket Manager](README.WebSocket.md)
- **Health checks**: [Health Monitoring](README.Health.md)

### Best Practices
- **Domain-Driven Design**: [Domain Architecture](README.Domains.md)
- **API Evolution**: [API Versioning](README.Versioning.md)
- **Testing Strategy**: [Integration Testing](README.Integration.md)

## Documentation Standards

All documentation follows these conventions:
- **Headers**: Clear section hierarchy with descriptive titles
- **Code Examples**: Practical, runnable code snippets
- **Type Annotations**: Full type hints in all examples
- **Error Handling**: Include error scenarios and edge cases
- **Links**: Cross-references to related documentation

## Contributing to Documentation

When updating documentation:
1. Keep examples concise and practical
2. Include both success and error scenarios
3. Update the table of contents if adding new sections
4. Verify all code examples are tested and working
5. Add cross-references to related topics
6. Use consistent formatting and terminology

---

**Last Updated**: April 2026
**Component**: Backend API Documentation
**Maintainer**: Development Team
