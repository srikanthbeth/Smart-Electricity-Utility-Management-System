from sqlalchemy import select
from sqlalchemy.orm import Session

from models.technician import Technician


class TechnicianRepository:

    def create(
        self,
        db: Session,
        technician: Technician,
    ) -> Technician:
        db.add(technician)
        db.commit()
        db.refresh(technician)

        return technician

    def get_by_id(
        self,
        db: Session,
        technician_id: int,
    ) -> Technician | None:
        return db.get(
            Technician,
            technician_id,
        )

    def get_all(
        self,
        db: Session,
    ) -> list[Technician]:
        statement = select(Technician).order_by(
            Technician.id.desc()
        )

        return list(
            db.scalars(statement).all()
        )

    def get_by_employee_id(
        self,
        db: Session,
        employee_id: str,
    ) -> Technician | None:
        statement = select(Technician).where(
            Technician.employee_id == employee_id
        )

        return db.scalars(statement).first()

    def update(
        self,
        db: Session,
        technician: Technician,
    ) -> Technician:
        db.add(technician)
        db.commit()
        db.refresh(technician)

        return technician