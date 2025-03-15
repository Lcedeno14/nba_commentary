from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import aiosqlite
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.schemas.user import User, UserCreate, Token
from app.db.session import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        "SELECT * FROM users WHERE username = ?",
        (form_data.username,)
    ) as cursor:
        user = await cursor.fetchone()
    
    if not user or not pwd_context.verify(form_data.password, user[4]):  # index 4 is hashed_password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user[1]})  # index 1 is username
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(
    user: UserCreate,
    db: aiosqlite.Connection = Depends(get_db)
):
    # Check if username already exists
    async with db.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (user.username, user.email)
    ) as cursor:
        if await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
    
    hashed_password = pwd_context.hash(user.password)
    
    async with db.execute(
        """
        INSERT INTO users (username, email, full_name, hashed_password)
        VALUES (?, ?, ?, ?)
        """,
        (user.username, user.email, user.full_name, hashed_password)
    ):
        await db.commit()
    
    return {
        "id": db.last_row_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": True
    } 