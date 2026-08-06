import logging
from collections.abc import AsyncGenerator
from uuid import UUID as PyUUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User


logger = logging.getLogger(__name__)

# HTTP Bearer authentication scheme.
# auto_error=False allows custom 401 handling.
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session for request-scoped operations.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate JWT token from Authorization header and return current user.
    """
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized_exception

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        logger.debug("Invalid JWT token received")
        raise unauthorized_exception

    subject = payload.get("sub")
    if subject is None:
        logger.debug("JWT token has no subject")
        raise unauthorized_exception

    try:
        user_id = PyUUID(subject)
    except ValueError:
        logger.debug("JWT subject is not a valid UUID")
        raise unauthorized_exception

    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
    except SQLAlchemyError:
        logger.exception("Database error while fetching current user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    user = result.scalar_one_or_none()

    if user is None:
        raise unauthorized_exception

    return user