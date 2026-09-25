from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.bill import Bill
from models.complaint import Complaint
from models.connection import Connection
from models.customer import Customer
from models.meter import Meter
from models.meter_reading import MeterReading
from models.payment import Payment


class DashboardRepository:

    def get_total_customers(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Customer.id)
            )
        ) or 0

    def get_active_connections(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Connection.id)
            ).where(
                Connection.status == "Active"
            )
        ) or 0

    def get_disconnected_connections(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Connection.id)
            ).where(
                Connection.status == "Disconnected"
            )
        ) or 0

    def get_total_meters(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Meter.id)
            )
        ) or 0

    def get_faulty_meters(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Meter.id)
            ).where(
                Meter.meter_status == "Faulty"
            )
        ) or 0

    def get_monthly_units_consumed(
        self,
        db: Session,
    ) -> float:
        today = date.today()

        statement = (
            select(
                func.coalesce(
                    func.sum(
                        MeterReading.units_consumed
                    ),
                    0,
                )
            )
            .where(
                MeterReading.reading_year
                == today.year,
                MeterReading.reading_month
                == today.month,
            )
        )

        return float(
            db.scalar(statement) or 0
        )

    def get_monthly_revenue(
        self,
        db: Session,
    ) -> float:
        today = date.today()

        statement = (
            select(
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ),
                    0,
                )
            )
            .where(
                Payment.payment_status == "Success",
                func.extract(
                    "year",
                    Payment.payment_date,
                ) == today.year,
                func.extract(
                    "month",
                    Payment.payment_date,
                ) == today.month,
            )
        )

        return float(
            db.scalar(statement) or 0
        )

    def get_pending_bills(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Bill.id)
            ).where(
                Bill.bill_status == "Pending"
            )
        ) or 0

    def get_overdue_bills(
        self,
        db: Session,
    ) -> int:
        today = date.today()

        return db.scalar(
            select(
                func.count(Bill.id)
            ).where(
                Bill.due_date < today,
                Bill.bill_status != "Paid",
            )
        ) or 0

    def get_open_complaints(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Complaint.id)
            ).where(
                Complaint.status == "Open"
            )
        ) or 0

    def get_resolved_complaints(
        self,
        db: Session,
    ) -> int:
        return db.scalar(
            select(
                func.count(Complaint.id)
            ).where(
                Complaint.status == "Resolved"
            )
        ) or 0