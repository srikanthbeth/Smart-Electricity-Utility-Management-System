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
from models.technician import Technician


class ReportsRepository:

    def get_daily_collection(self, db: Session):
        statement = (
            select(
                func.date(Payment.payment_date).label("date"),
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label("amount_collected"),
                func.count(Payment.id).label("payment_count"),
            )
            .where(
                Payment.payment_status == "Success",
            )
            .group_by(
                func.date(Payment.payment_date),
            )
            .order_by(
                func.date(Payment.payment_date),
            )
        )

        return db.execute(statement).all()

    def get_monthly_revenue(self, db: Session):
        year = func.extract(
            "year",
            Payment.payment_date,
        )

        month = func.extract(
            "month",
            Payment.payment_date,
        )

        statement = (
            select(
                year.label("year"),
                month.label("month"),
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label("revenue"),
                func.count(Payment.id).label("bill_count"),
            )
            .where(
                Payment.payment_status == "Success",
            )
            .group_by(
                year,
                month,
            )
            .order_by(
                year,
                month,
            )
        )

        return db.execute(statement).all()

    def get_customer_billing(self, db: Session):
        """
        Return billing information grouped by customer.

        Billing totals and successful payment totals are calculated
        in separate subqueries so that multiple bills/payments do
        not multiply each other.
        """

        billed_subquery = (
            select(
                Connection.customer_id.label("customer_id"),
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("total_billed"),
            )
            .select_from(Bill)
            .join(
                Connection,
                Connection.id == Bill.connection_id,
            )
            .group_by(
                Connection.customer_id,
            )
            .subquery()
        )

        paid_subquery = (
            select(
                Connection.customer_id.label("customer_id"),
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label("total_paid"),
            )
            .select_from(Payment)
            .join(
                Bill,
                Bill.id == Payment.bill_id,
            )
            .join(
                Connection,
                Connection.id == Bill.connection_id,
            )
            .where(
                Payment.payment_status == "Success",
            )
            .group_by(
                Connection.customer_id,
            )
            .subquery()
        )

        statement = (
            select(
                Customer.id,
                Customer.full_name,
                func.coalesce(
                    billed_subquery.c.total_billed,
                    0,
                ).label("total_billed"),
                func.coalesce(
                    paid_subquery.c.total_paid,
                    0,
                ).label("total_paid"),
            )
            .select_from(Customer)
            .outerjoin(
                billed_subquery,
                billed_subquery.c.customer_id == Customer.id,
            )
            .outerjoin(
                paid_subquery,
                paid_subquery.c.customer_id == Customer.id,
            )
            .order_by(
                Customer.id,
            )
        )

        return db.execute(statement).all()

    def get_connection_consumption(self, db: Session):
        """
        Return consumption and bill information per connection.

        Consumption and bill totals are calculated separately to
        prevent multiplication when a connection has multiple
        meter readings and multiple bills.
        """

        consumption_subquery = (
            select(
                Meter.connection_id.label("connection_id"),
                func.coalesce(
                    func.sum(MeterReading.units_consumed),
                    0,
                ).label("units_consumed"),
            )
            .select_from(MeterReading)
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .group_by(
                Meter.connection_id,
            )
            .subquery()
        )

        bill_subquery = (
            select(
                Bill.connection_id.label("connection_id"),
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("bill_amount"),
            )
            .select_from(Bill)
            .group_by(
                Bill.connection_id,
            )
            .subquery()
        )

        statement = (
            select(
                Connection.id,
                Connection.connection_number,
                func.coalesce(
                    consumption_subquery.c.units_consumed,
                    0,
                ).label("units_consumed"),
                func.coalesce(
                    bill_subquery.c.bill_amount,
                    0,
                ).label("bill_amount"),
            )
            .select_from(Connection)
            .outerjoin(
                consumption_subquery,
                consumption_subquery.c.connection_id
                == Connection.id,
            )
            .outerjoin(
                bill_subquery,
                bill_subquery.c.connection_id
                == Connection.id,
            )
            .order_by(
                Connection.id,
            )
        )

        return db.execute(statement).all()

    def get_technician_performance(self, db: Session):
        statement = (
            select(
                Technician.id.label("technician_id"),
                Technician.name.label("technician_name"),
                func.count(Complaint.id).label(
                    "assigned_complaints"
                ),
                func.count(
                    Complaint.id
                ).filter(
                    Complaint.status == "Resolved"
                ).label(
                    "resolved_complaints"
                ),
            )
            .select_from(Technician)
            .outerjoin(
                Complaint,
                Complaint.assigned_to == Technician.id,
            )
            .group_by(
                Technician.id,
                Technician.name,
            )
            .order_by(
                Technician.id,
            )
        )

        return db.execute(statement).all()

    def get_complaint_resolution(self, db: Session):
        statement = (
            select(
                Complaint.id.label("complaint_id"),
                Complaint.complaint_type,
                Complaint.priority,
                Complaint.status,
                Complaint.assigned_to,
            )
            .order_by(
                Complaint.id,
            )
        )

        return db.execute(statement).all()

    def get_outstanding_payments(self, db: Session):
        paid_subquery = (
            select(
                Payment.bill_id.label("bill_id"),
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label("paid_amount"),
            )
            .where(
                Payment.payment_status == "Success",
            )
            .group_by(
                Payment.bill_id,
            )
            .subquery()
        )

        statement = (
            select(
                Bill.id.label("bill_id"),
                Bill.connection_id,
                Bill.billing_month,
                Bill.total_amount,
                func.coalesce(
                    paid_subquery.c.paid_amount,
                    0,
                ).label("paid_amount"),
            )
            .select_from(Bill)
            .outerjoin(
                paid_subquery,
                paid_subquery.c.bill_id == Bill.id,
            )
            .where(
                Bill.total_amount
                > func.coalesce(
                    paid_subquery.c.paid_amount,
                    0,
                )
            )
            .order_by(
                Bill.id,
            )
        )

        return db.execute(statement).all()