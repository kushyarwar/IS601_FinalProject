"""
JWT token creation and decoding using HS256.

Tokens expire after EXPIRE_MINUTES minutes. The secret is read from the
JWT_SECRET environment variable; a startup warning is emitted by
app/dependencies.py if the default development value is still in use.
"""
import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretjwtkey-finalproject-is601-changeme")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30


def create_token(user_id: int, email: str) -> str:
    """Create a signed JWT containing the user's id and email."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises ValueError on invalid or expired tokens."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
