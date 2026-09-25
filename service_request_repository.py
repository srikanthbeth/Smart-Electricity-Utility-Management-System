from sqlalchemy import select
from sqlalchemy.orm import Session

from models.service_request import ServiceRequest


class ServiceRequestRepository:

    def create(
        self,
        db: Session,
        service_request: ServiceRequest,
    ) -> ServiceRequest:

        db.add(service_request)
        db.commit()
        db.refresh(service_request)

        return service_request

    def get_by_id(
        self,
        db: Session,
        service_request_id: int,
    ) -> ServiceRequest | None:

        return db.get(
            ServiceRequest,
            service_request_id,
        )

    def get_all(
        self,
        db: Session,
    ) -> list[ServiceRequest]:

        statement = select(
            ServiceRequest
        ).order_by(
            ServiceRequest.id.desc()
        )

        return list(
            db.scalars(statement).all()
        )

    def update(
        self,
        db: Session,
        service_request: ServiceRequest,
    ) -> ServiceRequest:

        db.add(service_request)
        db.commit()
        db.refresh(service_request)

        return service_request