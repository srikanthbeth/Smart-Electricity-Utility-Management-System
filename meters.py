from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.meter import (
    MeterCreate,
    MeterResponse,
    MeterUpdate,
)
from services.meter_service import MeterService


router = APIRouter(
    prefix="/meters",
    tags=["Meters"],
)


@router.post(
    "",
    response_model=MeterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meter(
    data: MeterCreate,
    db: Session = Depends(get_db),
):
    return MeterService.create_meter(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[MeterResponse],
)
def get_meters(
    db: Session = Depends(get_db),
):
    return MeterService.get_meters(db)


@router.get(
    "/{meter_id}",
    response_model=MeterResponse,
)
def get_meter(
    meter_id: int,
    db: Session = Depends(get_db),
):
    return MeterService.get_meter(
        db,
        meter_id,
    )


@router.put(
    "/{meter_id}",
    response_model=MeterResponse,
)
def update_meter(
    meter_id: int,
    data: MeterUpdate,
    db: Session = Depends(get_db),
):
    return MeterService.update_meter(
        db,
        meter_id,
        data,
    )


@router.post(
    "/{meter_id}/replace",
    response_model=MeterResponse,
)
def replace_meter(
    meter_id: int,
    db: Session = Depends(get_db),
):
    return MeterService.replace_meter(
        db,
        meter_id,
    )