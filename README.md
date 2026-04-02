# Stock Portfolio Dashboard

A full-stack stock portfolio management application built with **Angular** (frontend) and **FastAPI** (backend), featuring real-time stock tracking, analytics, and a modern microservices architecture.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development](#development)
- [Code Quality](#code-quality)
- [Docker & Infrastructure](#docker--infrastructure)
- [Documentation](#documentation)

## 🎯 Overview

This application provides a comprehensive stock portfolio management system with:

- Real-time stock price tracking and updates
- Portfolio analytics and performance metrics
- Interactive dashboards and visualizations
- RESTful API with comprehensive documentation
- Event-driven architecture using Kafka
- Caching layer with Redis
- PostgreSQL database for persistent storage

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Angular)                  │
│                  http://localhost:4200                   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────┐
│                  Backend API (FastAPI)                   │
│                  http://localhost:8000                   │
└─────┬──────────┬──────────┬──────────────────────────────┘
      │          │          │
      ▼          ▼          ▼
 ┌──────────┐ ┌──────┐ ┌────────────┐
 │PostgreSQL│ │Redis │ │Kafka       │
 │:5432     │ │:6379 │ │:9092/9093  │
 └──────────┘ └──────┘ └────────────┘
```

### Key Components

- **Frontend**: Angular 20 with SSR (Server-Side Rendering), RxJS for reactive programming
- **Backend**: FastAPI (Python 3.11+) with async/await support
- **Database**: PostgreSQL 16 for relational data storage
- **Cache**: Redis 7 for high-performance caching
- **Message Broker**: Apache Kafka for event streaming and real-time updates
- **Containerization**: Docker and Docker Compose for local development and deployment

## 🛠️ Tech Stack

### Frontend

- **Framework**: Angular 20.3
- **Language**: TypeScript 5.9
- **UI/Styling**: SCSS
- **HTTP Client**: Angular HttpClient
- **State Management**: RxJS
- **Build Tool**: Angular CLI with esbuild

### Backend

- **Framework**: FastAPI 0.115
- **Language**: Python 3.11+
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic 2.9
- **HTTP Client**: httpx

### Infrastructure

- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Message Broker**: Kafka 7.5 + Zookeeper
- **Containerization**: Docker & Docker Compose
- **Version Control**: Git with Conventional Commits

### Development Tools

- **Linting**: ESLint (TypeScript), Ruff (Python)
- **Formatting**: Prettier (TypeScript), Black (Python)
- **Type Checking**: TypeScript Compiler, mypy
- **Git Hooks**: Husky (Node), pre-commit (Python)
- **Commit Linting**: Commitlint with Conventional Commits
- **CI/CD**: GitHub Actions for automated testing and deployment

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+ and npm 10+
- **Python** 3.11+
- **Docker Desktop** (for containerized setup)
- **Git**

### Option 1: Docker (Recommended)

```powershell
# 1. Clone the repository
git clone <repository-url>
cd stock-portfolio-dashboard

# 2. Create environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Start all services
docker-compose up --build

# Access the application:
# - Frontend: http://localhost:4200
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```powershell
# 1. Install root dependencies
npm install

# 2. Setup Frontend
cd portfolio-dashboard
npm install
npm start  # Runs on http://localhost:4200

# 3. Setup Backend (new terminal)
cd ../backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py  # Runs on http://localhost:8000
```

## 📁 Project Structure

```
stock-portfolio-dashboard/
├── backend/                    # FastAPI backend application
│   ├── main.py                # Application entry point
│   ├── routes.py              # API route definitions
│   ├── models.py              # Data models
│   ├── config.py              # Configuration management
│   ├── requirements.txt       # Python dependencies
│   ├── pyproject.toml         # Python tooling config
│   ├── Dockerfile             # Backend container image
│   └── README.md              # Backend documentation
│
├── portfolio-dashboard/        # Angular frontend application
│   ├── src/                   # Source code
│   │   ├── app/               # Application components
│   │   ├── index.html         # Entry HTML
│   │   └── styles.scss        # Global styles
│   ├── package.json           # Node dependencies
│   ├── angular.json           # Angular CLI config
│   ├── tsconfig.json          # TypeScript config
│   ├── eslint.config.js       # ESLint configuration
│   ├── Dockerfile             # Frontend container image
│   └── README.md              # Frontend documentation
│
├── docker-compose.yml         # Multi-container orchestration
├── .env.example               # Example environment variables
├── package.json               # Root workspace config
├── commitlint.config.js       # Commit message linting
├── .pre-commit-config.yaml    # Python pre-commit hooks
├── .github/                   # GitHub configuration
│   ├── workflows/             # GitHub Actions CI/CD
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/        # Issue templates
├── .husky/                    # Git hooks (Husky)
├── .vscode/                   # VS Code settings
├── .editorconfig              # Editor configuration
├── .gitignore                 # Git ignore patterns
│
└── README.md                  # This file
```

## 💻 Development

### Running Development Servers

**Frontend:**

```powershell
cd portfolio-dashboard
npm start
# Available at http://localhost:4200
```

**Backend:**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python main.py
# Available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Common Commands

```powershell
# Frontend
npm run lint              # Lint TypeScript/Angular code
npm run format            # Format code with Prettier
npm run type-check        # TypeScript type checking
npm run build             # Production build

# Backend
black .                   # Format Python code
ruff check .              # Lint Python code
mypy .                    # Type check Python code
pytest                    # Run tests (when added)
```

### Building for Production

```powershell
# Frontend
cd portfolio-dashboard
npm run build
# Output in dist/portfolio-dashboard/

# Backend (already production-ready)
# Set DEBUG=false in .env

# Docker (all services)
docker-compose up --build -d
```

## ✅ Code Quality

This project enforces code quality and consistency through automated tooling.

### Commit Message Format

We use **Conventional Commits** enforced by commitlint:

```
<type>(<scope>): <subject>

Examples:
feat(portfolio): add stock filtering feature
fix(api): handle null values in stock data
docs: update setup instructions
refactor(backend): simplify database queries
```

#### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Pre-commit Hooks

Automated checks run before every commit:

- ✅ TypeScript/Angular linting (ESLint)
- ✅ Python linting (Ruff)
- ✅ Code formatting (Prettier, Black)
- ✅ Type checking (TypeScript, mypy)
- ✅ Commit message validation

**Bypass checks (emergency only):**

```powershell
git commit --no-verify -m "emergency fix"
```

### Setup Git Hooks

```powershell
# Install all hooks
npm install              # Installs Husky
pre-commit install       # Installs Python pre-commit
```

📖 **Detailed Guide**: See [README.CodeQuality.md](README.CodeQuality.md)

## � CI/CD Pipeline

### GitHub Actions Workflows

The project includes automated CI/CD pipelines that run on every push and pull request:

#### CI Workflow

- ✅ Frontend linting and type checking (ESLint, TypeScript)
- ✅ Backend linting and type checking (Ruff, Black, mypy)
- ✅ Security scanning (Bandit, CodeQL)
- ✅ Unit tests for both frontend and backend
- ✅ Commit message validation (Commitlint)
- ✅ Production build verification

#### Docker Build Workflow

- 🐳 Builds Docker images for frontend and backend
- 🐳 Pushes to GitHub Container Registry on main branch
- 🐳 Tags images with branch name, commit SHA, and semantic versions
- 🐳 Tests docker-compose setup

#### Security Workflows

- 🔒 CodeQL security analysis (weekly + on PR)
- 🔒 Dependency review on pull requests
- 🔒 Automated vulnerability scanning

### Workflow Triggers

**On Pull Request:**

```
✓ Run all tests and linting
✓ Validate commit messages
✓ Check code security
✓ Build Docker images (no push)
✓ Review dependencies
```

**On Push to Branches:**

```
develop → DEV environment (auto-deploy)
staging → QA environment (auto-deploy)
main    → PROD environment (requires approval)
```

**Manual Trigger:**

- Deploy to any environment on-demand via Actions tab

### Viewing CI Status

Check the **Actions** tab in your GitHub repository to view:

- Build status and logs
- Test results
- Security scan reports
- Docker image build outputs

### CI/CD Configuration Files

- `.github/workflows/ci.yml` - Main CI pipeline (tests, linting)
- `.github/workflows/deploy.yml` - Environment deployments (DEV/QA/PROD)
- `.github/workflows/docker-build.yml` - Docker image builds
- `.github/workflows/codeql.yml` - Security analysis
- `.github/workflows/dependency-review.yml` - Dependency scanning
- `.github/ENVIRONMENTS_GUIDE.md` - Deployment setup guide

## �🐳 Docker & Infrastructure

### Docker Compose Services

The application uses Docker Compose to orchestrate 6 services:

| Service   | Port(s)    | Description                  |
| --------- | ---------- | ---------------------------- |
| frontend  | 4200:80    | Angular application (nginx)  |
| backend   | 8000:8000  | FastAPI application          |
| postgres  | 5432:5432  | PostgreSQL database          |
| redis     | 6379:6379  | Redis cache                  |
| kafka     | 9092, 9093 | Kafka message broker         |
| zookeeper | 2181:2181  | Zookeeper (Kafka dependency) |

### Docker Commands

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose build backend

# Clean restart (removes volumes)
docker-compose down -v
docker-compose up --build
```

### Dockerfile Locations

- **Backend**: `backend/Dockerfile` - Python 3.11 slim image
- **Frontend**: `portfolio-dashboard/Dockerfile` - Multi-stage build (Node → nginx)

📖 **Detailed Guide**: See [README.Docker.md](README.Docker.md)

## 📚 Documentation

### Available Documentation

- **[README.CodeQuality.md](docs/README.CodeQuality.md)** - Code quality tools, linting, formatting, and commit conventions
- **[README.Docker.md](docs/README.Docker.md)** - Docker setup, commands, and troubleshooting
- **[backend/README.md](backend/README.md)** - Backend API documentation and setup
- **[portfolio-dashboard/README.md](portfolio-dashboard/README.md)** - Frontend application documentation

### API Documentation

Once the backend is running, interactive API documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Additional Resources

- [Angular Documentation](https://angular.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes following the code quality guidelines
3. Commit using conventional commits: `git commit -m "feat(scope): description"`
4. Push and create a Pull Request

Pre-commit hooks will automatically run to ensure code quality standards are met.

## 📝 License

[Specify your license here]

## 👥 Authors

[Your name/team here]

---

**Need Help?**

- Check the detailed documentation in the links above
- Review API documentation at http://localhost:8000/docs
- Open an issue in the repository
