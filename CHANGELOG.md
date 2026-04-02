# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project setup with monorepo structure
- Angular 20 frontend application with SSR support
- FastAPI backend with Python 3.11+
- Docker and Docker Compose configuration for local development
- PostgreSQL, Redis, and Kafka infrastructure setup
- Comprehensive code quality tooling
  - ESLint and Prettier for TypeScript/Angular
  - Black, Ruff, and mypy for Python
  - Husky and pre-commit hooks
  - Commitlint for conventional commits
- GitHub Actions CI/CD workflows
  - CI workflow for tests, linting, and type checking
  - Docker build workflow with GitHub Container Registry
  - CodeQL security analysis
  - Dependency review
  - Multi-environment deployment workflow (DEV/QA/PROD)
- GitHub templates
  - Pull request template
  - Bug report template
  - Feature request template
- Documentation
  - Root README with architecture overview
  - Code quality guide
  - Docker setup guide
  - Environment deployment guide
- VS Code configuration
  - Recommended extensions
  - Workspace settings for auto-formatting
- EditorConfig for consistent coding styles

### Changed

- Consolidated Prettier configuration to root `.prettierrc.json`
- Simplified package.json scripts with frontend/backend separation
- Reorganized documentation structure with clearer naming

### Infrastructure

- Docker Compose orchestration for 6 services (frontend, backend, postgres, redis, kafka, zookeeper)
- Multi-stage Docker builds for optimized image sizes
- Health checks for all containerized services

### Developer Experience

- One-command setup with `docker-compose up`
- Automated pre-commit hooks for code quality
- Comprehensive documentation for onboarding
- CI/CD automation for consistent builds

---

## Version History

### [1.0.0] - YYYY-MM-DD

_Initial release - Coming soon_

---

## Versioning Guidelines

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible new features
- **PATCH** version for backwards-compatible bug fixes

## Commit Types

Commits follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Adding or updating tests
- `build:` - Build system changes
- `ci:` - CI/CD changes
- `chore:` - Other changes (dependencies, etc.)

---

[unreleased]: https://github.com/USERNAME/stock-portfolio-dashboard/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/USERNAME/stock-portfolio-dashboard/releases/tag/v1.0.0
