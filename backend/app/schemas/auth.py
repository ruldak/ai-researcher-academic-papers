from uuid import UUID

from pydantic import BaseModel, field_validator, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """
    Request schema for user registration.
    """

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_byte_length(cls, value: str) -> str:
        """
        Bcrypt has a hard limit of 72 bytes. 
        Reject passwords that exceed this limit instead of silently truncating them.
        """
        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "Password is too long. It must not exceed 72 bytes. "
                "Please use a shorter password or fewer special characters/emojis."
            )
        return value


class UserLogin(BaseModel):
    """
    Request schema for user login.
    """

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_byte_length(cls, value: str) -> str:
        """
        Bcrypt has a hard limit of 72 bytes. 
        Reject passwords that exceed this limit instead of silently truncating them.
        """
        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "Password is too long. It must not exceed 72 bytes. "
                "Please use a shorter password or fewer special characters/emojis."
            )
        return value


class UserOut(BaseModel):
    """
    Public user representation returned by auth endpoints.
    """

    id: UUID
    email: EmailStr
    name: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """
    Response schema containing user data and JWT access token.
    """

    user: UserOut
    access_token: str
    token_type: str = "bearer"