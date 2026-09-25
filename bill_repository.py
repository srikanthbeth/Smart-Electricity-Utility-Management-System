from datetime import date

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from models.bill import Bill


class BillRepository:

    def create(
        self,
        db: Session,
        bill: Bill,
    ) -> Bill:
        db.add(bill)
        db.commit()
        db.refresh(bill)

        return bill

    def get_by_id(
        self,
        db: Session,
        bill_id: int,
    ) -> Bill | None:
        return db.get(
            Bill,
            bill_id,
        )

    def get_all(
        self,
        db: Session,
        billing_month: date | None = None,
        payment_status: str | None = None,
        overdue_status: str | None = None,
        amount_min: float | None = None,
        amount_max: float | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "billing_month",
        sort_order: str = "desc",
    ) -> tuple[list[Bill], int, int]:

        statement = select(Bill)

        # --------------------------------------------------
        # BILLING MONTH FILTER
        # --------------------------------------------------
        if billing_month is not None:
            statement = statement.where(
                Bill.billing_month == billing_month
            )

        # --------------------------------------------------
        # PAYMENT STATUS FILTER
        # --------------------------------------------------
        if payment_status is not None:
            statement = statement.where(
                Bill.bill_status == payment_status
            )

        # --------------------------------------------------
        # OVERDUE STATUS FILTER
        #
        # A bill is considered overdue when:
        # due_date < today
        # and bill is not paid/cancelled
        # --------------------------------------------------
        if overdue_status is not None:

            normalized_overdue_status = (
                overdue_status.lower()
            )

            if normalized_overdue_status == "overdue":
                statement = statement.where(
                    Bill.due_date < date.today(),
                    Bill.bill_status.notin_(
                        ["Paid", "Cancelled"]
                    ),
                )

            elif normalized_overdue_status == "not_overdue":
                statement = statement.where(
                    (
                        Bill.due_date >= date.today()
                    )
                    |
                    (
                        Bill.bill_status.in_(
                            ["Paid", "Cancelled"]
                        )
                    )
                )

        # --------------------------------------------------
        # AMOUNT RANGE FILTER
        # --------------------------------------------------
        if amount_min is not None:
            statement = statement.where(
                Bill.total_amount >= amount_min
            )

        if amount_max is not None:
            statement = statement.where(
                Bill.total_amount <= amount_max
            )

        # --------------------------------------------------
        # ALLOWED SORT COLUMNS
        # --------------------------------------------------
        allowed_sort_columns = {
            "id": Bill.id,
            "billing_month": Bill.billing_month,
            "units_consumed": Bill.units_consumed,
            "energy_charge": Bill.energy_charge,
            "fixed_charge": Bill.fixed_charge,
            "tax": Bill.tax,
            "late_fee": Bill.late_fee,
            "discount": Bill.discount,
            "total_amount": Bill.total_amount,
            "due_date": Bill.due_date,
            "bill_status": Bill.bill_status,
            "connection_id": Bill.connection_id,
        }

        sort_column = allowed_sort_columns.get(
            sort_by,
            Bill.billing_month,
        )

        # --------------------------------------------------
        # SORTING
        # --------------------------------------------------
        if sort_order.lower() == "asc":
            statement = statement.order_by(
                asc(sort_column),
                asc(Bill.id),
            )
        else:
            statement = statement.order_by(
                desc(sort_column),
                desc(Bill.id),
            )

        # --------------------------------------------------
        # TOTAL COUNT
        # --------------------------------------------------
        count_statement = select(
            func.count()
        ).select_from(
            statement.order_by(None).subquery()
        )

        total = db.execute(
            count_statement
        ).scalar_one()

        # --------------------------------------------------
        # PAGINATION
        # --------------------------------------------------
        offset = (page - 1) * limit

        statement = statement.offset(
            offset
        ).limit(
            limit
        )

        bills = list(
            db.scalars(statement).all()
        )

        # --------------------------------------------------
        # TOTAL PAGES
        # --------------------------------------------------
        total_pages = (
            (total + limit - 1) // limit
            if total > 0
            else 0
        )

        return (
            bills,
            total,
            total_pages,
        )

    def get_by_connection_and_month(
        self,
        db: Session,
        connection_id: int,
        billing_month: date,
    ) -> Bill | None:
        statement = select(Bill).where(
            Bill.connection_id == connection_id,
            Bill.billing_month == billing_month,
        )

        return db.scalars(statement).first()

    def get_by_connection(
        self,
        db: Session,
        connection_id: int,
    ) -> list[Bill]:
        statement = (
            select(Bill)
            .where(
                Bill.connection_id == connection_id
            )
            .order_by(
                Bill.billing_month.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    def get_by_customer(
        self,
        db: Session,
        customer_id: int,
    ) -> list[Bill]:

        from models.connection import Connection

        statement = (
            select(Bill)
            .join(
                Connection,
                Connection.id == Bill.connection_id,
            )
            .where(
                Connection.customer_id == customer_id
            )
            .order_by(
                Bill.billing_month.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )