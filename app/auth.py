"""
Password hashing and verification using bcrypt.

bcrypt automatically generates a unique salt per hash, so two calls
to hash_password with the same input will produce different hashes.
This prevents pre-computation (rainbow table) attacks.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with bcrypt and return the digest as a string."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
