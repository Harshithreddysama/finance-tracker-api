from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType
from app.auth import hash_password


def seed_data():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        admin = User(username="admin", email="admin@financetracker.com", hashed_password=hash_password("admin123"), role=UserRole.admin)
        analyst = User(username="analyst", email="analyst@financetracker.com", hashed_password=hash_password("analyst123"), role=UserRole.analyst)
        viewer = User(username="viewer", email="viewer@financetracker.com", hashed_password=hash_password("viewer123"), role=UserRole.viewer)
        db.add_all([admin, analyst, viewer])
        db.commit()
        db.refresh(admin)
        db.refresh(analyst)
        now = datetime.now(timezone.utc)
        transactions = [
            Transaction(amount=85000.00, type=TransactionType.income,  category="Salary",      date=now - timedelta(days=2),  notes="Monthly salary - March 2026", user_id=admin.id),
            Transaction(amount=12000.00, type=TransactionType.income,  category="Freelance",   date=now - timedelta(days=10), notes="Web development project",      user_id=admin.id),
            Transaction(amount=3200.00,  type=TransactionType.expense, category="Rent",        date=now - timedelta(days=5),  notes="March rent payment",           user_id=admin.id),
            Transaction(amount=1500.00,  type=TransactionType.expense, category="Groceries",   date=now - timedelta(days=8),  notes="Monthly groceries",            user_id=admin.id),
            Transaction(amount=800.00,   type=TransactionType.expense, category="Utilities",   date=now - timedelta(days=12), notes="Electricity and internet",     user_id=admin.id),
            Transaction(amount=2500.00,  type=TransactionType.expense, category="Transport",   date=now - timedelta(days=15), notes="Fuel and cab rides",           user_id=admin.id),
            Transaction(amount=5000.00,  type=TransactionType.income,  category="Investments", date=now - timedelta(days=20), notes="Stock dividend payout",        user_id=admin.id),
            Transaction(amount=1200.00,  type=TransactionType.expense, category="Dining",      date=now - timedelta(days=22), notes="Team dinner",                  user_id=admin.id),
            Transaction(amount=55000.00, type=TransactionType.income,  category="Salary",      date=now - timedelta(days=3),  notes="Monthly salary",               user_id=analyst.id),
            Transaction(amount=8000.00,  type=TransactionType.income,  category="Freelance",   date=now - timedelta(days=14), notes="Data analysis contract",       user_id=analyst.id),
            Transaction(amount=2200.00,  type=TransactionType.expense, category="Rent",        date=now - timedelta(days=6),  notes="March rent",                   user_id=analyst.id),
            Transaction(amount=900.00,   type=TransactionType.expense, category="Groceries",   date=now - timedelta(days=9),  notes="Weekly groceries",             user_id=analyst.id),
        ]
        db.add_all(transactions)
        db.commit()
        print("Seed data loaded. admin/admin123, analyst/analyst123, viewer/viewer123")
    except Exception as e:
        db.rollback()
        print(f"Seeding skipped: {e}")
    finally:
        db.close()
