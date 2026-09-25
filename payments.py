from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.payment import PaymentCreate, PaymentResponse
from services.payment_service import PaymentService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)

bill_payment_router = APIRouter(
    prefix="/bills",
    tags=["Bill Payments"],
)

service = PaymentService()


@router.post(
    "/{bill_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    bill_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
):
    return service.create_payment(
        db,
        bill_id,
        data,
    )


@router.get(
    "",
    response_model=list[PaymentResponse],
)
def get_payments(
    db: Session = Depends(get_db),
):
    return service.get_all_payments(db)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    return service.get_payment(
        db,
        payment_id,
    )


@bill_payment_router.get(
    "/{bill_id}/payments",
    response_model=list[PaymentResponse],
)
def get_bill_payments(
    bill_id: int,
    db: Session = Depends(get_db),
):
    return service.get_bill_payments(
        db,
        bill_id,
    )