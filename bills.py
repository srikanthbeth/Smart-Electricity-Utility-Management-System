from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db

from schemas.bill import (
    BillCreate,
    BillResponse,
)

from services.bill_service import BillService


router = APIRouter(
    prefix="/bills",
    tags=["Bills"],
)

customer_bill_router = APIRouter(
    prefix="/customers",
    tags=["Customer Bills"],
)

connection_bill_router = APIRouter(
    prefix="/connections",
    tags=["Connection Bills"],
)

service = BillService()


@router.post(
    "/generate",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_bill(
    data: BillCreate,
    db: Session = Depends(get_db),
):
    return service.generate_bill(
        db,
        data,
    )


@router.get("")
def get_bills(
    billing_month: date | None = Query(
        default=None,
        description="Filter by billing month",
    ),
    payment_status: str | None = Query(
        default=None,
        description=(
            "Filter by payment/bill status "
            "(Generated, Pending, Paid, Overdue, Cancelled)"
        ),
    ),
    overdue_status: str | None = Query(
        default=None,
        pattern="^(overdue|not_overdue)$",
        description=(
            "Filter by overdue status"
        ),
    ),
    amount_min: float | None = Query(
        default=None,
        ge=0,
        description="Minimum bill amount",
    ),
    amount_max: float | None = Query(
        default=None,
        ge=0,
        description="Maximum bill amount",
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
        description="Number of bills per page",
    ),
    sort_by: str = Query(
        default="billing_month",
        description="Field used for sorting",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    db: Session = Depends(get_db),
):
    bills, total, total_pages = (
        service.get_all_bills(
            db=db,
            billing_month=billing_month,
            payment_status=payment_status,
            overdue_status=overdue_status,
            amount_min=amount_min,
            amount_max=amount_max,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )

    return {
        "items": bills,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }


@router.get(
    "/{bill_id}",
    response_model=BillResponse,
)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
):
    return service.get_bill(
        db,
        bill_id,
    )


@customer_bill_router.get(
    "/{customer_id}/bills",
    response_model=list[BillResponse],
)
def get_customer_bills(
    customer_id: int,
    db: Session = Depends(get_db),
):
    return service.get_customer_bills(
        db,
        customer_id,
    )


@connection_bill_router.get(
    "/{connection_id}/bills",
    response_model=list[BillResponse],
)
def get_connection_bills(
    connection_id: int,
    db: Session = Depends(get_db),
):
    return service.get_connection_bills(
        db,
        connection_id,
    )