from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from models.complaint import Complaint


class ComplaintRepository:

    def create(
        self,
        db: Session,
        complaint: Complaint,
    ) -> Complaint:
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        return complaint

    def get_by_id(
        self,
        db: Session,
        complaint_id: int,
    ) -> Complaint | None:
        return db.get(
            Complaint,
            complaint_id,
        )

    def get_all(
        self,
        db: Session,
        priority: str | None = None,
        status: str | None = None,
        complaint_type: str | None = None,
        assigned_to: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> tuple[list[Complaint], int, int]:

        statement = select(Complaint)

        # PRIORITY FILTER
        if priority:
            statement = statement.where(
                Complaint.priority == priority
            )

        # STATUS FILTER
        if status:
            statement = statement.where(
                Complaint.status == status
            )

        # COMPLAINT TYPE FILTER
        if complaint_type:
            statement = statement.where(
                Complaint.complaint_type
                == complaint_type
            )

        # ASSIGNED TECHNICIAN FILTER
        if assigned_to is not None:
            statement = statement.where(
                Complaint.assigned_to
                == assigned_to
            )

        # SORTING
        allowed_sort_columns = {
            "id": Complaint.id,
            "customer_id": Complaint.customer_id,
            "connection_id": Complaint.connection_id,
            "complaint_type": Complaint.complaint_type,
            "priority": Complaint.priority,
            "assigned_to": Complaint.assigned_to,
            "status": Complaint.status,
        }

        sort_column = allowed_sort_columns.get(
            sort_by,
            Complaint.id,
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                asc(sort_column),
                asc(Complaint.id),
            )
        else:
            statement = statement.order_by(
                desc(sort_column),
                desc(Complaint.id),
            )

        # TOTAL COUNT
        count_statement = select(
            func.count()
        ).select_from(
            statement.order_by(None).subquery()
        )

        total = db.execute(
            count_statement
        ).scalar_one()

        # PAGINATION
        offset = (page - 1) * limit

        statement = statement.offset(
            offset
        ).limit(
            limit
        )

        complaints = list(
            db.scalars(statement).all()
        )

        total_pages = (
            (total + limit - 1) // limit
            if total > 0
            else 0
        )

        return (
            complaints,
            total,
            total_pages,
        )

    def update(
        self,
        db: Session,
        complaint: Complaint,
    ) -> Complaint:
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        return complaint