from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import FinancialSummary, CategoryBreakdown
from app.services import analytics_service
from app.middleware.auth_middleware import require_viewer, require_analyst
from app.models.transaction import TransactionType
from app.models.user import User

router = APIRouter()


@router.get("/summary", response_model=FinancialSummary)
def financial_summary(db: Session = Depends(get_db), current_user: User = Depends(require_viewer)):
    return analytics_service.get_financial_summary(db, current_user)


@router.get("/category-breakdown", response_model=list[CategoryBreakdown])
def category_breakdown(
    type: TransactionType = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    return analytics_service.get_category_report(db, current_user, type)
