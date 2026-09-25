from pydantic import BaseModel


class MonthlyConsumptionResponse(BaseModel):
    month: str
    units_consumed: float
    bill_amount: float


class YearlyConsumptionResponse(BaseModel):
    year: int
    units_consumed: float
    bill_amount: float


class ConnectionUsageResponse(BaseModel):
    connection_id: int
    connection_number: str
    units_consumed: float
    bill_amount: float


class CustomerUsageResponse(BaseModel):
    customer_id: int
    units_consumed: float
    bill_amount: float


class HighestConsumptionResponse(BaseModel):
    connection_id: int
    connection_number: str
    units_consumed: float


class AverageMonthlyConsumptionResponse(BaseModel):
    average_monthly_consumption: float