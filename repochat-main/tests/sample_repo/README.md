# Sample E-commerce API (test fixture)

A tiny, intentionally simplified codebase used to exercise the Codebase
Intelligence System. It has:

- Authentication (`src/auth/authentication.py`)
- A database layer (`src/db/connection.py`)
- API route handlers (`src/api/routes.py`)
- A user service (`src/services/user_service.py`)
- Tests (`tests/test_auth.py`)
- Two intentional bugs, for testing the "find potential bugs" feature:
  1. `hash_password` uses no per-user salt (see docstring).
  2. `get_connection` does not handle connection failures (see docstring).