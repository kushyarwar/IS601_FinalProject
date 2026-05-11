"""
User management routes: profile, password change, self-delete.

All routes require a valid JWT and are strictly self-scoped — users can
only read and modify their own data. There is no route that exposes
another user's profile, email, or account details.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password
from app.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/profile", response_model=schemas.UserRead)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    """Return the authenticated user's own profile."""
    return current_user


@router.put("/me/profile", response_model=schemas.UserRead)
def update_my_profile(
    update: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update the authenticated user's username, email, or bio."""
    if update.username and update.username != current_user.username:
        conflict = db.query(models.User).filter(
            models.User.username == update.username
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = update.username

    if update.email and update.email != current_user.email:
        conflict = db.query(models.User).filter(
            models.User.email == update.email
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = update.email

    if update.bio is not None:
        current_user.bio = update.bio

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password", status_code=200)
def change_password(
    payload: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Change the authenticated user's password after verifying the current one."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/{user_id}", response_model=schemas.UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return a user's profile. Users may only retrieve their own account."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own account")
    return current_user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a user account. Users may only delete their own account."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
