from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.meter import Meter, MeterStatus
from models.meter_reading import MeterReading
from repositories.meter_reading_repository import (
    MeterReadingRepository,
)
from schemas.meter_reading import MeterReadingCreate


class MeterReadingService:

    @staticmethod
    def create_reading(
        db: Session,
        data: MeterReadingCreate,
    ) -> MeterReading:

        # Check meter exists
        meter = db.get(
            Meter,
            data.meter_id,
        )

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found",
            )

        # Only active meters can receive readings
        if meter.meter_status != MeterStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active meters can receive readings",
            )

        # Current reading cannot be lower
        # than previous reading
        if data.current_reading < data.previous_reading:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Current reading cannot be lower "
                    "than previous reading"
                ),
            )

        # Calculate consumption
        units_consumed = (
            data.current_reading
            - data.previous_reading
        )

        # Extra protection against negative consumption
        if units_consumed < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Negative consumption is not allowed",
            )

        # Check duplicate billing period
        existing_reading = (
            MeterReadingRepository.get_by_meter_and_period(
                db,
                data.meter_id,
                data.reading_date,
            )
        )

        if existing_reading:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Reading already exists for "
                    "this meter and billing period"
                ),
            )

        reading = MeterReading(
            meter_id=data.meter_id,
            reading_date=data.reading_date,
            previous_reading=data.previous_reading,
            current_reading=data.current_reading,
            units_consumed=units_consumed,
            reading_source=data.reading_source,
            remarks=data.remarks,
            reading_year=data.reading_date.year,
            reading_month=data.reading_date.month,
        )

        return MeterReadingRepository.create(
            db,
            reading,
        )

    @staticmethod
    def get_readings(
        db: Session,
    ) -> list[MeterReading]:

        return MeterReadingRepository.get_all(db)

    @staticmethod
    def get_meter_readings(
        db: Session,
        meter_id: int,
    ) -> list[MeterReading]:

        meter = db.get(
            Meter,
            meter_id,
        )

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found",
            )

        return MeterReadingRepository.get_by_meter(
            db,
            meter_id,
        )

    @staticmethod
    def get_connection_readings(
        db: Session,
        connection_id: int,
    ) -> list[MeterReading]:

        from models.connection import Connection

        connection = db.get(
            Connection,
            connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return MeterReadingRepository.get_by_connection(
            db,
            connection_id,
        )