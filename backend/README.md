# Arvalox Backend

FastAPI-based backend for the Arvalox Invoice Management System.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Local Development Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd arvalox/backend
```

### 2. Create Virtual Environment

Using uv (recommended):
```bash
uv venv --python 3.11
```

Or using Python's built-in venv:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

Using uv:
```bash
uv pip install -r requirements.txt
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 4. Database Setup

Create PostgreSQL databases:
```bash
# Connect to PostgreSQL
psql -U postgres

# Create databases
CREATE DATABASE arvalox_dev;
CREATE DATABASE arvalox_test;


# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE arvalox_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE arvalox_test TO postgres;

# Exit
\q
```

### 5. Environment Configuration

Copy and configure the environment file:
```bash
cp .env.example .env
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

> Update `.env` with your configuration

### 6. Database Migration

Initialize and run migrations:
```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 7. Run the Application

Start the development server:
```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the run script
python run.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Tools

### Linting and Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check for linting issues
ruff check .

# Fix linting issues automatically
ruff check . --fix

# Format code
ruff format .

# Run both linting and formatting
./scripts/lint.sh
```

### Testing

Run tests using pytest:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_main.py

# Run with verbose output
pytest -v
```

### Database Operations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# View migration history
alembic history
```

## Contributing

1. Follow the existing code style (enforced by Ruff)
2. Write tests for new features
3. Update documentation as needed
4. Run linting and tests before committing

