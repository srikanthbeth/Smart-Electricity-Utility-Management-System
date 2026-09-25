from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionUpdate,
)
from services.connection_service import ConnectionService


router = APIRouter(
    prefix="/connections",
    tags=["Connections"],
)


@router.post(
    "",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_connection(
    data: ConnectionCreate,
    db: Session = Depends(get_db),
):
    return ConnectionService.create_connection(
        db,
        data,
    )


@router.get("")
def get_connections(
    tariff_type: str | None = Query(
        default=None,
        description="Filter by tariff type",
    ),
    connection_type: str | None = Query(
        default=None,
        description="Filter by connection type",
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by connection status",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of connections per page",
    ),
    sort_by: str = Query(
        default="id",
        description="Field used for sorting",
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    db: Session = Depends(get_db),
):
    connections, total, total_pages = (
        ConnectionService.get_connections(
            db=db,
            tariff_type=tariff_type,
            connection_type=connection_type,
            status=status_filter,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )

    return {
        "items": connections,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }


@router.get(
    "/{connection_id}",
    response_model=ConnectionResponse,
)
def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
):
    return ConnectionService.get_connection(
        db,
        connection_id,
    )


@router.put(
    "/{connection_id}",
    response_model=ConnectionResponse,
)
def update_connection(
    connection_id: int,
    data: ConnectionUpdate,
    db: Session = Depends(get_db),
):
    return ConnectionService.update_connection(
        db,
        connection_id,
        data,
    )


@router.post(
    "/{connection_id}/disconnect",
    response_model=ConnectionResponse,
)
def disconnect_connection(
    connection_id: int,
    db: Session = Depends(get_db),
):
    return ConnectionService.disconnect_connection(
        db,
        connection_id,
    )