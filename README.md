# IS601 Final Project – Advanced Calculator API

A full-stack web application built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and **Playwright** that provides secure calculator functionality with user authentication, profile management, extended operations, and a usage reporting dashboard.

## Features

### Core (BREAD Operations)
- Create, Read, Browse, Edit, and Delete calculations
- All operations are user-scoped and JWT-protected

### New Operations (Final Project Feature 1)
- **Power** – `a ^ b` (exponentiation)
- **Modulus** – `a % b` (remainder)

### User Profile & Password Change (Final Project Feature 2)
- View and update username, email, and bio
- Change password with current-password verification
- Automatic logout and re-login prompt after password change

### Reports & History Dashboard (Final Project Feature 3)
- Total calculations performed
- Most used operation
- Average result across all calculations
- Per-operation breakdown with visual usage bars
- Last calculation display

### Security
- JWT authentication (HS256, 30-minute expiry)
- bcrypt password hashing
- User-scoped data (users can only access their own calculations)
- Input validation via Pydantic schemas

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.111, Python 3.11 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| Migrations | Alembic 1.13 |
| Auth | python-jose (JWT) + bcrypt |
| Frontend | Vanilla HTML/CSS/JS |
| Testing | pytest + Playwright |
| CI/CD | GitHub Actions |
| Deployment | Docker + Docker Hub |

---

## Running the Application

### Prerequisites
- Docker Desktop installed and running

### Start with Docker Compose

```bash
git clone <your-repo-url>
cd IS601_FinalProject
docker compose up --build
```

The app will be available at:
- **App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (admin@admin.com / admin)

### Pages

| URL | Description |
|---|---|
| `/static/login.html` | Login page |
| `/static/register.html` | Registration page |
| `/static/calculations.html` | BREAD calculator UI |
| `/static/profile.html` | Profile & password change |
| `/static/reports.html` | Usage statistics dashboard |

---

## Running Tests Locally

### Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### Unit & Integration Tests (SQLite)

```bash
pytest tests/ --ignore=tests/e2e -v --cov=app --cov-report=term-missing
```

### Unit & Integration Tests (PostgreSQL)

```bash
# Start only the DB:
docker compose up db -d

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
pytest tests/ --ignore=tests/e2e -v
```

### E2E Playwright Tests

```bash
pytest tests/e2e/ -v
```

The E2E suite spins up a live uvicorn server on port 8001 automatically using an in-memory SQLite database.

---

## Running Alembic Migrations

Alembic is configured to read `DATABASE_URL` from the environment.

```bash
# Apply all migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Check current revision
alembic current

# Generate a new migration (after model changes)
alembic revision --autogenerate -m "describe your change"
```

When using Docker Compose, run migrations inside the web container:

```bash
docker compose exec web alembic upgrade head
```

---

## API Reference

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Register new user, returns JWT |
| POST | `/login` | No | Login, returns JWT |

### Profile
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/users/me/profile` | JWT | Get current user profile |
| PUT | `/users/me/profile` | JWT | Update username, email, or bio |
| POST | `/users/me/change-password` | JWT | Change password |

### Calculations
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/calculations` | JWT | Create calculation |
| GET | `/calculations` | JWT | Browse all your calculations |
| GET | `/calculations/{id}` | JWT | Read one calculation |
| PUT | `/calculations/{id}` | JWT | Edit calculation (recomputes) |
| PATCH | `/calculations/{id}` | JWT | Partial edit |
| DELETE | `/calculations/{id}` | JWT | Delete calculation |

**Supported operations:** `Add`, `Sub`, `Multiply`, `Divide`, `Power`, `Modulus`

### Reports
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/reports/summary` | JWT | Usage stats (total, avg, most used, breakdown) |

---

## Docker Hub

The Docker image is automatically built and pushed on every merge to `main`:

```
docker pull kushyarwar/is601-final:latest
```

Docker Hub: https://hub.docker.com/r/kushyarwar/is601-final

---

## CI/CD Pipeline

GitHub Actions runs on every push and pull request to `main`:

1. **Test job**: Spins up PostgreSQL, installs dependencies, runs unit + integration tests, then E2E Playwright tests
2. **build-and-push job** (main branch only): Builds Docker image, pushes to Docker Hub, runs Trivy vulnerability scan

Pipeline secrets required in GitHub repository settings:
- `DOCKERHUB_USERNAME` – your Docker Hub username
- `DOCKERHUB_TOKEN` – your Docker Hub access token

---

## Project Structure

```
IS601_FinalProject/
├── app/
│   ├── main.py          # FastAPI app, all routes
│   ├── models.py        # SQLAlchemy User + Calculation models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── calculator.py    # CalculationFactory + all 6 OperationTypes
│   ├── auth.py          # bcrypt hash/verify
│   ├── jwt_utils.py     # JWT create/decode
│   ├── database.py      # SQLAlchemy engine + session
│   └── reports.py       # Usage stats aggregation logic
├── alembic/
│   ├── env.py           # Alembic environment config
│   └── versions/
│       └── 001_initial_schema.py
├── static/
│   ├── login.html
│   ├── register.html
│   ├── calculations.html
│   ├── profile.html
│   └── reports.html
├── tests/
│   ├── conftest.py          # pytest fixtures (SQLite test DB)
│   ├── test_unit.py         # Unit tests: calculator, auth, JWT, schemas
│   ├── test_integration.py  # Integration tests: all API routes
│   └── e2e/
│       ├── conftest.py      # Live server fixture
│       └── test_e2e.py      # Playwright E2E tests
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── requirements.txt
```
