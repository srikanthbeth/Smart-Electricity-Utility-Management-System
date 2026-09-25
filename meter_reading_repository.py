from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.meter import Meter
from models.meter_reading import MeterReading


class MeterReadingRepository:

    @staticmethod
    def create(
        db: Session,
        reading: MeterReading,
    ) -> MeterReading:

        db.add(reading)
        db.commit()
        db.refresh(reading)

        return reading

    @staticmethod
    def get_by_id(
        db: Session,
        reading_id: int,
    ) -> MeterReading | None:

        return db.execute(
            select(MeterReading).where(
                MeterReading.id == reading_id
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[MeterReading]:

        return list(
            db.execute(
                select(MeterReading).order_by(
                    MeterReading.reading_date
                )
            )
            .scalars()
            .all()
        )

    @staticmethod
    def get_by_meter_and_period(
        db: Session,
        meter_id: int,
        reading_date: date,
    ) -> MeterReading | None:

        return db.execute(
            select(MeterReading).where(
                MeterReading.meter_id == meter_id,
                MeterReading.reading_year == reading_date.year,
                MeterReading.reading_month == reading_date.month,
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_by_meter(
        db: Session,
        meter_id: int,
    ) -> list[MeterReading]:

        return list(
            db.execute(
                select(MeterReading)
                .where(
                    MeterReading.meter_id == meter_id
                )
                .order_by(
                    MeterReading.reading_date
                )
            )
            .scalars()
            .all()
        )

    @staticmethod
    def get_by_connection(
        db: Session,
        connection_id: int,
    ) -> list[MeterReading]:

        return list(
            db.execute(
                select(MeterReading)
                .join(
                    Meter,
                    MeterReading.meter_id == Meter.id,
                )
                .where(
                    Meter.connection_id == connection_id
                )
                .order_by(
                    MeterReading.reading_date
                )
            )
            .scalars()
            .all()
        )

    @staticmethod
    def get_by_connection_and_month(
        db: Session,
        connection_id: int,
        billing_month: date,
    ) -> MeterReading | None:

        return db.execute(
            select(MeterReading)
            .join(
                Meter,
                MeterReading.meter_id == Meter.id,
            )
            .where(
                Meter.connection_id == connection_id,
                MeterReading.reading_year == billing_month.year,
                MeterReading.reading_month == billing_month.month,
            )
            .order_by(
                MeterReading.reading_date.desc()
            )
        ).scalars().first()