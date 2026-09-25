from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.bill import Bill, BillStatus
from models.connection import Connection
from repositories.bill_repository import BillRepository
from repositories.meter_reading_repository import (
    MeterReadingRepository,
)
from repositories.tariff_repository import TariffRepository
from schemas.bill import BillCreate


class BillService:

    def __init__(self):
        self.bill_repository = BillRepository()
        self.reading_repository = MeterReadingRepository()
        self.tariff_repository = TariffRepository()

    def generate_bill(
        self,
        db: Session,
        data: BillCreate,
    ) -> Bill:

        # 1. Check connection
        connection = db.get(
            Connection,
            data.connection_id,
        )

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        # 2. Disconnected connections cannot generate bills
        connection_status = getattr(
            connection.status,
            "value",
            connection.status,
        )

        if str(connection_status).lower() == "disconnected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Disconnected connections cannot "
                    "generate regular bills"
                ),
            )

        # 3. Prevent duplicate bill
        existing_bill = (
            self.bill_repository
            .get_by_connection_and_month(
                db,
                data.connection_id,
                data.billing_month,
            )
        )

        if existing_bill is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Bill already exists for this "
                    "connection and billing month"
                ),
            )

        # 4. Get meter reading
        reading = (
            self.reading_repository
            .get_by_connection_and_month(
                db,
                data.connection_id,
                data.billing_month,
            )
        )

        if reading is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No meter reading found for this "
                    "connection and billing month"
                ),
            )

        # 5. Units consumed come from meter reading
        units_consumed = float(
            reading.units_consumed
        )

        if units_consumed < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Units consumed cannot be negative",
            )

        # 6. Find applicable tariff
        connection_type = getattr(
            connection.connection_type,
            "value",
            connection.connection_type,
        )

        tariff = (
            self.tariff_repository
            .find_applicable_tariff(
                db=db,
                connection_type=str(connection_type),
                units_consumed=units_consumed,
                billing_date=data.billing_month,
            )
        )

        if tariff is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No applicable tariff found",
            )

        # 7. Calculate energy charge
        energy_charge = (
            units_consumed
            * float(tariff.rate_per_unit)
        )

        # 8. Fixed charge comes from tariff
        fixed_charge = float(
            tariff.fixed_charge
        )

        # 9. Calculate total
        total_amount = (
            energy_charge
            + fixed_charge
            + float(data.tax)
            + float(data.late_fee)
            - float(data.discount)
        )

        # 10. Bill amount must be greater than zero
        if total_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill amount must be greater than 0",
            )

        # 11. Create bill
        bill = Bill(
            connection_id=data.connection_id,
            billing_month=data.billing_month,
            units_consumed=units_consumed,
            energy_charge=round(
                energy_charge,
                2,
            ),
            fixed_charge=round(
                fixed_charge,
                2,
            ),
            tax=round(
                float(data.tax),
                2,
            ),
            late_fee=round(
                float(data.late_fee),
                2,
            ),
            discount=round(
                float(data.discount),
                2,
            ),
            total_amount=round(
                total_amount,
                2,
            ),
            due_date=data.due_date,
            bill_status=BillStatus.GENERATED,
        )

        return self.bill_repository.create(
            db,
            bill,
        )

    # ======================================================
    # LEVEL 13 - FILTERING + PAGINATION + SORTING
    # ======================================================

    def get_all_bills(
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
    ):

        if (
            amount_min is not None
            and amount_max is not None
            and amount_min > amount_max
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "amount_min cannot be greater "
                    "than amount_max"
                ),
            )

        return self.bill_repository.get_all(
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

    def get_bill(
        self,
        db: Session,
        bill_id: int,
    ) -> Bill:

        bill = self.bill_repository.get_by_id(
            db,
            bill_id,
        )

        if bill is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )

        return bill

    def get_customer_bills(
        self,
        db: Session,
        customer_id: int,
    ) -> list[Bill]:

        return self.bill_repository.get_by_customer(
            db,
            customer_id,
        )

    def get_connection_bills(
        self,
        db: Session,
        connection_id: int,
    ) -> list[Bill]:

        connection = db.get(
            Connection,
            connection_id,
        )

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return self.bill_repository.get_by_connection(
            db,
            connection_id,
        )