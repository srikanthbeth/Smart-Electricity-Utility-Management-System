from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BillCreate(BaseModel):
    connection_id: int = Field(
        ...,
        gt=0,
    )

    billing_month: date

    tax: float = Field(
        default=0.0,
        ge=0,
    )

    late_fee: float = Field(
        default=0.0,
        ge=0,
    )

    discount: float = Field(
        default=0.0,
        ge=0,
    )

    due_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.billing_month.day != 1:
            raise ValueError(
                "billing_month must be the first day of the month"
            )

        return self


class BillResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    connection_id: int
    billing_month: date
    units_consumed: float
    energy_charge: float
    fixed_charge: float
    tax: float
    late_fee: float
    discount: float
    total_amount: float
    due_date: date
    bill_status: str