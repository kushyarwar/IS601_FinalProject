# Final Project Reflection – IS601

## What I Built

A full-stack calculator web application with:

- **Secure authentication** – JWT-based login/registration with bcrypt password hashing
- **BREAD operations** – users can Browse, Read, Edit, Add, and Delete their own calculations
- **Six math operations** – Add, Subtract, Multiply, Divide, **Power** (a^b), and **Modulus** (a%b)
- **User Profile management** – update username, email, bio, and change password with re-login flow
- **Usage Reports dashboard** – per-user stats: total calculations, most-used operation, average result, operation breakdown with visual bars
- **Alembic migrations** – versioned schema management for production-safe DB changes
- **Full CI/CD pipeline** – GitHub Actions runs all tests, builds the Docker image, and pushes to Docker Hub on every merge to main

---

## How Modules 12–14 Led Here

| Module | What It Introduced | How the Final Project Extends It |
|---|---|---|
| Module 12 | SQLAlchemy models, BREAD routes, basic pytest integration tests | Final project keeps BREAD as the core, adds Power and Modulus, adds user-scoping |
| Module 13 | JWT authentication, bcrypt hashing, static HTML login/register pages, Playwright E2E tests | Final project builds on the same JWT/bcrypt stack, extends E2E tests to cover all new features |
| Module 14 | User-scoped calculations (each user sees only their own data), Docker + postgres + pgAdmin compose stack | Final project keeps user-scoping, adds profile management, reports, and splits app into `APIRouter` modules |

---

## Security Decisions

- **JWT (HS256)** with a 30-minute expiry. The secret is injected via the `JWT_SECRET` environment variable. The app logs a warning at startup if the default development secret is still in use.
- **bcrypt** with per-password salts — two identical passwords produce different hashes, preventing rainbow table attacks.
- **User-scoped data** — every calculation query filters by `user_id == current_user.id`. A user requesting another user's calculation gets a 404, not a 403, to avoid leaking whether the resource exists.
- **Self-only delete** — `DELETE /users/{id}` returns 403 if the authenticated user tries to delete someone else's account.
- **All routes protected** — `GET /users/`, `GET /users/{id}`, `DELETE /users/{id}`, and `GET /calculations/join/all` all require a valid JWT. No user data is publicly accessible.
- **Input validation** — Pydantic schemas reject division/modulus by zero, enforce minimum password length (8 chars), and validate email format before any DB interaction.

---

## Testing Approach

| Layer | Count | What It Covers |
|---|---|---|
| Unit | 30 tests | Calculator operations (all 6), bcrypt hash/verify, JWT create/decode/tamper, Pydantic schema validators |
| Integration | 34 tests | All API routes including auth guards, BREAD, profile, password change, reports, cascade deletes |
| E2E (Playwright) | 17 tests | Full browser flows: register, login, BREAD with Power/Modulus, profile update, password change, reports dashboard |

Tests use SQLite in-memory for speed locally and a real PostgreSQL 15 instance in CI to match production.

---

## Challenges and What I Learned

- **Route ordering matters in FastAPI** — `/users/me/profile` must be declared before `/users/{user_id}` or FastAPI matches `me` as an integer ID and returns a 422.
- **E2E token injection** — Pages that redirect unauthenticated users require setting `localStorage` on a neutral page first before navigating to the protected page. Doing `goto → set token → reload` fails when the initial load already triggers a redirect.
- **Alembic with environment variables** — Alembic's `env.py` must read `DATABASE_URL` from the environment at runtime so the same codebase works locally (SQLite), in Docker (PostgreSQL), and in CI (PostgreSQL service container).
