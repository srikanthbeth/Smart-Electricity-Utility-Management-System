from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.customer import Customer
from repositories.customer_repository import (
    CustomerRepository,
)
from schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
)


class CustomerService:

    @staticmethod
    def create_customer(
        db: Session,
        data: CustomerCreate,
    ) -> Customer:

        existing_customer_number = (
            CustomerRepository.get_by_customer_number(
                db,
                data.customer_number,
            )
        )

        if existing_customer_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer number already exists",
            )

        existing_email = (
            CustomerRepository.get_by_email(
                db,
                str(data.email),
            )
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer email already exists",
            )

        customer = Customer(
            customer_number=data.customer_number,
            full_name=data.full_name,
            email=str(data.email),
            phone=data.phone,
            address=data.address,
            city=data.city,
            status=data.status,
        )

        return CustomerRepository.create(
            db,
            customer,
        )

    @staticmethod
    def get_customer(
        db: Session,
        customer_id: int,
    ) -> Customer:

        customer = CustomerRepository.get_by_id(
            db,
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer

    @staticmethod
    def get_customers(
        db: Session,
        city: str | None = None,
        status: str | None = None,
        connection_type: str | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
    ):

        return CustomerRepository.get_all(
            db=db,
            city=city,
            status=status,
            connection_type=connection_type,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    def update_customer(
        db: Session,
        customer_id: int,
        data: CustomerUpdate,
    ) -> Customer:

        customer = CustomerService.get_customer(
            db,
            customer_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "email" in update_data:

            existing_email = (
                CustomerRepository.get_by_email(
                    db,
                    str(update_data["email"]),
                )
            )

            if (
                existing_email
                and existing_email.id != customer.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer email already exists",
                )

            update_data["email"] = str(
                update_data["email"]
            )

        return CustomerRepository.update(
            db,
            customer,
            update_data,
        )

    @staticmethod
    def delete_customer(
        db: Session,
        customer_id: int,
    ) -> None:

        customer = CustomerService.get_customer(
            db,
            customer_id,
        )

        CustomerRepository.delete(
            db,
            customer,
        )