from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.meter_reading import (
    MeterReadingCreate,
    MeterReadingResponse,
)
from services.meter_reading_service import (
    MeterReadingService,
)


router = APIRouter(
    prefix="/meter-readings",
    tags=["Meter Readings"],
)


@router.post(
    "",
    response_model=MeterReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meter_reading(
    data: MeterReadingCreate,
    db: Session = Depends(get_db),
):
    return MeterReadingService.create_reading(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[MeterReadingResponse],
)
def get_meter_readings(
    db: Session = Depends(get_db),
):
    return MeterReadingService.get_readings(
        db
    )


meter_reading_meter_router = APIRouter(
    prefix="/meters",
    tags=["Meter Readings"],
)


@meter_reading_meter_router.get(
    "/{meter_id}/readings",
    response_model=list[MeterReadingResponse],
)
def get_readings_by_meter(
    meter_id: int,
    db: Session = Depends(get_db),
):
    return MeterReadingService.get_meter_readings(
        db,
        meter_id,
    )


meter_reading_connection_router = APIRouter(
    prefix="/connections",
    tags=["Meter Readings"],
)


@meter_reading_connection_router.get(
    "/{connection_id}/readings",
    response_model=list[MeterReadingResponse],
)
def get_readings_by_connection(
    connection_id: int,
    db: Session = Depends(get_db),
):
    return MeterReadingService.get_connection_readings(
        db,
        connection_id,
    )