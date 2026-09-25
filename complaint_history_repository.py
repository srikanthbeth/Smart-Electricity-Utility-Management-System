from sqlalchemy import select
from sqlalchemy.orm import Session

from models.complaint_history import ComplaintHistory


class ComplaintHistoryRepository:

    def create(
        self,
        db: Session,
        history: ComplaintHistory,
    ) -> ComplaintHistory:
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    def get_by_complaint(
        self,
        db: Session,
        complaint_id: int,
    ) -> list[ComplaintHistory]:
        statement = (
            select(ComplaintHistory)
            .where(
                ComplaintHistory.complaint_id == complaint_id
            )
            .order_by(
                ComplaintHistory.id.asc()
            )
        )

        return list(
            db.scalars(statement).all()
        )