from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.technician import (
    TechnicianAvailabilityUpdate,
    TechnicianCreate,
    TechnicianResponse,
)
from services.technician_service import TechnicianService


router = APIRouter(
    prefix="/technicians",
    tags=["Technicians"],
)

service = TechnicianService()


@router.post(
    "",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_technician(
    data: TechnicianCreate,
    db: Session = Depends(get_db),
):
    return service.create_technician(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[TechnicianResponse],
)
def get_technicians(
    db: Session = Depends(get_db),
):
    return service.get_all_technicians(db)


@router.get(
    "/{technician_id}",
    response_model=TechnicianResponse,
)
def get_technician(
    technician_id: int,
    db: Session = Depends(get_db),
):
    return service.get_technician(
        db,
        technician_id,
    )


@router.put(
    "/{technician_id}/availability",
    response_model=TechnicianResponse,
)
def update_technician_availability(
    technician_id: int,
    data: TechnicianAvailabilityUpdate,
    db: Session = Depends(get_db),
):
    return service.update_availability(
        db,
        technician_id,
        data,
    )