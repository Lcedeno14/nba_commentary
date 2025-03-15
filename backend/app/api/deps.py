from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
import aiosqlite

from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: aiosqlite.Connection = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    async with db.execute(
        "SELECT * FROM users WHERE username = ?", 
        (token_data.username,)
    ) as cursor:
        user = await cursor.fetchone()
        
    if user is None:
        raise credentials_exception
        
    return {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "full_name": user[3],
        "is_active": bool(user[5])
    } 