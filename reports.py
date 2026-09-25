from datetime import date

from pydantic import BaseModel


class DailyCollectionResponse(BaseModel):
    date: date
    amount_collected: float
    payment_count: int


class MonthlyRevenueResponse(BaseModel):
    month: str
    revenue: float
    bill_count: int


class CustomerBillingResponse(BaseModel):
    customer_id: int
    customer_name: str
    total_billed: float
    total_paid: float
    outstanding_amount: float


class ConnectionConsumptionResponse(BaseModel):
    connection_id: int
    connection_number: str
    units_consumed: float
    bill_amount: float


class TechnicianPerformanceResponse(BaseModel):
    technician_id: int
    technician_name: str
    assigned_complaints: int
    resolved_complaints: int


class ComplaintResolutionResponse(BaseModel):
    complaint_id: int
    complaint_type: str
    priority: str
    status: str
    assigned_to: int | None


class OutstandingPaymentResponse(BaseModel):
    bill_id: int
    connection_id: int
    billing_month: str
    total_amount: float
    paid_amount: float
    outstanding_amount: float