from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.connection import (
    Connection,
    ConnectionStatus,
)
from repositories.connection_repository import (
    ConnectionRepository,
)
from schemas.connection import (
    ConnectionCreate,
    ConnectionUpdate,
)


class ConnectionService:

    @staticmethod
    def create_connection(
        db: Session,
        data: ConnectionCreate,
    ) -> Connection:

        # Check customer exists
        from models.customer import Customer

        customer = db.get(
            Customer,
            data.customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        # Check connection number uniqueness
        existing = (
            ConnectionRepository
            .get_by_connection_number(
                db,
                data.connection_number,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Connection number already exists",
            )

        connection = Connection(
            customer_id=data.customer_id,
            connection_number=data.connection_number,
            connection_type=data.connection_type,
            sanctioned_load=data.sanctioned_load,
            tariff_type=data.tariff_type,
            connection_date=data.connection_date,
            status=data.status,
        )

        return ConnectionRepository.create(
            db,
            connection,
        )

    @staticmethod
    def get_connections(
        db: Session,
        tariff_type: str | None = None,
        connection_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
    ):

        return ConnectionRepository.get_all(
            db=db,
            tariff_type=tariff_type,
            connection_type=connection_type,
            status=status,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    def get_connection(
        db: Session,
        connection_id: int,
    ) -> Connection:

        connection = ConnectionRepository.get_by_id(
            db,
            connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return connection

    @staticmethod
    def update_connection(
        db: Session,
        connection_id: int,
        data: ConnectionUpdate,
    ) -> Connection:

        connection = ConnectionService.get_connection(
            db,
            connection_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        return ConnectionRepository.update(
            db,
            connection,
            update_data,
        )

    @staticmethod
    def disconnect_connection(
        db: Session,
        connection_id: int,
    ) -> Connection:

        connection = ConnectionService.get_connection(
            db,
            connection_id,
        )

        if connection.status == ConnectionStatus.DISCONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Connection is already disconnected",
            )

        connection.status = ConnectionStatus.DISCONNECTED

        db.commit()
        db.refresh(connection)

        return connection