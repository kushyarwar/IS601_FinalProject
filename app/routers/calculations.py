"""
Calculation BREAD routes (Browse, Read, Edit, Add, Delete).

Every route is strictly scoped to the authenticated user — queries always
filter by user_id so users can never read or modify each other's calculations.
Unauthenticated requests receive 401; cross-user resource requests receive
404 to avoid leaking whether a resource exists.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.calculator import CalculationFactory, OperationType
from app.dependencies import get_current_user

router = APIRouter(prefix="/calculations", tags=["Calculations"])


@router.get("/", response_model=List[schemas.CalculationRead])
@router.get("", response_model=List[schemas.CalculationRead])
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


@router.get("/{calc_id}", response_model=schemas.CalculationRead)
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


@router.put("/{calc_id}", response_model=schemas.CalculationRead)
@router.patch("/{calc_id}", response_model=schemas.CalculationRead)
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


@router.post("/", response_model=schemas.CalculationRead, status_code=201)
@router.post("", response_model=schemas.CalculationRead, status_code=201)
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


@router.delete("/{calc_id}", status_code=204)
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
