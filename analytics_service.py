from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.bill import Bill
from models.connection import Connection
from models.customer import Customer
from models.meter import Meter
from models.meter_reading import MeterReading


class AnalyticsService:

    def get_connection_monthly_consumption(
        self,
        db: Session,
        connection_id: int,
    ):

        connection = db.get(
            Connection,
            connection_id,
        )

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        statement = (
            select(
                MeterReading.reading_year,
                MeterReading.reading_month,
                func.sum(
                    MeterReading.units_consumed
                ).label("units_consumed"),
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("bill_amount"),
            )
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .outerjoin(
                Bill,
                (
                    (Bill.connection_id == connection_id)
                    &
                    (
                        func.extract(
                            "year",
                            Bill.billing_month,
                        )
                        == MeterReading.reading_year
                    )
                    &
                    (
                        func.extract(
                            "month",
                            Bill.billing_month,
                        )
                        == MeterReading.reading_month
                    )
                ),
            )
            .where(
                Meter.connection_id == connection_id
            )
            .group_by(
                MeterReading.reading_year,
                MeterReading.reading_month,
            )
            .order_by(
                MeterReading.reading_year.asc(),
                MeterReading.reading_month.asc(),
            )
        )

        rows = db.execute(statement).all()

        result = []

        for row in rows:
            result.append(
                {
                    "month": (
                        f"{int(row.reading_year):04d}-"
                        f"{int(row.reading_month):02d}"
                    ),
                    "units_consumed": float(
                        row.units_consumed or 0
                    ),
                    "bill_amount": float(
                        row.bill_amount or 0
                    ),
                }
            )

        return result

    def get_connection_yearly_consumption(
        self,
        db: Session,
        connection_id: int,
    ):

        connection = db.get(
            Connection,
            connection_id,
        )

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        statement = (
            select(
                MeterReading.reading_year,
                func.sum(
                    MeterReading.units_consumed
                ).label("units_consumed"),
            )
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .where(
                Meter.connection_id == connection_id
            )
            .group_by(
                MeterReading.reading_year
            )
            .order_by(
                MeterReading.reading_year.asc()
            )
        )

        rows = db.execute(statement).all()

        result = []

        for row in rows:

            year = int(row.reading_year)

            bill_statement = select(
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                )
            ).where(
                Bill.connection_id == connection_id,
                func.extract(
                    "year",
                    Bill.billing_month,
                ) == year,
            )

            bill_amount = db.scalar(
                bill_statement
            )

            result.append(
                {
                    "year": year,
                    "units_consumed": float(
                        row.units_consumed or 0
                    ),
                    "bill_amount": float(
                        bill_amount or 0
                    ),
                }
            )

        return result

    def get_connection_usage(
        self,
        db: Session,
        connection_id: int,
    ):

        connection = db.get(
            Connection,
            connection_id,
        )

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        units_statement = (
            select(
                func.coalesce(
                    func.sum(
                        MeterReading.units_consumed
                    ),
                    0,
                )
            )
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .where(
                Meter.connection_id == connection_id
            )
        )

        units_consumed = db.scalar(
            units_statement
        )

        bill_statement = select(
            func.coalesce(
                func.sum(Bill.total_amount),
                0,
            )
        ).where(
            Bill.connection_id == connection_id
        )

        bill_amount = db.scalar(
            bill_statement
        )

        return {
            "connection_id": connection.id,
            "connection_number": connection.connection_number,
            "units_consumed": float(
                units_consumed or 0
            ),
            "bill_amount": float(
                bill_amount or 0
            ),
        }

    def get_customer_usage(
        self,
        db: Session,
        customer_id: int,
    ):

        customer = db.get(
            Customer,
            customer_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        units_statement = (
            select(
                func.coalesce(
                    func.sum(
                        MeterReading.units_consumed
                    ),
                    0,
                )
            )
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .join(
                Connection,
                Connection.id == Meter.connection_id,
            )
            .where(
                Connection.customer_id == customer_id
            )
        )

        units_consumed = db.scalar(
            units_statement
        )

        bill_statement = (
            select(
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                )
            )
            .join(
                Connection,
                Connection.id == Bill.connection_id,
            )
            .where(
                Connection.customer_id == customer_id
            )
        )

        bill_amount = db.scalar(
            bill_statement
        )

        return {
            "customer_id": customer_id,
            "units_consumed": float(
                units_consumed or 0
            ),
            "bill_amount": float(
                bill_amount or 0
            ),
        }

    def get_highest_consuming_connections(
        self,
        db: Session,
    ):

        statement = (
            select(
                Connection.id.label(
                    "connection_id"
                ),
                Connection.connection_number,
                func.coalesce(
                    func.sum(
                        MeterReading.units_consumed
                    ),
                    0,
                ).label("units_consumed"),
            )
            .outerjoin(
                Meter,
                Meter.connection_id == Connection.id,
            )
            .outerjoin(
                MeterReading,
                MeterReading.meter_id == Meter.id,
            )
            .group_by(
                Connection.id,
                Connection.connection_number,
            )
            .order_by(
                func.coalesce(
                    func.sum(
                        MeterReading.units_consumed
                    ),
                    0,
                ).desc()
            )
        )

        rows = db.execute(statement).all()

        return [
            {
                "connection_id": row.connection_id,
                "connection_number": row.connection_number,
                "units_consumed": float(
                    row.units_consumed or 0
                ),
            }
            for row in rows
        ]

    def get_average_monthly_consumption(
        self,
        db: Session,
    ):

        monthly_statement = (
            select(
                MeterReading.reading_year,
                MeterReading.reading_month,
                func.sum(
                    MeterReading.units_consumed
                ).label("units_consumed"),
            )
            .group_by(
                MeterReading.reading_year,
                MeterReading.reading_month,
            )
        )

        rows = db.execute(
            monthly_statement
        ).all()

        if not rows:
            return {
                "average_monthly_consumption": 0.0
            }

        total_consumption = sum(
            float(row.units_consumed or 0)
            for row in rows
        )

        average = (
            total_consumption / len(rows)
        )

        return {
            "average_monthly_consumption": average
        }