from datetime import datetime, timedelta
from typing import Optional
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# Конфигурация
# SECRET_KEY генерируется при каждом запуске сервера,
# что инвалидирует все токены после перезапуска приложения
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Схема для извлечения токена из заголовка
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Модель для данных в токене
class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        role: Optional[str] = payload.get("role")
        return TokenData(user_id=user_id, role=role)
    except JWTError:
        return None

# Зависимость для защиты маршрутов
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    return token_data  # содержит user_id и role

# Зависимость для проверки прав администратора
def get_admin_user(current_user: TokenData = Depends(get_current_user)):
    """Dependency для проверки прав администратора"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user