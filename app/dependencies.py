import os
import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.jwt_utils import decode_token

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "supersecretjwtkey-finalproject-is601-changeme"

if os.getenv("JWT_SECRET", _DEFAULT_SECRET) == _DEFAULT_SECRET:
    logger.warning(
        "JWT_SECRET is using the default insecure value. "
        "Set the JWT_SECRET environment variable in production."
    )

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization token required")
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
