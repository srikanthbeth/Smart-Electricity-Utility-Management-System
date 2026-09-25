from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from repositories.audit_log_repository import (
    AuditLogRepository,
)


class AuditLogService:

    @staticmethod
    def create_log(
        db: Session,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        details: str | None = None,
    ) -> AuditLog:

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

        return AuditLogRepository.create(
            db,
            audit_log,
        )

    @staticmethod
    def get_all_logs(
        db: Session,
    ) -> list[AuditLog]:
        return AuditLogRepository.get_all(db)

    @staticmethod
    def get_user_logs(
        db: Session,
        user_id: int,
    ) -> list[AuditLog]:
        return AuditLogRepository.get_by_user(
            db,
            user_id,
        )