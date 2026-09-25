from sqlalchemy import select
from sqlalchemy.orm import Session

from models.meter import Meter, MeterStatus


class MeterRepository:

    @staticmethod
    def create(
        db: Session,
        meter: Meter,
    ) -> Meter:
        db.add(meter)
        db.commit()
        db.refresh(meter)

        return meter

    @staticmethod
    def get_by_id(
        db: Session,
        meter_id: int,
    ) -> Meter | None:
        return db.execute(
            select(Meter).where(
                Meter.id == meter_id
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_by_meter_number(
        db: Session,
        meter_number: str,
    ) -> Meter | None:
        return db.execute(
            select(Meter).where(
                Meter.meter_number == meter_number
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Meter]:
        return list(
            db.execute(
                select(Meter).order_by(Meter.id)
            ).scalars().all()
        )

    @staticmethod
    def get_active_by_connection(
        db: Session,
        connection_id: int,
    ) -> Meter | None:
        return db.execute(
            select(Meter).where(
                Meter.connection_id == connection_id,
                Meter.meter_status == MeterStatus.ACTIVE,
            )
        ).scalar_one_or_none()

    @staticmethod
    def update(
        db: Session,
        meter: Meter,
        data: dict,
    ) -> Meter:

        for field, value in data.items():
            setattr(meter, field, value)

        db.commit()
        db.refresh(meter)

        return meter