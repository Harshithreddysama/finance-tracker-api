from sqlalchemy.orm import Session
from collections import defaultdict
from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole


def get_financial_summary(db: Session, current_user: User) -> dict:
    query = db.query(Transaction)
    if current_user.role != UserRole.admin:
        query = query.filter(Transaction.user_id == current_user.id)
    all_transactions = query.order_by(Transaction.date.desc()).all()
    total_income = sum(t.amount for t in all_transactions if t.type == TransactionType.income)
    total_expenses = sum(t.amount for t in all_transactions if t.type == TransactionType.expense)
    current_balance = round(total_income - total_expenses, 2)
    income_by_category = _group_by_category([t for t in all_transactions if t.type == TransactionType.income])
    expense_by_category = _group_by_category([t for t in all_transactions if t.type == TransactionType.expense])
    monthly_totals = _compute_monthly_totals(all_transactions)
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "current_balance": current_balance,
        "total_transactions": len(all_transactions),
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
        "monthly_totals": monthly_totals,
        "recent_transactions": all_transactions[:5],
    }


def _group_by_category(transactions: list) -> list:
    category_data = defaultdict(lambda: {"total": 0.0, "count": 0})
    for t in transactions:
        category_data[t.category]["total"] += t.amount
        category_data[t.category]["count"] += 1
    return [
        {"category": cat, "total": round(data["total"], 2), "count": data["count"]}
        for cat, data in sorted(category_data.items(), key=lambda x: x[1]["total"], reverse=True)
    ]


def _compute_monthly_totals(transactions: list) -> list:
    monthly = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        if t.type == TransactionType.income:
            monthly[key]["income"] += t.amount
        else:
            monthly[key]["expenses"] += t.amount
    result = []
    for month in sorted(monthly.keys(), reverse=True):
        income = round(monthly[month]["income"], 2)
        expenses = round(monthly[month]["expenses"], 2)
        result.append({"month": month, "income": income, "expenses": expenses, "net": round(income - expenses, 2)})
    return result


def get_category_report(db: Session, current_user: User, transaction_type: TransactionType) -> list:
    query = db.query(Transaction).filter(Transaction.type == transaction_type)
    if current_user.role != UserRole.admin:
        query = query.filter(Transaction.user_id == current_user.id)
    return _group_by_category(query.all())
