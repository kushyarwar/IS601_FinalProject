from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, get_db
from app import models, schemas
from app.auth import hash_password, verify_password
from app.calculator import CalculationFactory, OperationType
from app.jwt_utils import create_token, decode_token
from app.reports import get_user_summary

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calculator API - Final Project", version="7.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
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


# ── Root redirect ──────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/login.html")


# ── Auth Routes ────────────────────────────────────────────────────────────

@app.post("/register", response_model=schemas.RegisterResponse, status_code=201)
@app.post("/users/register", response_model=schemas.RegisterResponse, status_code=201)
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


@app.post("/login", response_model=schemas.LoginResponse)
@app.post("/users/login", response_model=schemas.LoginResponse)
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


# ── User Management ────────────────────────────────────────────────────────

@app.get("/users/", response_model=List[schemas.UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


# ── Profile Feature ────────────────────────────────────────────────────────

@app.get("/users/me/profile", response_model=schemas.UserRead)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.put("/users/me/profile", response_model=schemas.UserRead)
def update_my_profile(
    update: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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


@app.post("/users/me/change-password", status_code=200)
def change_password(
    payload: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


# ── Calculation Routes (BREAD) ─────────────────────────────────────────────

@app.get("/calculations/", response_model=List[schemas.CalculationRead])
@app.get("/calculations", response_model=List[schemas.CalculationRead])
def browse_calculations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Calculation)
        .filter(models.Calculation.user_id == current_user.id)
        .order_by(models.Calculation.id.desc())
        .all()
    )


@app.get("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def read_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id,
    ).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc


@app.put("/calculations/{calc_id}", response_model=schemas.CalculationRead)
@app.patch("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def edit_calculation(
    calc_id: int,
    update: schemas.CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id,
    ).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    new_a = update.a if update.a is not None else calc.a
    new_b = update.b if update.b is not None else calc.b
    new_type_str = update.type.value if update.type is not None else calc.type
    new_type = OperationType(new_type_str)

    if new_type == OperationType.Divide and new_b == 0:
        raise HTTPException(status_code=422, detail="Division by zero is not allowed")
    if new_type == OperationType.Modulus and new_b == 0:
        raise HTTPException(status_code=422, detail="Modulus by zero is not allowed")

    calc.a = new_a
    calc.b = new_b
    calc.type = new_type_str
    calc.result = CalculationFactory.compute(new_type, new_a, new_b)

    db.commit()
    db.refresh(calc)
    return calc


@app.post("/calculations/", response_model=schemas.CalculationRead, status_code=201)
@app.post("/calculations", response_model=schemas.CalculationRead, status_code=201)
def add_calculation(
    calc: schemas.CalculationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = CalculationFactory.compute(calc.type, calc.a, calc.b)
    db_calc = models.Calculation(
        a=calc.a,
        b=calc.b,
        type=calc.type.value,
        result=result,
        user_id=current_user.id,
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc


@app.delete("/calculations/{calc_id}", status_code=204)
def delete_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id,
    ).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()


# ── Reports Feature ────────────────────────────────────────────────────────

@app.get("/reports/summary", response_model=schemas.ReportSummary)
def report_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_user_summary(current_user.id, db)


# ── Join Query ─────────────────────────────────────────────────────────────

@app.get("/calculations/join/all", response_model=List[schemas.CalculationWithUser])
def calculations_with_users(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Calculation, models.User.username)
        .join(models.User, models.Calculation.user_id == models.User.id)
        .all()
    )
    return [schemas.CalculationWithUser(
        username=username,
        a=calc.a,
        b=calc.b,
        type=calc.type,
        result=calc.result,
    ) for calc, username in rows]


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
