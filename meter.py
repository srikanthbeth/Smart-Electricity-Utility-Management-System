from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MeterStatus(str, Enum):
    ACTIVE = "Active"
    FAULTY = "Faulty"
    REMOVED = "Removed"


class MeterCreate(BaseModel):
    connection_id: int = Field(
        ...,
        gt=0,
    )

    meter_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    meter_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    installation_date: date

    initial_reading: float = Field(
        ...,
        ge=0,
    )

    current_reading: float = Field(
        ...,
        ge=0,
    )

    meter_status: MeterStatus = MeterStatus.ACTIVE


class MeterUpdate(BaseModel):
    meter_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    installation_date: date | None = None

    initial_reading: float | None = Field(
        default=None,
        ge=0,
    )

    current_reading: float | None = Field(
        default=None,
        ge=0,
    )

    meter_status: MeterStatus | None = None


class MeterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connection_id: int
    meter_number: str
    meter_type: str
    installation_date: date
    initial_reading: float
    current_reading: float
    meter_status: MeterStatus