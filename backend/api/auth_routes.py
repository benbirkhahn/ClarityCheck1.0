from datetime import timedelta
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from sqlmodel import select
from pydantic import BaseModel, EmailStr

from backend.core.auth import create_access_token, get_password_hash, verify_password
from backend.core.config import settings
from backend.core.database import get_session
from backend.core.models import DBUser

def _is_admin_email(email: str) -> bool:
    return email.lower() in settings.ADMIN_EMAILS

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    is_active: bool

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    statement = select(DBUser).where(DBUser.email == email)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_optional_current_user(token: Annotated[Optional[str], Depends(oauth2_scheme)] = None, session: AsyncSession = Depends(get_session)):
    """
    Return user if token is valid, otherwise None.
    Do NOT raise 401.
    """
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
        
    statement = select(DBUser).where(DBUser.email == email)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    # Check if user exists
    statement = select(DBUser).where(DBUser.email == user_in.email)
    result = await session.execute(statement)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = DBUser(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_admin=_is_admin_email(user_in.email)
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: AsyncSession = Depends(get_session)):
    # OAuth2PasswordRequestForm expects username (which is email for us)
    statement = select(DBUser).where(DBUser.email == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Auto-promote to admin if email is in ADMIN_EMAILS
    if _is_admin_email(user.email) and not user.is_admin:
        user.is_admin = True
        session.add(user)
        await session.commit()
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[DBUser, Depends(get_current_user)]):
    return current_user
