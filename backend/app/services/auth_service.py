import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.auth import AuthResponse, UserLogin, UserOut, UserRegister


logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt directly.
    The password is guaranteed to be <= 72 bytes by Pydantic validation.
    """
    pwd_bytes = password.encode("utf-8")
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plain-text password against stored hash.
    """
    pwd_bytes = plain_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, password_hash.encode("utf-8"))


def create_access_token(user: User) -> str:
    """
    Create JWT access token for authenticated user.
    """
    expire_at = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expire_at,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


async def register_user(
    db: AsyncSession,
    payload: UserRegister,
) -> AuthResponse:
    """
    Register a new user and return user data with access token.
    """
    email = payload.email.lower()

    try:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while checking existing user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    try:
        password_hash = hash_password(payload.password)
    except Exception:
        logger.exception("Failed to hash password during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    user = User(
        email=email,
        password_hash=password_hash,
        name=payload.name.strip(),
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while registering user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    try:
        access_token = create_access_token(user)
    except Exception:
        logger.exception("Failed to create access token during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return AuthResponse(
        user=UserOut.model_validate(user),
        access_token=access_token,
    )


async def authenticate_user(
    db: AsyncSession,
    payload: UserLogin,
) -> AuthResponse:
    """
    Authenticate user by email and password, then return JWT.
    """
    email = payload.email.lower()

    try:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while authenticating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    try:
        password_is_valid = verify_password(
            payload.password,
            user.password_hash,
        )
    except Exception:
        logger.exception("Unexpected error during password verification")
        password_is_valid = False

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    try:
        access_token = create_access_token(user)
    except Exception:
        logger.exception("Failed to create access token during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return AuthResponse(
        user=UserOut.model_validate(user),
        access_token=access_token,
    )