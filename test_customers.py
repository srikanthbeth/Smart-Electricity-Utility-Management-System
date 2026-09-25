import os
from datetime import date
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "smart_electricity_utility_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app

from models.connection import (
    Connection,
    ConnectionStatus,
    ConnectionType,
)


client = TestClient(app)

CUSTOMERS_URL = "/api/v1/customers"


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def cleanup_customers():
    db = SessionLocal()

    try:
        # Delete connections first because they reference customers.
        db.execute(text("DELETE FROM connections"))
        db.execute(text("DELETE FROM customers"))
        db.commit()
    finally:
        db.close()


def customer_payload(
    city="Hyderabad",
    status="Active",
):
    unique_id = uuid4().hex[:8]

    return {
        "customer_number": f"CUST-{unique_id}",
        "full_name": "John Customer",
        "email": f"john_{unique_id}@example.com",
        "phone": "9876543210",
        "address": "123 Main Street",
        "city": city,
        "status": status,
    }


def create_customer(
    city="Hyderabad",
    status="Active",
):
    payload = customer_payload(
        city=city,
        status=status,
    )

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    return response.json(), payload


def create_connection_for_customer(
    customer_id,
    connection_type="Residential",
    connection_number=None,
):
    db = SessionLocal()

    try:
        if connection_number is None:
            connection_number = (
                f"CONN-{uuid4().hex[:8]}"
            )

        connection = Connection(
            customer_id=customer_id,
            connection_number=connection_number,
            connection_type=ConnectionType(
                connection_type
            ),
            sanctioned_load=5.0,
            tariff_type="Domestic",
            connection_date=date.today(),
            status=ConnectionStatus.ACTIVE,
        )

        db.add(connection)
        db.commit()
        db.refresh(connection)

        return connection.id

    finally:
        db.close()


# ============================================================
# BASIC CUSTOMER TESTS
# ============================================================


def test_create_customer():
    cleanup_customers()

    payload = customer_payload()

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_number"] == payload["customer_number"]
    assert data["full_name"] == payload["full_name"]
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["address"] == payload["address"]
    assert data["city"] == payload["city"]
    assert data["status"] == "Active"


def test_get_customers():
    cleanup_customers()

    payload = customer_payload()

    create_response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(CUSTOMERS_URL)

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert "items" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data
    assert "total_pages" in data

    assert isinstance(data["items"], list)

    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] == 1
    assert data["total_pages"] == 1

    assert len(data["items"]) == 1

    assert (
        data["items"][0]["customer_number"]
        == payload["customer_number"]
    )


def test_get_customer_by_id():
    cleanup_customers()

    payload = customer_payload()

    create_response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.get(
        f"{CUSTOMERS_URL}/{customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["customer_number"] == payload["customer_number"]


def test_get_customer_not_found():
    cleanup_customers()

    response = client.get(
        f"{CUSTOMERS_URL}/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_update_customer():
    cleanup_customers()

    payload = customer_payload()

    create_response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    update_payload = {
        "full_name": "Updated Customer",
        "phone": "9123456789",
        "city": "Bengaluru",
    }

    response = client.put(
        f"{CUSTOMERS_URL}/{customer_id}",
        json=update_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == "Updated Customer"
    assert data["phone"] == "9123456789"
    assert data["city"] == "Bengaluru"

    assert data["customer_number"] == payload["customer_number"]
    assert data["email"] == payload["email"]


def test_update_customer_status_to_suspended():
    cleanup_customers()

    payload = customer_payload()

    create_response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.put(
        f"{CUSTOMERS_URL}/{customer_id}",
        json={
            "status": "Suspended",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Suspended"


def test_update_customer_status_to_closed():
    cleanup_customers()

    payload = customer_payload()

    create_response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.put(
        f"{CUSTOMERS_URL}/{customer_id}",
        json={
            "status": "Closed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Closed"


def test_duplicate_customer_number():
    cleanup_customers()

    first_payload = customer_payload()

    response = client.post(
        CUSTOMERS_URL,
        json=first_payload,
    )

    assert response.status_code == 201

    second_payload = customer_payload()

    second_payload["customer_number"] = (
        first_payload["customer_number"]
    )

    response = client.post(
        CUSTOMERS_URL,
        json=second_payload,
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Customer number already exists"
    )


def test_duplicate_customer_email():
    cleanup_customers()

    first_payload = customer_payload()

    response = client.post(
        CUSTOMERS_URL,
        json=first_payload,
    )

    assert response.status_code == 201

    second_payload = customer_payload()

    second_payload["email"] = first_payload["email"]

    response = client.post(
        CUSTOMERS_URL,
        json=second_payload,
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Customer email already exists"
    )


def test_update_customer_with_duplicate_email():
    cleanup_customers()

    first_payload = customer_payload()
    second_payload = customer_payload()

    first_response = client.post(
        CUSTOMERS_URL,
        json=first_payload,
    )

    second_response = client.post(
        CUSTOMERS_URL,
        json=second_payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    second_customer_id = second_response.json()["id"]

    response = client.put(
        f"{CUSTOMERS_URL}/{second_customer_id}",
        json={
            "email": first_payload["email"],
        },
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Customer email already exists"
    )


def test_delete_customer():
    cleanup_customers()

    payload = customer_payload()

    create_response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    delete_response = client.delete(
        f"{CUSTOMERS_URL}/{customer_id}"
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"{CUSTOMERS_URL}/{customer_id}"
    )

    assert get_response.status_code == 404


def test_delete_customer_not_found():
    cleanup_customers()

    response = client.delete(
        f"{CUSTOMERS_URL}/999999"
    )

    assert response.status_code == 404


def test_invalid_customer_email():
    cleanup_customers()

    payload = customer_payload()

    payload["email"] = "invalid-email"

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_missing_required_customer_fields():
    cleanup_customers()

    response = client.post(
        CUSTOMERS_URL,
        json={},
    )

    assert response.status_code == 422


def test_invalid_customer_status():
    cleanup_customers()

    payload = customer_payload()

    payload["status"] = "InvalidStatus"

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_create_suspended_customer():
    cleanup_customers()

    payload = customer_payload()

    payload["status"] = "Suspended"

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "Suspended"


def test_create_closed_customer():
    cleanup_customers()

    payload = customer_payload()

    payload["status"] = "Closed"

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "Closed"


# ============================================================
# LEVEL 13 - CITY FILTER
# ============================================================


def test_filter_customers_by_city():
    cleanup_customers()

    hyderabad_customer, _ = create_customer(
        city="Hyderabad"
    )

    create_customer(
        city="Bengaluru"
    )

    create_customer(
        city="Chennai"
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == hyderabad_customer["id"]
    )

    assert (
        data["items"][0]["city"]
        == "Hyderabad"
    )


# ============================================================
# LEVEL 13 - STATUS FILTER
# ============================================================


def test_filter_customers_by_status():
    cleanup_customers()

    active_customer, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    create_customer(
        city="Bengaluru",
        status="Suspended",
    )

    create_customer(
        city="Chennai",
        status="Closed",
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "status": "Active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == active_customer["id"]
    )

    assert data["items"][0]["status"] == "Active"


# ============================================================
# LEVEL 13 - CONNECTION TYPE FILTER
# ============================================================


def test_filter_customers_by_connection_type():
    cleanup_customers()

    residential_customer, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    commercial_customer, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    create_customer(
        city="Chennai",
        status="Active",
    )

    create_connection_for_customer(
        customer_id=residential_customer["id"],
        connection_type="Residential",
    )

    create_connection_for_customer(
        customer_id=commercial_customer["id"],
        connection_type="Commercial",
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "connection_type": "Residential",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == residential_customer["id"]
    )

    assert (
        data["items"][0]["customer_number"]
        == residential_customer["customer_number"]
    )


# ============================================================
# LEVEL 13 - MULTIPLE FILTERS
# ============================================================


def test_filter_customers_by_multiple_filters():
    cleanup_customers()

    matching_customer, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    wrong_status_customer, _ = create_customer(
        city="Hyderabad",
        status="Suspended",
    )

    wrong_city_customer, _ = create_customer(
        city="Bengaluru",
        status="Active",
    )

    create_connection_for_customer(
        customer_id=matching_customer["id"],
        connection_type="Residential",
    )

    create_connection_for_customer(
        customer_id=wrong_status_customer["id"],
        connection_type="Residential",
    )

    create_connection_for_customer(
        customer_id=wrong_city_customer["id"],
        connection_type="Residential",
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "city": "Hyderabad",
            "status": "Active",
            "connection_type": "Residential",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == matching_customer["id"]
    )

    assert data["items"][0]["city"] == "Hyderabad"
    assert data["items"][0]["status"] == "Active"


# ============================================================
# LEVEL 13 - PAGINATION
# ============================================================


def test_customer_pagination():
    cleanup_customers()

    created_customers = []

    for _ in range(5):
        customer, _ = create_customer()
        created_customers.append(customer)

    response = client.get(
        CUSTOMERS_URL,
        params={
            "page": 1,
            "limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 2


def test_customer_second_page():
    cleanup_customers()

    for _ in range(5):
        create_customer()

    response = client.get(
        CUSTOMERS_URL,
        params={
            "page": 2,
            "limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 2


def test_customer_last_page():
    cleanup_customers()

    for _ in range(5):
        create_customer()

    response = client.get(
        CUSTOMERS_URL,
        params={
            "page": 3,
            "limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 3
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 1


# ============================================================
# LEVEL 13 - SORTING ASCENDING
# ============================================================


def test_sort_customers_by_full_name_ascending():
    cleanup_customers()

    first_payload = customer_payload()
    second_payload = customer_payload()
    third_payload = customer_payload()

    first_payload["full_name"] = "Charlie Customer"
    second_payload["full_name"] = "Alice Customer"
    third_payload["full_name"] = "Bob Customer"

    client.post(
        CUSTOMERS_URL,
        json=first_payload,
    )

    client.post(
        CUSTOMERS_URL,
        json=second_payload,
    )

    client.post(
        CUSTOMERS_URL,
        json=third_payload,
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "sort_by": "full_name",
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    data = response.json()

    names = [
        customer["full_name"]
        for customer in data["items"]
    ]

    assert names == [
        "Alice Customer",
        "Bob Customer",
        "Charlie Customer",
    ]


# ============================================================
# LEVEL 13 - SORTING DESCENDING
# ============================================================


def test_sort_customers_by_full_name_descending():
    cleanup_customers()

    first_payload = customer_payload()
    second_payload = customer_payload()
    third_payload = customer_payload()

    first_payload["full_name"] = "Charlie Customer"
    second_payload["full_name"] = "Alice Customer"
    third_payload["full_name"] = "Bob Customer"

    client.post(
        CUSTOMERS_URL,
        json=first_payload,
    )

    client.post(
        CUSTOMERS_URL,
        json=second_payload,
    )

    client.post(
        CUSTOMERS_URL,
        json=third_payload,
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "sort_by": "full_name",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200

    data = response.json()

    names = [
        customer["full_name"]
        for customer in data["items"]
    ]

    assert names == [
        "Charlie Customer",
        "Bob Customer",
        "Alice Customer",
    ]


# ============================================================
# LEVEL 13 - FILTER + PAGINATION + SORTING
# ============================================================


def test_customer_filter_pagination_and_sorting():
    cleanup_customers()

    customer_1, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    customer_2, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    customer_3, _ = create_customer(
        city="Hyderabad",
        status="Active",
    )

    create_customer(
        city="Bengaluru",
        status="Active",
    )

    create_customer(
        city="Hyderabad",
        status="Suspended",
    )

    # Give the matching customers different names.
    db = SessionLocal()

    try:
        db_customer_1 = db.get(
            type(
                "CustomerProxy",
                (),
                {},
            ),
            None,
        )
    except Exception:
        db_customer_1 = None
    finally:
        db.close()

    # Update names through the API.
    client.put(
        f"{CUSTOMERS_URL}/{customer_1['id']}",
        json={
            "full_name": "Charlie Customer",
        },
    )

    client.put(
        f"{CUSTOMERS_URL}/{customer_2['id']}",
        json={
            "full_name": "Alice Customer",
        },
    )

    client.put(
        f"{CUSTOMERS_URL}/{customer_3['id']}",
        json={
            "full_name": "Bob Customer",
        },
    )

    response = client.get(
        CUSTOMERS_URL,
        params={
            "city": "Hyderabad",
            "status": "Active",
            "page": 1,
            "limit": 2,
            "sort_by": "full_name",
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2

    assert data["total"] == 3
    assert data["total_pages"] == 2

    assert len(data["items"]) == 2

    names = [
        customer["full_name"]
        for customer in data["items"]
    ]

    assert names == [
        "Alice Customer",
        "Bob Customer",
    ]

    for customer in data["items"]:
        assert customer["city"] == "Hyderabad"
        assert customer["status"] == "Active"


# ============================================================
# LEVEL 13 - INVALID PAGINATION
# ============================================================


def test_customer_invalid_page():
    cleanup_customers()

    response = client.get(
        CUSTOMERS_URL,
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_customer_invalid_limit():
    cleanup_customers()

    response = client.get(
        CUSTOMERS_URL,
        params={
            "limit": 0,
        },
    )

    assert response.status_code == 422


def test_customer_limit_greater_than_100():
    cleanup_customers()

    response = client.get(
        CUSTOMERS_URL,
        params={
            "limit": 101,
        },
    )

    assert response.status_code == 422


# ============================================================
# LEVEL 13 - INVALID SORT ORDER
# ============================================================


def test_customer_invalid_sort_order():
    cleanup_customers()

    response = client.get(
        CUSTOMERS_URL,
        params={
            "sort_order": "invalid",
        },
    )

    assert response.status_code == 422