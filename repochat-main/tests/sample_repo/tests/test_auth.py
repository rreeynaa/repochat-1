"""Tests for the sample authentication flow."""

from src.auth.authentication import hash_password, verify_password


def test_hash_password_is_deterministic():
    assert hash_password("secret123") == hash_password("secret123")


def test_verify_password_accepts_correct_password():
    password_hash = hash_password("secret123")
    assert verify_password("secret123", password_hash) is True


def test_verify_password_rejects_wrong_password():
    password_hash = hash_password("secret123")
    assert verify_password("wrong-password", password_hash) is False
