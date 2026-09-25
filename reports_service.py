from sqlalchemy.orm import Session

from repositories.reports_repository import (
    ReportsRepository,
)


class ReportsService:

    def __init__(self):
        self.repository = ReportsRepository()

    def get_daily_collection(
        self,
        db: Session,
    ):
        rows = self.repository.get_daily_collection(db)

        return [
            {
                "date": row.payment_date,
                "amount_collected": float(
                    row.amount or 0
                ),
                "payment_count": row.payment_count,
            }
            for row in rows
        ]

    def get_monthly_revenue(
        self,
        db: Session,
    ):
        rows = self.repository.get_monthly_revenue(db)

        return [
            {
                "month": (
                    f"{int(row.year):04d}-"
                    f"{int(row.month):02d}"
                ),
                "revenue": float(
                    row.revenue or 0
                ),
                "bill_count": row.payment_count,
            }
            for row in rows
        ]

    def get_customer_billing(
        self,
        db: Session,
    ):
        rows = self.repository.get_customer_billing(db)

        result = []

        for row in rows:
            billed = float(
                row.total_billed or 0
            )

            paid = float(
                row.total_paid or 0
            )

            result.append(
                {
                    "customer_id": row.id,
                    "customer_name": row.full_name,
                    "total_billed": billed,
                    "total_paid": paid,
                    "outstanding_amount": max(
                        billed - paid,
                        0,
                    ),
                }
            )

        return result

    def get_connection_consumption(
        self,
        db: Session,
    ):
        rows = (
            self.repository
            .get_connection_consumption(db)
        )

        return [
            {
                "connection_id": row.id,
                "connection_number": (
                    row.connection_number
                ),
                "units_consumed": float(
                    row.units_consumed or 0
                ),
                "bill_amount": float(
                    row.bill_amount or 0
                ),
            }
            for row in rows
        ]

    def get_technician_performance(
        self,
        db: Session,
    ):
        rows = (
            self.repository
            .get_technician_performance(db)
        )

        return [
            {
                "technician_id": row.id,
                "technician_name": row.name,
                "assigned_complaints": (
                    row.assigned_complaints
                ),
                "resolved_complaints": (
                    row.resolved_complaints
                ),
            }
            for row in rows
        ]

    def get_complaint_resolution(
        self,
        db: Session,
    ):
        rows = (
            self.repository
            .get_complaint_resolution(db)
        )

        return [
            {
                "complaint_id": row.id,
                "complaint_type": (
                    row.complaint_type
                ),
                "priority": row.priority,
                "status": row.status,
                "assigned_to": row.assigned_to,
            }
            for row in rows
        ]

    def get_outstanding_payments(
        self,
        db: Session,
    ):
        rows = (
            self.repository
            .get_outstanding_payments(db)
        )

        return [
            {
                "bill_id": row.id,
                "connection_id": (
                    row.connection_id
                ),
                "billing_month": (
                    row.billing_month.strftime(
                        "%Y-%m"
                    )
                ),
                "total_amount": float(
                    row.total_amount or 0
                ),
                "paid_amount": float(
                    row.paid_amount or 0
                ),
                "outstanding_amount": max(
                    float(
                        row.total_amount or 0
                    )
                    - float(
                        row.paid_amount or 0
                    ),
                    0,
                ),
            }
            for row in rows
        ]