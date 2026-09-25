from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.tariff import Tariff
from repositories.tariff_repository import TariffRepository
from schemas.tariff import TariffCreate, TariffUpdate


class TariffService:

    def __init__(self):
        self.repository = TariffRepository()

    def create_tariff(
        self,
        db: Session,
        data: TariffCreate,
    ) -> Tariff:

        tariff = Tariff(
            tariff_name=data.tariff_name,
            connection_type=data.connection_type,
            minimum_units=data.minimum_units,
            maximum_units=data.maximum_units,
            rate_per_unit=data.rate_per_unit,
            fixed_charge=data.fixed_charge,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            status=data.status,
        )

        return self.repository.create(db, tariff)

    def get_tariffs(
        self,
        db: Session,
    ) -> list[Tariff]:

        return self.repository.get_all(db)

    def get_tariff(
        self,
        db: Session,
        tariff_id: int,
    ) -> Tariff:

        tariff = self.repository.get_by_id(
            db,
            tariff_id,
        )

        if tariff is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tariff not found",
            )

        return tariff

    def update_tariff(
        self,
        db: Session,
        tariff_id: int,
        data: TariffUpdate,
    ) -> Tariff:

        tariff = self.get_tariff(
            db,
            tariff_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        minimum_units = values.get(
            "minimum_units",
            tariff.minimum_units,
        )

        maximum_units = values.get(
            "maximum_units",
            tariff.maximum_units,
        )

        effective_from = values.get(
            "effective_from",
            tariff.effective_from,
        )

        effective_to = values.get(
            "effective_to",
            tariff.effective_to,
        )

        if (
            maximum_units is not None
            and maximum_units < minimum_units
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "maximum_units must be greater than "
                    "or equal to minimum_units"
                ),
            )

        if (
            effective_to is not None
            and effective_to < effective_from
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "effective_to must be greater than "
                    "or equal to effective_from"
                ),
            )

        for field, value in values.items():
            setattr(
                tariff,
                field,
                value,
            )

        db.commit()
        db.refresh(tariff)

        return tariff

    def delete_tariff(
        self,
        db: Session,
        tariff_id: int,
    ) -> None:

        tariff = self.get_tariff(
            db,
            tariff_id,
        )

        self.repository.delete(
            db,
            tariff,
        )

    def get_applicable_tariff(
        self,
        db: Session,
        connection_type: str,
        units_consumed: float,
        billing_date: date,
    ) -> Tariff:

        tariff = self.repository.find_applicable_tariff(
            db=db,
            connection_type=connection_type,
            units_consumed=units_consumed,
            billing_date=billing_date,
        )

        if tariff is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No applicable tariff found",
            )

        return tariff