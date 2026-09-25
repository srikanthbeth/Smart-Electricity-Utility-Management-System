from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.tariff import (
    TariffCreate,
    TariffResponse,
    TariffUpdate,
)
from services.tariff_service import TariffService


router = APIRouter(
    prefix="/tariffs",
    tags=["Tariffs"],
)

service = TariffService()


@router.post(
    "",
    response_model=TariffResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tariff(
    data: TariffCreate,
    db: Session = Depends(get_db),
):
    return service.create_tariff(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[TariffResponse],
)
def get_tariffs(
    db: Session = Depends(get_db),
):
    return service.get_tariffs(db)


@router.get(
    "/{tariff_id}",
    response_model=TariffResponse,
)
def get_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
):
    return service.get_tariff(
        db,
        tariff_id,
    )


@router.put(
    "/{tariff_id}",
    response_model=TariffResponse,
)
def update_tariff(
    tariff_id: int,
    data: TariffUpdate,
    db: Session = Depends(get_db),
):
    return service.update_tariff(
        db,
        tariff_id,
        data,
    )


@router.delete(
    "/{tariff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
):
    service.delete_tariff(
        db,
        tariff_id,
    )

    return None