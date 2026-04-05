from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, PaginatedTransactions
from app.services import transaction_service
from app.middleware.auth_middleware import get_current_user, require_viewer
from app.models.transaction import TransactionType
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.create_transaction(db, data, current_user)


@router.get("/", response_model=PaginatedTransactions)
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_viewer),
    type: Optional[TransactionType] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    return transaction_service.get_transactions(db, current_user, type, category, start_date, end_date, page, page_size)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_viewer)):
    return transaction_service.get_transaction_by_id(db, transaction_id, current_user)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, data: TransactionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.update_transaction(db, transaction_id, data, current_user)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.delete_transaction(db, transaction_id, current_user)
