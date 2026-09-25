from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str
    transaction_id: str = Field(
        min_length=1,
        max_length=100,
    )
    payment_date: datetime
    payment_status: str = PaymentStatus.PENDING

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        allowed_methods = {
            PaymentMethod.UPI,
            PaymentMethod.CARD,
            PaymentMethod.NET_BANKING,
            PaymentMethod.WALLET,
        }

        if value not in allowed_methods:
            raise ValueError(
                "Invalid payment method. "
                "Allowed values: UPI, Card, Net Banking, Wallet"
            )

        return value

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value: str) -> str:
        allowed_statuses = {
            PaymentStatus.PENDING,
            PaymentStatus.SUCCESS,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED,
        }

        if value not in allowed_statuses:
            raise ValueError(
                "Invalid payment status. "
                "Allowed values: Pending, Success, Failed, Refunded"
            )

        return value

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Transaction ID cannot be empty"
            )

        return value


class PaymentResponse(BaseModel):
    id: int
    bill_id: int
    amount: float
    payment_method: str
    transaction_id: str
    payment_date: datetime
    payment_status: str

    model_config = {
        "from_attributes": True
    }