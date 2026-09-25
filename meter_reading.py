from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReadingSource(str, Enum):
    MANUAL = "Manual"
    SMART_METER = "Smart Meter"
    FIELD_TECHNICIAN = "Field Technician"


class MeterReadingCreate(BaseModel):
    meter_id: int = Field(
        ...,
        gt=0,
    )

    reading_date: date

    previous_reading: float = Field(
        ...,
        ge=0,
    )

    current_reading: float = Field(
        ...,
        ge=0,
    )

    reading_source: ReadingSource

    remarks: str | None = None


class MeterReadingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    meter_id: int
    reading_date: date
    previous_reading: float
    current_reading: float
    units_consumed: float
    reading_source: ReadingSource
    remarks: str | None