from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TariffCreate(BaseModel):
    tariff_name: str = Field(..., min_length=1, max_length=100)

    connection_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    minimum_units: float = Field(
        ...,
        ge=0,
    )

    maximum_units: float | None = Field(
        default=None,
        ge=0,
    )

    rate_per_unit: float = Field(
        ...,
        gt=0,
    )

    fixed_charge: float = Field(
        default=0.0,
        ge=0,
    )

    effective_from: date

    effective_to: date | None = None

    status: bool = True

    @model_validator(mode="after")
    def validate_tariff(self):
        if (
            self.maximum_units is not None
            and self.maximum_units < self.minimum_units
        ):
            raise ValueError(
                "maximum_units must be greater than or equal to minimum_units"
            )

        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "effective_to must be greater than or equal to effective_from"
            )

        return self


class TariffUpdate(BaseModel):
    tariff_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    connection_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    minimum_units: float | None = Field(
        default=None,
        ge=0,
    )

    maximum_units: float | None = Field(
        default=None,
        ge=0,
    )

    rate_per_unit: float | None = Field(
        default=None,
        gt=0,
    )

    fixed_charge: float | None = Field(
        default=None,
        ge=0,
    )

    effective_from: date | None = None

    effective_to: date | None = None

    status: bool | None = None


class TariffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tariff_name: str
    connection_type: str
    minimum_units: float
    maximum_units: float | None
    rate_per_unit: float
    fixed_charge: float
    effective_from: date
    effective_to: date | None
    status: bool