"""
Reports routes providing per-user usage statistics.

The summary endpoint aggregates calculation counts, most-used operation,
average result, and last calculation — all scoped to the authenticated user.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.reports import get_user_summary
from app.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary", response_model=schemas.ReportSummary)
def report_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_user_summary(current_user.id, db)
