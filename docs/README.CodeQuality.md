# Code Quality & Consistency Setup

This project uses multiple tools to ensure code quality and consistency across the monorepo. # noqa E999

## Tools Overview

### Frontend (Angular)

- **ESLint**: TypeScript and Angular linting
- **Prettier**: Code formatting
- **TypeScript**: Type checking
- **Husky**: Git hooks

### Backend (Python)

- **Black**: Code formatting
- **Ruff**: Fast linting and import sorting
- **mypy**: Static type checking
- **Bandit**: Security linting
- **pre-commit**: Git hooks for Python

### Commit Messages

- **commitlint**: Enforces conventional commits

## Installation

### 1. Install Node.js dependencies (root and frontend)

```powershell
# Install root dependencies (husky, commitlint)
npm install

# Install frontend dependencies
cd portfolio-dashboard
npm install
cd ..
```

### 2. Install Python dependencies (backend)

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Install pre-commit hooks

```powershell
# Install pre-commit hooks for Python
pre-commit install

# Initialize Husky hooks for Node
npm run prepare
```

## Usage

### Running Checks Manually

#### Frontend Checks

```powershell
# Lint TypeScript/Angular files
npm run lint --workspace=portfolio-dashboard

# Fix linting issues
npm run lint:fix --workspace=portfolio-dashboard

# Format code with Prettier
npm run format --workspace=portfolio-dashboard

# Check formatting
npm run format:check --workspace=portfolio-dashboard

# Type check
npm run type-check --workspace=portfolio-dashboard
```

#### Backend Checks

```powershell
cd backend

# Format code with Black
black .

# Lint with Ruff
ruff check .

# Fix linting issues
ruff check --fix .

# Type check with mypy
mypy .

# Security check with Bandit
bandit -r . -c pyproject.toml
```

#### Run All Checks

```powershell
# From root directory
npm run lint
npm run format
npm run type-check
```

### Automated Checks

Checks run automatically on:

- **Pre-commit**: Type checking, linting, formatting
- **Commit message**: Validates conventional commit format

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

**Examples:**

```bash
git commit -m "feat(portfolio): add stock filtering feature"
git commit -m "fix(api): handle null values in stock data"
git commit -m "docs: update README with setup instructions"
git commit -m "refactor(backend): simplify database queries"
```

## Configuration Files

- **Root:**
  - `package.json` - Node workspace config
  - `commitlint.config.js` - Commit message rules
  - `.husky/` - Git hooks
  - `.pre-commit-config.yaml` - Python pre-commit hooks

- **Frontend:**
  - `portfolio-dashboard/eslint.config.js` - ESLint rules
  - `portfolio-dashboard/package.json` - Prettier config

- **Backend:**
  - `backend/pyproject.toml` - Black, Ruff, mypy config

## Bypassing Hooks (Emergency Only)

```bash
# Skip pre-commit hooks (not recommended)
git commit --no-verify -m "emergency fix"

# Skip only specific pre-commit hooks
SKIP=eslint git commit -m "message"
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Install dependencies
  run: |
    npm ci
    pip install -r backend/requirements.txt

- name: Run linting
  run: |
    npm run lint
    npm run type-check
    cd backend && ruff check . && mypy .
```

## Troubleshooting

### Husky hooks not running

```powershell
npm run prepare
```

### Pre-commit hooks not running

```powershell
pre-commit install
```

### Update pre-commit hooks

```powershell
pre-commit autoupdate
```

### Run pre-commit on all files

```powershell
pre-commit run --all-files
```

### ESLint errors in IDE

Install the ESLint extension for VS Code and restart.

## IDE Integration

### VS Code

Install recommended extensions:

- ESLint
- Prettier
- Python
- Pylance
- Black Formatter

Add to `.vscode/settings.json`:

```json
{
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "editor.formatOnSave": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true
}
```
