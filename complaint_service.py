from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.complaint import (
    Complaint,
    ComplaintStatus,
)
from models.complaint_history import ComplaintHistory
from models.connection import Connection
from models.customer import Customer
from models.user import User
from repositories.complaint_history_repository import (
    ComplaintHistoryRepository,
)
from repositories.complaint_repository import ComplaintRepository
from schemas.complaint import (
    ComplaintAssign,
    ComplaintCreate,
    ComplaintStatusUpdate,
)


class ComplaintService:

    def __init__(self):
        self.complaint_repository = ComplaintRepository()
        self.history_repository = ComplaintHistoryRepository()

    def create_complaint(
        self,
        db: Session,
        data: ComplaintCreate,
    ) -> Complaint:

        customer = db.get(
            Customer,
            data.customer_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        connection = db.get(
            Connection,
            data.connection_id,
        )

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        if connection.customer_id != data.customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Connection does not belong to the customer"
                ),
            )

        complaint = Complaint(
            customer_id=data.customer_id,
            connection_id=data.connection_id,
            complaint_type=data.complaint_type,
            description=data.description,
            priority=data.priority,
            assigned_to=None,
            status=ComplaintStatus.OPEN,
        )

        complaint = self.complaint_repository.create(
            db,
            complaint,
        )

        history = ComplaintHistory(
            complaint_id=complaint.id,
            action="Created",
            old_value=None,
            new_value=ComplaintStatus.OPEN,
            changed_by=None,
        )

        self.history_repository.create(
            db,
            history,
        )

        return complaint

    # ========================================================
    # LEVEL 13 - FILTERING / PAGINATION / SORTING
    # ========================================================

    def get_all_complaints(
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
    ):

        return self.complaint_repository.get_all(
            db=db,
            priority=priority,
            status=status,
            complaint_type=complaint_type,
            assigned_to=assigned_to,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_complaint(
        self,
        db: Session,
        complaint_id: int,
    ) -> Complaint:

        complaint = self.complaint_repository.get_by_id(
            db,
            complaint_id,
        )

        if complaint is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found",
            )

        return complaint

    def assign_complaint(
        self,
        db: Session,
        complaint_id: int,
        data: ComplaintAssign,
    ) -> Complaint:

        complaint = self.get_complaint(
            db,
            complaint_id,
        )

        technician = db.get(
            User,
            data.technician_id,
        )

        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician not found",
            )

        if technician.role != "Technician":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a technician",
            )

        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Technician is not available",
            )

        old_assigned_to = complaint.assigned_to

        complaint.assigned_to = technician.id

        if complaint.status == ComplaintStatus.OPEN:
            old_status = complaint.status
            complaint.status = ComplaintStatus.ASSIGNED

            self.complaint_repository.update(
                db,
                complaint,
            )

            history = ComplaintHistory(
                complaint_id=complaint.id,
                action="Status Changed",
                old_value=old_status,
                new_value=ComplaintStatus.ASSIGNED,
                changed_by=technician.id,
            )

            self.history_repository.create(
                db,
                history,
            )
        else:
            self.complaint_repository.update(
                db,
                complaint,
            )

        history = ComplaintHistory(
            complaint_id=complaint.id,
            action="Assigned",
            old_value=(
                str(old_assigned_to)
                if old_assigned_to is not None
                else None
            ),
            new_value=str(technician.id),
            changed_by=technician.id,
        )

        self.history_repository.create(
            db,
            history,
        )

        return complaint

    def update_status(
        self,
        db: Session,
        complaint_id: int,
        data: ComplaintStatusUpdate,
    ) -> Complaint:

        complaint = self.get_complaint(
            db,
            complaint_id,
        )

        old_status = complaint.status

        if old_status == data.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complaint already has this status",
            )

        complaint.status = data.status

        self.complaint_repository.update(
            db,
            complaint,
        )

        history = ComplaintHistory(
            complaint_id=complaint.id,
            action="Status Changed",
            old_value=old_status,
            new_value=data.status,
            changed_by=complaint.assigned_to,
        )

        self.history_repository.create(
            db,
            history,
        )

        return complaint

    def get_history(
        self,
        db: Session,
        complaint_id: int,
    ) -> list[ComplaintHistory]:

        self.get_complaint(
            db,
            complaint_id,
        )

        return self.history_repository.get_by_complaint(
            db,
            complaint_id,
        )