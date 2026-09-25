from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.tariff import Tariff


class TariffRepository:

    def create(
        self,
        db: Session,
        tariff: Tariff,
    ) -> Tariff:
        db.add(tariff)
        db.commit()
        db.refresh(tariff)

        return tariff

    def get_by_id(
        self,
        db: Session,
        tariff_id: int,
    ) -> Tariff | None:
        return db.get(Tariff, tariff_id)

    def get_all(
        self,
        db: Session,
    ) -> list[Tariff]:
        statement = select(Tariff).order_by(Tariff.id)

        return list(
            db.scalars(statement).all()
        )

    def find_applicable_tariff(
        self,
        db: Session,
        connection_type: str,
        units_consumed: float,
        billing_date: date,
    ) -> Tariff | None:

        statement = select(Tariff).where(
            Tariff.connection_type == connection_type,
            Tariff.status.is_(True),
            Tariff.minimum_units <= units_consumed,
            (
                (Tariff.maximum_units.is_(None))
                | (Tariff.maximum_units >= units_consumed)
            ),
            Tariff.effective_from <= billing_date,
            (
                (Tariff.effective_to.is_(None))
                | (Tariff.effective_to >= billing_date)
            ),
        ).order_by(
            Tariff.minimum_units.desc()
        )

        return db.scalars(statement).first()

    def delete(
        self,
        db: Session,
        tariff: Tariff,
    ) -> None:
        db.delete(tariff)
        db.commit()