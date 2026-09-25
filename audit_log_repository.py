from sqlalchemy import select
from sqlalchemy.orm import Session

from models.audit_log import AuditLog


class AuditLogRepository:

    @staticmethod
    def create(
        db: Session,
        audit_log: AuditLog,
    ) -> AuditLog:
        db.add(audit_log)
        db.flush()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id
            )
            .order_by(
                AuditLog.created_at.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )