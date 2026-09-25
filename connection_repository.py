from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from models.connection import Connection


class ConnectionRepository:

    @staticmethod
    def create(
        db: Session,
        connection: Connection,
    ) -> Connection:
        db.add(connection)
        db.commit()
        db.refresh(connection)

        return connection

    @staticmethod
    def get_by_id(
        db: Session,
        connection_id: int,
    ) -> Connection | None:
        return db.execute(
            select(Connection).where(
                Connection.id == connection_id
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_by_connection_number(
        db: Session,
        connection_number: str,
    ) -> Connection | None:
        return db.execute(
            select(Connection).where(
                Connection.connection_number
                == connection_number
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_all(
        db: Session,
        tariff_type: str | None = None,
        connection_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Connection], int, int]:

        statement = select(Connection)

        # -------------------------
        # FILTER: TARIFF TYPE
        # -------------------------
        if tariff_type:
            statement = statement.where(
                Connection.tariff_type == tariff_type
            )

        # -------------------------
        # FILTER: CONNECTION TYPE
        # -------------------------
        if connection_type:
            statement = statement.where(
                Connection.connection_type
                == connection_type
            )

        # -------------------------
        # FILTER: STATUS
        # -------------------------
        if status:
            statement = statement.where(
                Connection.status == status
            )

        # -------------------------
        # SORTING
        # -------------------------

        allowed_sort_columns = {
            "id": Connection.id,
            "customer_id": Connection.customer_id,
            "connection_number": Connection.connection_number,
            "connection_type": Connection.connection_type,
            "sanctioned_load": Connection.sanctioned_load,
            "tariff_type": Connection.tariff_type,
            "connection_date": Connection.connection_date,
            "status": Connection.status,
        }

        sort_column = allowed_sort_columns.get(
            sort_by,
            Connection.id,
        )

        if sort_order.lower() == "desc":
            statement = statement.order_by(
                desc(sort_column)
            )
        else:
            statement = statement.order_by(
                asc(sort_column)
            )

        # -------------------------
        # TOTAL COUNT
        # -------------------------

        count_statement = select(
            func.count()
        ).select_from(
            statement.order_by(None).subquery()
        )

        total = db.execute(
            count_statement
        ).scalar_one()

        # -------------------------
        # PAGINATION
        # -------------------------

        offset = (page - 1) * limit

        statement = statement.offset(
            offset
        ).limit(
            limit
        )

        connections = list(
            db.execute(
                statement
            ).scalars().all()
        )

        total_pages = (
            (total + limit - 1) // limit
            if total > 0
            else 0
        )

        return (
            connections,
            total,
            total_pages,
        )

    @staticmethod
    def update(
        db: Session,
        connection: Connection,
        data: dict,
    ) -> Connection:

        for field, value in data.items():
            setattr(connection, field, value)

        db.commit()
        db.refresh(connection)

        return connection