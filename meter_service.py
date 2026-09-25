from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.connection import Connection
from models.meter import Meter, MeterStatus
from repositories.meter_repository import MeterRepository
from schemas.meter import MeterCreate, MeterUpdate


class MeterService:

    @staticmethod
    def create_meter(
        db: Session,
        data: MeterCreate,
    ) -> Meter:

        # Check connection exists
        connection = db.get(
            Connection,
            data.connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        # Check meter number uniqueness
        existing_meter = (
            MeterRepository.get_by_meter_number(
                db,
                data.meter_number,
            )
        )

        if existing_meter:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meter number already exists",
            )

        # Only one active meter per connection
        if data.meter_status == MeterStatus.ACTIVE:
            active_meter = (
                MeterRepository.get_active_by_connection(
                    db,
                    data.connection_id,
                )
            )

            if active_meter:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Connection already has an active meter",
                )

        # Current reading cannot be below initial reading
        if data.current_reading < data.initial_reading:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current reading cannot be less than initial reading",
            )

        meter = Meter(
            connection_id=data.connection_id,
            meter_number=data.meter_number,
            meter_type=data.meter_type,
            installation_date=data.installation_date,
            initial_reading=data.initial_reading,
            current_reading=data.current_reading,
            meter_status=data.meter_status,
        )

        return MeterRepository.create(
            db,
            meter,
        )

    @staticmethod
    def get_meters(
        db: Session,
    ) -> list[Meter]:

        return MeterRepository.get_all(db)

    @staticmethod
    def get_meter(
        db: Session,
        meter_id: int,
    ) -> Meter:

        meter = MeterRepository.get_by_id(
            db,
            meter_id,
        )

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found",
            )

        return meter

    @staticmethod
    def update_meter(
        db: Session,
        meter_id: int,
        data: MeterUpdate,
    ) -> Meter:

        meter = MeterService.get_meter(
            db,
            meter_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        new_initial_reading = update_data.get(
            "initial_reading",
            meter.initial_reading,
        )

        new_current_reading = update_data.get(
            "current_reading",
            meter.current_reading,
        )

        if new_current_reading < new_initial_reading:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current reading cannot be less than initial reading",
            )

        if update_data.get("meter_status") == MeterStatus.ACTIVE:
            active_meter = (
                MeterRepository.get_active_by_connection(
                    db,
                    meter.connection_id,
                )
            )

            if (
                active_meter
                and active_meter.id != meter.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Connection already has an active meter",
                )

        return MeterRepository.update(
            db,
            meter,
            update_data,
        )

    @staticmethod
    def replace_meter(
        db: Session,
        meter_id: int,
    ) -> Meter:

        old_meter = MeterService.get_meter(
            db,
            meter_id,
        )

        if old_meter.meter_status == MeterStatus.REMOVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meter is already removed",
            )

        old_meter.meter_status = MeterStatus.REMOVED

        db.commit()
        db.refresh(old_meter)

        return old_meter