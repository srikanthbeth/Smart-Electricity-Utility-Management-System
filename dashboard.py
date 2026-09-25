from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_customers: int
    active_connections: int
    disconnected_connections: int
    total_meters: int
    faulty_meters: int
    monthly_units_consumed: float
    monthly_revenue: float
    pending_bills: int
    overdue_bills: int
    open_complaints: int
    resolved_complaints: int