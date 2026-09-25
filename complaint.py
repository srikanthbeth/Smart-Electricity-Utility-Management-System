from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.complaint import (
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
)


class ComplaintCreate(BaseModel):
    customer_id: int
    connection_id: int
    complaint_type: str
    description: str = Field(
        min_length=1,
        max_length=2000,
    )
    priority: str = ComplaintPriority.MEDIUM

    @field_validator("complaint_type")
    @classmethod
    def validate_complaint_type(cls, value: str) -> str:
        allowed_types = {
            ComplaintType.POWER_FAILURE,
            ComplaintType.VOLTAGE_ISSUE,
            ComplaintType.METER_ISSUE,
            ComplaintType.BILLING_ISSUE,
            ComplaintType.CONNECTION_ISSUE,
            ComplaintType.OTHER,
        }

        if value not in allowed_types:
            raise ValueError(
                "Invalid complaint type. "
                "Allowed values: Power Failure, Voltage Issue, "
                "Meter Issue, Billing Issue, Connection Issue, Other"
            )

        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        allowed_priorities = {
            ComplaintPriority.LOW,
            ComplaintPriority.MEDIUM,
            ComplaintPriority.HIGH,
            ComplaintPriority.EMERGENCY,
        }

        if value not in allowed_priorities:
            raise ValueError(
                "Invalid priority. "
                "Allowed values: Low, Medium, High, Emergency"
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Description cannot be empty")

        return value


class ComplaintAssign(BaseModel):
    technician_id: int


class ComplaintStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed_statuses = {
            ComplaintStatus.OPEN,
            ComplaintStatus.ASSIGNED,
            ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.RESOLVED,
            ComplaintStatus.CLOSED,
        }

        if value not in allowed_statuses:
            raise ValueError(
                "Invalid status. "
                "Allowed values: Open, Assigned, In Progress, "
                "Resolved, Closed"
            )

        return value


class ComplaintResponse(BaseModel):
    id: int
    customer_id: int
    connection_id: int
    complaint_type: str
    description: str
    priority: str
    assigned_to: int | None
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ComplaintHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    action: str
    old_value: str | None
    new_value: str | None
    changed_by: int | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )