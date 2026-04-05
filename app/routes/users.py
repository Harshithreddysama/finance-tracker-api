from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate, UserResponse, UserLogin, TokenResponse
from app.services import user_service
from app.middleware.auth_middleware import get_current_user, require_admin
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return user_service.register_user(db, data)


@router.post("/register/privileged", response_model=UserResponse, status_code=201)
def register_privileged(data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return user_service.register_user(db, data, requesting_user=current_user)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    return user_service.login_user(db, data.username, data.password)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return user_service.get_all_users(db, current_user)


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return user_service.delete_user(db, user_id, current_user)
