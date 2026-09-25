from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db

from schemas.complaint import (
    ComplaintAssign,
    ComplaintCreate,
    ComplaintHistoryResponse,
    ComplaintResponse,
    ComplaintStatusUpdate,
)

from services.complaint_service import ComplaintService


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"],
)

service = ComplaintService()


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
):
    return service.create_complaint(
        db,
        data,
    )


@router.get("")
def get_complaints(
    priority: str | None = Query(
        default=None,
        description="Filter by complaint priority",
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by complaint status",
    ),
    complaint_type: str | None = Query(
        default=None,
        description="Filter by complaint type",
    ),
    assigned_to: int | None = Query(
        default=None,
        description="Filter by assigned technician ID",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of complaints per page",
    ),
    sort_by: str = Query(
        default="id",
        description="Field used for sorting",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    db: Session = Depends(get_db),
):
    complaints, total, total_pages = (
        service.get_all_complaints(
            db=db,
            priority=priority,
            status=status_filter,
            complaint_type=complaint_type,
            assigned_to=assigned_to,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )

    return {
        "items": complaints,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    return service.get_complaint(
        db,
        complaint_id,
    )


@router.put(
    "/{complaint_id}/assign",
    response_model=ComplaintResponse,
)
def assign_complaint(
    complaint_id: int,
    data: ComplaintAssign,
    db: Session = Depends(get_db),
):
    return service.assign_complaint(
        db,
        complaint_id,
        data,
    )


@router.put(
    "/{complaint_id}/status",
    response_model=ComplaintResponse,
)
def update_complaint_status(
    complaint_id: int,
    data: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
):
    return service.update_status(
        db,
        complaint_id,
        data,
    )


@router.get(
    "/{complaint_id}/history",
    response_model=list[ComplaintHistoryResponse],
)
def get_complaint_history(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    return service.get_history(
        db,
        complaint_id,
    )