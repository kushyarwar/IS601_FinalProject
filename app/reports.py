"""
Report aggregation logic for the usage statistics dashboard.

All queries are scoped to a single user so no cross-user data leaks
into the summary response.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models


def get_user_summary(user_id: int, db: Session) -> dict:
    """
    Build a usage summary for the given user.

    Returns:
        total_calculations: count of all calculations for this user
        most_used_operation: the operation type with the highest count, or None
        average_result: mean of all result values rounded to 4 decimals, or None
        last_calculation: the most recently created Calculation ORM object, or None
        operation_counts: dict mapping each operation name to its count
    """
    total = db.query(func.count(models.Calculation.id)).filter(
        models.Calculation.user_id == user_id
    ).scalar() or 0

    avg_result = db.query(func.avg(models.Calculation.result)).filter(
        models.Calculation.user_id == user_id
    ).scalar()

    # Group by operation type to build the breakdown chart
    counts_rows = (
        db.query(models.Calculation.type, func.count(models.Calculation.id))
        .filter(models.Calculation.user_id == user_id)
        .group_by(models.Calculation.type)
        .all()
    )
    operation_counts = {row[0]: row[1] for row in counts_rows}

    most_used = max(operation_counts, key=operation_counts.get) if operation_counts else None

    last_calc = (
        db.query(models.Calculation)
        .filter(models.Calculation.user_id == user_id)
        .order_by(models.Calculation.id.desc())
        .first()
    )

    return {
        "total_calculations": total,
        "most_used_operation": most_used,
        "average_result": round(avg_result, 4) if avg_result is not None else None,
        "last_calculation": last_calc,
        "operation_counts": operation_counts,
    }
