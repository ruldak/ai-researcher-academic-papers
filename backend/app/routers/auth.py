from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import AuthResponse, UserLogin, UserOut, UserRegister
from app.services import auth_service
from app.utils.dependencies import get_current_user, get_db


router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user and return JWT access token.
    """
    return await auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=AuthResponse,
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Login with email and password, then return JWT access token.
    """
    return await auth_service.authenticate_user(db, payload)


@router.get(
    "/me",
    response_model=UserOut,
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current authenticated user profile.
    """
    return current_user