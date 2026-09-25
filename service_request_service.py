from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.connection import Connection
from models.customer import Customer
from models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
    ServiceRequestType,
)
from repositories.service_request_repository import (
    ServiceRequestRepository,
)
from schemas.service_request import ServiceRequestCreate


class ServiceRequestService:

    def __init__(self):
        self.repository = ServiceRequestRepository()

    def create_service_request(
        self,
        db: Session,
        data: ServiceRequestCreate,
    ) -> ServiceRequest:

        customer = db.get(
            Customer,
            data.customer_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        connection = None

        if data.connection_id is not None:
            connection = db.get(
                Connection,
                data.connection_id,
            )

            if connection is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found",
                )

            if connection.customer_id != data.customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Connection does not belong "
                        "to the customer"
                    ),
                )

        if (
            data.request_type
            != ServiceRequestType.NEW_CONNECTION
            and data.connection_id is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Connection ID is required for "
                    "this service request"
                ),
            )

        service_request = ServiceRequest(
            customer_id=data.customer_id,
            connection_id=data.connection_id,
            request_type=data.request_type,
            description=data.description,
            requested_date=data.requested_date,
            status=ServiceRequestStatus.SUBMITTED,
        )

        return self.repository.create(
            db,
            service_request,
        )

    def get_all_service_requests(
        self,
        db: Session,
    ) -> list[ServiceRequest]:

        return self.repository.get_all(db)

    def get_service_request(
        self,
        db: Session,
        service_request_id: int,
    ) -> ServiceRequest:

        service_request = self.repository.get_by_id(
            db,
            service_request_id,
        )

        if service_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        return service_request

    def approve_service_request(
        self,
        db: Session,
        service_request_id: int,
    ) -> ServiceRequest:

        service_request = self.get_service_request(
            db,
            service_request_id,
        )

        if service_request.status != (
            ServiceRequestStatus.SUBMITTED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only submitted requests can "
                    "be approved"
                ),
            )

        service_request.status = (
            ServiceRequestStatus.APPROVED
        )

        return self.repository.update(
            db,
            service_request,
        )

    def reject_service_request(
        self,
        db: Session,
        service_request_id: int,
    ) -> ServiceRequest:

        service_request = self.get_service_request(
            db,
            service_request_id,
        )

        if service_request.status != (
            ServiceRequestStatus.SUBMITTED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only submitted requests can "
                    "be rejected"
                ),
            )

        service_request.status = (
            ServiceRequestStatus.REJECTED
        )

        return self.repository.update(
            db,
            service_request,
        )

    def complete_service_request(
        self,
        db: Session,
        service_request_id: int,
    ) -> ServiceRequest:

        service_request = self.get_service_request(
            db,
            service_request_id,
        )

        if service_request.status != (
            ServiceRequestStatus.APPROVED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only approved requests can "
                    "be completed"
                ),
            )

        service_request.status = (
            ServiceRequestStatus.COMPLETED
        )

        return self.repository.update(
            db,
            service_request,
        )