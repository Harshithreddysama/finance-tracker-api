from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import Optional
from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas import TransactionCreate, TransactionUpdate


def create_transaction(db: Session, data: TransactionCreate, current_user: User) -> Transaction:
    if current_user.role not in (UserRole.admin, UserRole.analyst):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins and Analysts can create transactions.")
    transaction = Transaction(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date or datetime.now(timezone.utc),
        notes=data.notes,
        user_id=current_user.id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transactions(db: Session, current_user: User, transaction_type=None, category=None, start_date=None, end_date=None, page=1, page_size=10) -> dict:
    query = db.query(Transaction)
    if current_user.role != UserRole.admin:
        query = query.filter(Transaction.user_id == current_user.id)
    filters = []
    if transaction_type:
        filters.append(Transaction.type == transaction_type)
    if category:
        filters.append(Transaction.category.ilike(f"%{category}%"))
    if start_date:
        filters.append(Transaction.date >= start_date)
    if end_date:
        filters.append(Transaction.date <= end_date)
    if filters:
        query = query.filter(and_(*filters))
    total = query.count()
    transactions = query.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "transactions": transactions}


def get_transaction_by_id(db: Session, transaction_id: int, current_user: User) -> Transaction:
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    if current_user.role != UserRole.admin and transaction.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this transaction.")
    return transaction


def update_transaction(db: Session, transaction_id: int, data: TransactionUpdate, current_user: User) -> Transaction:
    transaction = get_transaction_by_id(db, transaction_id, current_user)
    if current_user.role == UserRole.viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot update transactions.")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    transaction.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction_id: int, current_user: User) -> dict:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can delete transactions.")
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    db.delete(transaction)
    db.commit()
    return {"message": f"Transaction {transaction_id} has been deleted successfully."}
