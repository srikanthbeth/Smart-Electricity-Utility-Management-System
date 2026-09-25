from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.technician import (
    TechnicianAvailability,
    TechnicianSpecialization,
)


class TechnicianCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    employee_id: str = Field(
        min_length=1,
        max_length=50,
    )

    phone: str = Field(
        min_length=10,
        max_length=20,
    )

    specialization: str

    availability_status: str = (
        TechnicianAvailability.AVAILABLE
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Name cannot be empty"
            )

        return value

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Employee ID cannot be empty"
            )

        return value

    @field_validator("specialization")
    @classmethod
    def validate_specialization(cls, value: str) -> str:
        allowed_specializations = {
            TechnicianSpecialization.METER_INSTALLATION,
            TechnicianSpecialization.METER_REPLACEMENT,
            TechnicianSpecialization.CONNECTION_INSPECTION,
            TechnicianSpecialization.COMPLAINT_RESOLUTION,
        }

        if value not in allowed_specializations:
            raise ValueError(
                "Invalid specialization. "
                "Allowed values: Meter Installation, "
                "Meter Replacement, Connection Inspection, "
                "Complaint Resolution"
            )

        return value

    @field_validator("availability_status")
    @classmethod
    def validate_availability_status(cls, value: str) -> str:
        allowed_statuses = {
            TechnicianAvailability.AVAILABLE,
            TechnicianAvailability.BUSY,
            TechnicianAvailability.ON_LEAVE,
            TechnicianAvailability.UNAVAILABLE,
        }

        if value not in allowed_statuses:
            raise ValueError(
                "Invalid availability status. "
                "Allowed values: Available, Busy, "
                "On Leave, Unavailable"
            )

        return value


class TechnicianAvailabilityUpdate(BaseModel):
    availability_status: str

    @field_validator("availability_status")
    @classmethod
    def validate_availability_status(cls, value: str) -> str:
        allowed_statuses = {
            TechnicianAvailability.AVAILABLE,
            TechnicianAvailability.BUSY,
            TechnicianAvailability.ON_LEAVE,
            TechnicianAvailability.UNAVAILABLE,
        }

        if value not in allowed_statuses:
            raise ValueError(
                "Invalid availability status. "
                "Allowed values: Available, Busy, "
                "On Leave, Unavailable"
            )

        return value


class TechnicianResponse(BaseModel):
    id: int
    name: str
    employee_id: str
    phone: str
    specialization: str
    availability_status: str

    model_config = ConfigDict(
        from_attributes=True,
    )