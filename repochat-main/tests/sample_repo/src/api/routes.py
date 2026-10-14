"""HTTP routes for the sample e-commerce API."""

from src.auth.authentication import authenticate_user
from src.services.user_service import UserService

user_service = UserService()


def handle_login(username: str, password: str) -> dict:
    """
    Handles POST /login.

    Calls authenticate_user() to verify credentials and issue a token.
    """
    token = authenticate_user(username, password)
    if token is None:
        return {"status": 401, "error": "Invalid username or password"}
    return {"status": 200, "token": token}


def handle_register(username: str, password: str) -> dict:
    """Handles POST /register by delegating to UserService."""
    user_id = user_service.create_user(username, password)
    return {"status": 201, "user_id": user_id}


def handle_refresh_token(old_token: str) -> dict:
    """Handles POST /refresh. Currently a placeholder for Phase 1 testing."""
    return {"status": 501, "error": "Not implemented yet"}
