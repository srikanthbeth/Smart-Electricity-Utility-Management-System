from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.service_request import (
    ServiceRequestStatus,
    ServiceRequestType,
)


class ServiceRequestCreate(BaseModel):
    customer_id: int

    connection_id: int | None = None

    request_type: str

    description: str = Field(
        min_length=1,
        max_length=2000,
    )

    requested_date: date

    @field_validator("request_type")
    @classmethod
    def validate_request_type(
        cls,
        value: str,
    ) -> str:

        allowed_types = {
            ServiceRequestType.NEW_CONNECTION,
            ServiceRequestType.LOAD_CHANGE,
            ServiceRequestType.METER_REPLACEMENT,
            ServiceRequestType.NAME_CHANGE,
            ServiceRequestType.ADDRESS_CHANGE,
            ServiceRequestType.DISCONNECTION,
            ServiceRequestType.RECONNECTION,
        }

        if value not in allowed_types:
            raise ValueError(
                "Invalid service request type. "
                "Allowed values: New Connection, Load Change, "
                "Meter Replacement, Name Change, Address Change, "
                "Disconnection, Reconnection"
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Description cannot be empty"
            )

        return value


class ServiceRequestResponse(BaseModel):
    id: int
    customer_id: int
    connection_id: int | None
    request_type: str
    description: str
    requested_date: date
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )