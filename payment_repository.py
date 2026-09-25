from sqlalchemy import select
from sqlalchemy.orm import Session

from models.payment import Payment


class PaymentRepository:

    def create(
        self,
        db: Session,
        payment: Payment,
    ) -> Payment:
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def get_by_id(
        self,
        db: Session,
        payment_id: int,
    ) -> Payment | None:
        return db.get(
            Payment,
            payment_id,
        )

    def get_all(
        self,
        db: Session,
    ) -> list[Payment]:
        statement = select(Payment).order_by(
            Payment.id.desc()
        )

        return list(
            db.scalars(statement).all()
        )

    def get_by_bill(
        self,
        db: Session,
        bill_id: int,
    ) -> list[Payment]:
        statement = (
            select(Payment)
            .where(
                Payment.bill_id == bill_id
            )
            .order_by(
                Payment.payment_date.desc(),
                Payment.id.desc(),
            )
        )

        return list(
            db.scalars(statement).all()
        )

    def get_by_transaction_id(
        self,
        db: Session,
        transaction_id: str,
    ) -> Payment | None:
        statement = select(Payment).where(
            Payment.transaction_id == transaction_id
        )

        return db.scalars(statement).first()