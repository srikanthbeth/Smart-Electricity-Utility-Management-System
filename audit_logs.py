from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.audit_log import AuditLogResponse
from services.audit_log_service import AuditLogService
from utils.dependencies import require_roles
from utils.enums import UserRole


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
):
    return AuditLogService.get_all_logs(db)


@router.get(
    "/user/{user_id}",
    response_model=list[AuditLogResponse],
)
def get_user_audit_logs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
):
    return AuditLogService.get_user_logs(
        db,
        user_id,
    )