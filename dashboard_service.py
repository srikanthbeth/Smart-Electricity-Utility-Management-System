from sqlalchemy.orm import Session

from repositories.dashboard_repository import (
    DashboardRepository,
)


class DashboardService:

    def __init__(self):
        self.repository = DashboardRepository()

    def get_dashboard(
        self,
        db: Session,
    ):
        return {
            "total_customers": (
                self.repository.get_total_customers(db)
            ),
            "active_connections": (
                self.repository.get_active_connections(db)
            ),
            "disconnected_connections": (
                self.repository.get_disconnected_connections(
                    db
                )
            ),
            "total_meters": (
                self.repository.get_total_meters(db)
            ),
            "faulty_meters": (
                self.repository.get_faulty_meters(db)
            ),
            "monthly_units_consumed": (
                self.repository.get_monthly_units_consumed(
                    db
                )
            ),
            "monthly_revenue": (
                self.repository.get_monthly_revenue(db)
            ),
            "pending_bills": (
                self.repository.get_pending_bills(db)
            ),
            "overdue_bills": (
                self.repository.get_overdue_bills(db)
            ),
            "open_complaints": (
                self.repository.get_open_complaints(db)
            ),
            "resolved_complaints": (
                self.repository.get_resolved_complaints(
                    db
                )
            ),
        }