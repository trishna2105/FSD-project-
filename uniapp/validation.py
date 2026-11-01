import re

from uniapp.errors import ValidationError


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9_+-]+(?:\.[A-Za-z0-9_+-]+)*@university\.com")
PASSWORD_PATTERN = re.compile(r"[A-Z][A-Za-z]{4,}[0-9]{3,}")


def _validate_text(value: str, field: str) -> None:
    if not isinstance(value, str):
        raise ValidationError(field, "invalid_type")
    if not value or value.isspace():
        raise ValidationError(field, "required")


def normalize_email(email: str) -> str:
    """Use the same account key for registration, login and duplicate checks."""
    _validate_text(email, "email")
    return email.strip().lower()


def validate_email(email: str) -> None:
    normalized = normalize_email(email)
    if EMAIL_PATTERN.fullmatch(normalized) is None:
        raise ValidationError("email", "invalid_format")


def validate_password(password: str) -> None:
    """Require at least five letters starting uppercase, then at least three digits."""
    _validate_text(password, "password")
    if PASSWORD_PATTERN.fullmatch(password) is None:
        raise ValidationError("password", "invalid_format")


def validate_name(name: str) -> None:
    _validate_text(name, "name")
