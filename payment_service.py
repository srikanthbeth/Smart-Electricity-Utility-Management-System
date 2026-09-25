from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.bill import Bill, BillStatus
from models.payment import Payment, PaymentStatus
from repositories.payment_repository import PaymentRepository
from schemas.payment import PaymentCreate


class PaymentService:

    def __init__(self):
        self.payment_repository = PaymentRepository()

    def create_payment(
        self,
        db: Session,
        bill_id: int,
        data: PaymentCreate,
    ) -> Payment:

        bill = db.get(
            Bill,
            bill_id,
        )

        if bill is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )

        existing_payment = (
            self.payment_repository
            .get_by_transaction_id(
                db,
                data.transaction_id,
            )
        )

        if existing_payment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate transaction ID",
            )

        bill_amount = float(
            bill.total_amount
        )

        payment_amount = float(
            data.amount
        )

        if payment_amount > bill_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Payment amount cannot exceed "
                    "bill amount"
                ),
            )

        payment = Payment(
            bill_id=bill_id,
            amount=payment_amount,
            payment_method=data.payment_method,
            transaction_id=data.transaction_id,
            payment_date=data.payment_date,
            payment_status=data.payment_status,
        )

        payment = self.payment_repository.create(
            db,
            payment,
        )

        if data.payment_status == PaymentStatus.SUCCESS:
            bill.bill_status = BillStatus.PAID

            db.add(bill)
            db.commit()
            db.refresh(payment)

        return payment

    def get_all_payments(
        self,
        db: Session,
    ) -> list[Payment]:
        return self.payment_repository.get_all(db)

    def get_payment(
        self,
        db: Session,
        payment_id: int,
    ) -> Payment:

        payment = (
            self.payment_repository
            .get_by_id(
                db,
                payment_id,
            )
        )

        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return payment

    def get_bill_payments(
        self,
        db: Session,
        bill_id: int,
    ) -> list[Payment]:

        bill = db.get(
            Bill,
            bill_id,
        )

        if bill is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )

        return (
            self.payment_repository
            .get_by_bill(
                db,
                bill_id,
            )
        )