from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.auth import hash_password, verify_password, create_access_token
from app.schemas import UserCreate


def register_user(db: Session, data: UserCreate, requesting_user: User = None) -> User:
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username '{data.username}' is already taken.")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{data.email}' is already registered.")
    assigned_role = data.role
    if assigned_role in (UserRole.analyst, UserRole.admin):
        if requesting_user is None or requesting_user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can assign Analyst or Admin roles.")
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=assigned_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": user}


def get_all_users(db: Session, current_user: User) -> list:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can list all users.")
    return db.query(User).all()


def delete_user(db: Session, user_id: int, current_user: User) -> dict:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can delete users.")
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete their own account.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    db.delete(user)
    db.commit()
    return {"message": f"User '{user.username}' has been deleted successfully."}
