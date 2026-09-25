from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from models.connection import Connection
from models.customer import Customer


class CustomerRepository:

    @staticmethod
    def create(
        db: Session,
        customer: Customer,
    ) -> Customer:
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return customer

    @staticmethod
    def get_by_id(
        db: Session,
        customer_id: int,
    ) -> Customer | None:
        return db.execute(
            select(Customer).where(
                Customer.id == customer_id
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_by_customer_number(
        db: Session,
        customer_number: str,
    ) -> Customer | None:
        return db.execute(
            select(Customer).where(
                Customer.customer_number
                == customer_number
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_by_email(
        db: Session,
        email: str,
    ) -> Customer | None:
        return db.execute(
            select(Customer).where(
                Customer.email == email
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_all(
        db: Session,
        city: str | None = None,
        status: str | None = None,
        connection_type: str | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Customer], int, int]:

        statement = select(Customer)

        # -----------------------------------------------------------
        # CITY FILTER
        # -----------------------------------------------------------

        if city:
            statement = statement.where(
                Customer.city == city
            )

        # -----------------------------------------------------------
        # CUSTOMER STATUS FILTER
        # -----------------------------------------------------------

        if status:
            statement = statement.where(
                Customer.status == status
            )

        # -----------------------------------------------------------
        # CONNECTION TYPE FILTER
        # -----------------------------------------------------------

        if connection_type:
            statement = (
                statement
                .join(
                    Connection,
                    Connection.customer_id
                    == Customer.id,
                )
                .where(
                    Connection.connection_type
                    == connection_type
                )
                .distinct()
            )

        # -----------------------------------------------------------
        # SORTING
        # -----------------------------------------------------------

        allowed_sort_columns = {
            "id": Customer.id,
            "customer_number": Customer.customer_number,
            "full_name": Customer.full_name,
            "email": Customer.email,
            "phone": Customer.phone,
            "address": Customer.address,
            "city": Customer.city,
            "status": Customer.status,
        }

        sort_column = allowed_sort_columns.get(
            sort_by,
            Customer.id,
        )

        if sort_order.lower() == "desc":
            statement = statement.order_by(
                desc(sort_column),
                desc(Customer.id),
            )
        else:
            statement = statement.order_by(
                asc(sort_column),
                asc(Customer.id),
            )

        # -----------------------------------------------------------
        # TOTAL COUNT
        # -----------------------------------------------------------

        count_statement = select(
            func.count()
        ).select_from(
            statement.order_by(None).subquery()
        )

        total = db.execute(
            count_statement
        ).scalar_one()

        # -----------------------------------------------------------
        # PAGINATION
        # -----------------------------------------------------------

        offset = (page - 1) * limit

        statement = statement.offset(
            offset
        ).limit(
            limit
        )

        customers = list(
            db.execute(
                statement
            ).scalars().all()
        )

        # -----------------------------------------------------------
        # TOTAL PAGES
        # -----------------------------------------------------------

        total_pages = (
            (total + limit - 1) // limit
            if total > 0
            else 0
        )

        return (
            customers,
            total,
            total_pages,
        )

    @staticmethod
    def update(
        db: Session,
        customer: Customer,
        data: dict,
    ) -> Customer:

        for field, value in data.items():
            setattr(
                customer,
                field,
                value,
            )

        db.commit()
        db.refresh(customer)

        return customer

    @staticmethod
    def delete(
        db: Session,
        customer: Customer,
    ) -> None:

        db.delete(customer)
        db.commit()