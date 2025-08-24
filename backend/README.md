# Arvalox Backend

FastAPI-based backend for the Arvalox Invoice Management System.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+

## Getting Started

### 1. Setup Virtual Environment

```bash
cd arvalox/backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Create PostgreSQL databases:
```bash
psql -U postgres
CREATE DATABASE arvalox_dev;
CREATE DATABASE arvalox_test;
\q
```

### 4. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/arvalox_dev
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/arvalox_test

# Security
SECRET_KEY=your-generated-secret-key-here

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Paystack
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
PAYSTACK_WEBHOOK_SECRET=your_webhook_secret_here
```

### 5. Database Migration

```bash
alembic upgrade head
```

### 6. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_subscription.py
```

## Development Tools

### Linting and Formatting

```bash
# Check linting
ruff check .

# Fix issues
ruff check . --fix

# Format code
ruff format .
```

### Database Operations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Commands to Remember

```bash
# Start backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Apply migrations
alembic upgrade head

# Format and lint
ruff format . && ruff check . --fix
```