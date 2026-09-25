from sqlalchemy.orm import Session

from models.user import User
from repositories.user_repository import UserRepository
from schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)
from utils.exceptions import bad_request, conflict, unauthorized
from utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:

    @staticmethod
    def register(
        db: Session,
        data: RegisterRequest,
    ) -> User:

        existing_user = UserRepository.get_by_email(
            db,
            data.email,
        )

        if existing_user:
            raise conflict(
                "Email is already registered"
            )

        user = User(
            full_name=data.full_name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role.value,
            is_active=True,
        )

        return UserRepository.create(
            db,
            user,
        )

    @staticmethod
    def login(
        db: Session,
        data: LoginRequest,
    ) -> tuple[str, str]:

        user = UserRepository.get_by_email(
            db,
            data.email,
        )

        if not user:
            raise unauthorized(
                "Invalid email or password"
            )

        if not verify_password(
            data.password,
            user.hashed_password,
        ):
            raise unauthorized(
                "Invalid email or password"
            )

        if not user.is_active:
            raise unauthorized(
                "User account is inactive"
            )

        access_token = create_access_token(
            user.id,
            user.role,
        )

        refresh_token = create_refresh_token(
            user.id,
            user.role,
        )

        return access_token, refresh_token

    @staticmethod
    def refresh(
        db: Session,
        refresh_token: str,
    ) -> tuple[str, str]:

        try:
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise unauthorized(
                    "Refresh token required"
                )

            user_id = payload.get("sub")

            if not user_id:
                raise unauthorized(
                    "Invalid refresh token"
                )

            user = UserRepository.get_by_id(
                db,
                int(user_id),
            )

            if not user:
                raise unauthorized(
                    "User not found"
                )

            if not user.is_active:
                raise unauthorized(
                    "User account is inactive"
                )

            new_access_token = create_access_token(
                user.id,
                user.role,
            )

            new_refresh_token = create_refresh_token(
                user.id,
                user.role,
            )

            return (
                new_access_token,
                new_refresh_token,
            )

        except Exception as exc:
            if hasattr(exc, "status_code"):
                raise

            raise unauthorized(
                "Invalid or expired refresh token"
            )

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:

        if not verify_password(
            data.current_password,
            user.hashed_password,
        ):
            raise bad_request(
                "Current password is incorrect"
            )

        if data.current_password == data.new_password:
            raise bad_request(
                "New password must be different"
            )

        user.hashed_password = hash_password(
            data.new_password
        )

        UserRepository.update(
            db,
            user,
        )