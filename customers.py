from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from services.customer_service import CustomerService


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    return CustomerService.create_customer(
        db,
        data,
    )


@router.get("")
def get_customers(
    city: str | None = Query(
        default=None,
        description="Filter customers by city",
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter customers by status",
    ),
    connection_type: str | None = Query(
        default=None,
        description=(
            "Filter customers by connection type "
            "(Residential, Commercial, Industrial)"
        ),
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
        description="Number of customers per page",
    ),
    sort_by: str = Query(
        default="id",
        description="Field used for sorting",
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    db: Session = Depends(get_db),
):
    customers, total, total_pages = (
        CustomerService.get_customers(
            db=db,
            city=city,
            status=status_filter,
            connection_type=connection_type,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )

    return {
        "items": customers,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    return CustomerService.get_customer(
        db,
        customer_id,
    )


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    return CustomerService.update_customer(
        db,
        customer_id,
        data,
    )


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    CustomerService.delete_customer(
        db,
        customer_id,
    )

    return None