from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ConnectionType(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INDUSTRIAL = "Industrial"


class ConnectionStatus(str, Enum):
    ACTIVE = "Active"
    DISCONNECTED = "Disconnected"
    SUSPENDED = "Suspended"


class ConnectionCreate(BaseModel):
    customer_id: int = Field(
        ...,
        gt=0,
    )

    connection_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    connection_type: ConnectionType

    sanctioned_load: float = Field(
        ...,
        gt=0,
    )

    tariff_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    connection_date: date

    status: ConnectionStatus = ConnectionStatus.ACTIVE


class ConnectionUpdate(BaseModel):
    connection_type: ConnectionType | None = None

    sanctioned_load: float | None = Field(
        default=None,
        gt=0,
    )

    tariff_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    connection_date: date | None = None

    status: ConnectionStatus | None = None


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    connection_number: str
    connection_type: ConnectionType
    sanctioned_load: float
    tariff_type: str
    connection_date: date
    status: ConnectionStatus