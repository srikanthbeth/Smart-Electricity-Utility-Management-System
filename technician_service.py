from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.technician import Technician
from repositories.technician_repository import (
    TechnicianRepository,
)
from schemas.technician import (
    TechnicianAvailabilityUpdate,
    TechnicianCreate,
)


class TechnicianService:

    def __init__(self):
        self.repository = TechnicianRepository()

    def create_technician(
        self,
        db: Session,
        data: TechnicianCreate,
    ) -> Technician:

        existing = self.repository.get_by_employee_id(
            db,
            data.employee_id,
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee ID already exists",
            )

        technician = Technician(
            name=data.name,
            employee_id=data.employee_id,
            phone=data.phone,
            specialization=data.specialization,
            availability_status=data.availability_status,
        )

        return self.repository.create(
            db,
            technician,
        )

    def get_all_technicians(
        self,
        db: Session,
    ) -> list[Technician]:
        return self.repository.get_all(db)

    def get_technician(
        self,
        db: Session,
        technician_id: int,
    ) -> Technician:

        technician = self.repository.get_by_id(
            db,
            technician_id,
        )

        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician not found",
            )

        return technician

    def update_availability(
        self,
        db: Session,
        technician_id: int,
        data: TechnicianAvailabilityUpdate,
    ) -> Technician:

        technician = self.get_technician(
            db,
            technician_id,
        )

        technician.availability_status = (
            data.availability_status
        )

        return self.repository.update(
            db,
            technician,
        )