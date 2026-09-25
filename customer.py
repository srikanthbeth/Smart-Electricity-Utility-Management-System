from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    CLOSED = "Closed"


class CustomerCreate(BaseModel):
    customer_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    phone: str = Field(
        ...,
        min_length=7,
        max_length=20,
    )

    address: str = Field(
        ...,
        min_length=3,
        max_length=500,
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )

    address: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_number: str
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    status: CustomerStatus