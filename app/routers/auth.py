"""
Authentication routes: user registration and login.

Both endpoints return a JWT on success so the client can immediately
make authenticated requests without a second round-trip.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password
from app.jwt_utils import create_token

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=schemas.RegisterResponse, status_code=201)
@router.post("/users/register", response_model=schemas.RegisterResponse, status_code=201)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    effective_username = user.username or user.email.split("@")[0]
    existing = db.query(models.User).filter(
        (models.User.username == effective_username) | (models.User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    db_user = models.User(
        username=effective_username,
        email=user.email,
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    token = create_token(db_user.id, db_user.email)
    return schemas.RegisterResponse(
        token=token,
        message="Registration successful",
        user=schemas.UserRead.model_validate(db_user),
    )


@router.post("/login", response_model=schemas.LoginResponse)
@router.post("/users/login", response_model=schemas.LoginResponse)
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user.id, user.email)
    return schemas.LoginResponse(
        token=token,
        message="Login successful",
        user=schemas.UserRead.model_validate(user),
    )
