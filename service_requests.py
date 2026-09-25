from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestResponse,
)
from services.service_request_service import (
    ServiceRequestService,
)


router = APIRouter(
    prefix="/service-requests",
    tags=["Service Requests"],
)

service = ServiceRequestService()


@router.post(
    "",
    response_model=ServiceRequestResponse,
    status_code=201,
)
def create_service_request(
    data: ServiceRequestCreate,
    db: Session = Depends(get_db),
):
    return service.create_service_request(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[ServiceRequestResponse],
)
def get_service_requests(
    db: Session = Depends(get_db),
):
    return service.get_all_service_requests(db)


@router.get(
    "/{service_request_id}",
    response_model=ServiceRequestResponse,
)
def get_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
):
    return service.get_service_request(
        db,
        service_request_id,
    )


@router.put(
    "/{service_request_id}/approve",
    response_model=ServiceRequestResponse,
)
def approve_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
):
    return service.approve_service_request(
        db,
        service_request_id,
    )


@router.put(
    "/{service_request_id}/reject",
    response_model=ServiceRequestResponse,
)
def reject_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
):
    return service.reject_service_request(
        db,
        service_request_id,
    )


@router.put(
    "/{service_request_id}/complete",
    response_model=ServiceRequestResponse,
)
def complete_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
):
    return service.complete_service_request(
        db,
        service_request_id,
    )