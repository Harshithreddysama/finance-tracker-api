import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_finance.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def create_admin_and_get_token():
    client.post("/api/users/register", json={"username": "testadmin", "email": "testadmin@test.com", "password": "admin123", "role": "viewer"})
    from app.models.user import UserRole, User
    db = TestingSessionLocal()
    u = db.query(User).filter(User.username == "testadmin").first()
    u.role = UserRole.admin
    db.commit()
    db.close()
    resp = client.post("/api/users/login", json={"username": "testadmin", "password": "admin123"})
    return resp.json()["access_token"]


def register_and_login(username, password, role="viewer", admin_token=None):
    if role in ("analyst", "admin") and admin_token:
        client.post("/api/users/register/privileged", json={"username": username, "email": f"{username}@test.com", "password": password, "role": role}, headers={"Authorization": f"Bearer {admin_token}"})
    else:
        client.post("/api/users/register", json={"username": username, "email": f"{username}@test.com", "password": password, "role": "viewer"})
    resp = client.post("/api/users/login", json={"username": username, "password": password})
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestUserRegistration:
    def test_register_viewer_success(self):
        resp = client.post("/api/users/register", json={"username": "testuser", "email": "testuser@test.com", "password": "pass123", "role": "viewer"})
        assert resp.status_code == 201
        assert resp.json()["username"] == "testuser"

    def test_register_duplicate_username(self):
        client.post("/api/users/register", json={"username": "dupuser", "email": "dup@test.com", "password": "pass123", "role": "viewer"})
        resp = client.post("/api/users/register", json={"username": "dupuser", "email": "other@test.com", "password": "pass123", "role": "viewer"})
        assert resp.status_code == 409

    def test_register_invalid_username_too_short(self):
        resp = client.post("/api/users/register", json={"username": "ab", "email": "ab@test.com", "password": "pass123", "role": "viewer"})
        assert resp.status_code == 422

    def test_register_weak_password(self):
        resp = client.post("/api/users/register", json={"username": "validuser", "email": "valid@test.com", "password": "123", "role": "viewer"})
        assert resp.status_code == 422


class TestUserLogin:
    def test_login_success(self):
        client.post("/api/users/register", json={"username": "loginuser", "email": "login@test.com", "password": "secure123", "role": "viewer"})
        resp = client.post("/api/users/login", json={"username": "loginuser", "password": "secure123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        client.post("/api/users/register", json={"username": "wrongpass", "email": "wp@test.com", "password": "correct123", "role": "viewer"})
        resp = client.post("/api/users/login", json={"username": "wrongpass", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):
        resp = client.post("/api/users/login", json={"username": "ghost", "password": "ghost123"})
        assert resp.status_code == 401


class TestTransactions:
    def test_analyst_can_create_transaction(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst1", "analyst123", "analyst", admin_token)
        resp = client.post("/api/transactions/", json={"amount": 5000.00, "type": "income", "category": "Salary"}, headers=auth_headers(token))
        assert resp.status_code == 201
        assert resp.json()["amount"] == 5000.00

    def test_viewer_cannot_create_transaction(self):
        token = register_and_login("viewer1", "viewer123", "viewer")
        resp = client.post("/api/transactions/", json={"amount": 1000.00, "type": "expense", "category": "Food"}, headers=auth_headers(token))
        assert resp.status_code == 403

    def test_negative_amount_rejected(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst2", "analyst123", "analyst", admin_token)
        resp = client.post("/api/transactions/", json={"amount": -500.00, "type": "expense", "category": "Food"}, headers=auth_headers(token))
        assert resp.status_code == 422

    def test_zero_amount_rejected(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst3", "analyst123", "analyst", admin_token)
        resp = client.post("/api/transactions/", json={"amount": 0, "type": "income", "category": "Other"}, headers=auth_headers(token))
        assert resp.status_code == 422

    def test_viewer_can_list_transactions(self):
        token = register_and_login("viewer2", "viewer123", "viewer")
        resp = client.get("/api/transactions/", headers=auth_headers(token))
        assert resp.status_code == 200
        assert "transactions" in resp.json()

    def test_filter_by_type(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst4", "analyst123", "analyst", admin_token)
        headers = auth_headers(token)
        client.post("/api/transactions/", json={"amount": 3000, "type": "income", "category": "Salary"}, headers=headers)
        client.post("/api/transactions/", json={"amount": 500, "type": "expense", "category": "Food"}, headers=headers)
        resp = client.get("/api/transactions/?type=income", headers=headers)
        assert resp.status_code == 200
        assert all(t["type"] == "income" for t in resp.json()["transactions"])

    def test_update_transaction(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst5", "analyst123", "analyst", admin_token)
        headers = auth_headers(token)
        create_resp = client.post("/api/transactions/", json={"amount": 1000, "type": "income", "category": "Freelance"}, headers=headers)
        tid = create_resp.json()["id"]
        update_resp = client.put(f"/api/transactions/{tid}", json={"amount": 1500}, headers=headers)
        assert update_resp.status_code == 200
        assert update_resp.json()["amount"] == 1500.00

    def test_unauthenticated_access_denied(self):
        resp = client.get("/api/transactions/")
        assert resp.status_code == 403


class TestAnalytics:
    def test_summary_accessible_to_viewer(self):
        token = register_and_login("viewer3", "viewer123", "viewer")
        resp = client.get("/api/analytics/summary", headers=auth_headers(token))
        assert resp.status_code == 200
        assert "total_income" in resp.json()

    def test_category_breakdown_requires_analyst(self):
        token = register_and_login("viewer4", "viewer123", "viewer")
        resp = client.get("/api/analytics/category-breakdown?type=expense", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_category_breakdown_accessible_to_analyst(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst6", "analyst123", "analyst", admin_token)
        resp = client.get("/api/analytics/category-breakdown?type=expense", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_summary_balance_calculation(self):
        admin_token = create_admin_and_get_token()
        token = register_and_login("analyst7", "analyst123", "analyst", admin_token)
        headers = auth_headers(token)
        client.post("/api/transactions/", json={"amount": 10000, "type": "income", "category": "Salary"}, headers=headers)
        client.post("/api/transactions/", json={"amount": 3000, "type": "expense", "category": "Rent"}, headers=headers)
        resp = client.get("/api/analytics/summary", headers=headers)
        assert resp.json()["current_balance"] == 7000.00
