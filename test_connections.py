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


client = TestClient(app)

CUSTOMERS_URL = "/api/v1/customers"
CONNECTIONS_URL = "/api/v1/connections"


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def cleanup_data():
    db = SessionLocal()

    try:
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
        "full_name": "Connection Customer",
        "email": f"customer_{unique_id}@example.com",
        "phone": "9876543210",
        "address": "123 Main Street",
        "city": city,
        "status": status,
    }


def create_customer(
    city="Hyderabad",
    status="Active",
):
    response = client.post(
        CUSTOMERS_URL,
        json=customer_payload(
            city=city,
            status=status,
        ),
    )

    assert response.status_code == 201

    return response.json()


def connection_payload(
    customer_id,
    connection_type="Residential",
    tariff_type="Domestic",
    status="Active",
    sanctioned_load=5.0,
):
    unique_id = uuid4().hex[:8]

    return {
        "customer_id": customer_id,
        "connection_number": f"CONN-{unique_id}",
        "connection_type": connection_type,
        "sanctioned_load": sanctioned_load,
        "tariff_type": tariff_type,
        "connection_date": str(date.today()),
        "status": status,
    }


def create_connection(
    customer_id,
    connection_type="Residential",
    tariff_type="Domestic",
    status="Active",
    sanctioned_load=5.0,
):
    response = client.post(
        CONNECTIONS_URL,
        json=connection_payload(
            customer_id=customer_id,
            connection_type=connection_type,
            tariff_type=tariff_type,
            status=status,
            sanctioned_load=sanctioned_load,
        ),
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# BASIC CONNECTION TESTS
# ============================================================


def test_create_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer["id"]
    assert data["connection_number"] == payload["connection_number"]
    assert data["connection_type"] == "Residential"
    assert data["sanctioned_load"] == 5.0
    assert data["tariff_type"] == "Domestic"
    assert data["status"] == "Active"


def test_get_connections():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    create_response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        CONNECTIONS_URL
    )

    assert response.status_code == 200

    data = response.json()

    # Level 13 pagination response
    assert isinstance(data, dict)

    assert "items" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data
    assert "total_pages" in data

    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] >= 1
    assert data["total_pages"] >= 1

    assert any(
        item["connection_number"]
        == payload["connection_number"]
        for item in data["items"]
    )


def test_get_connection_by_id():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    create_response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    response = client.get(
        f"{CONNECTIONS_URL}/{connection_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == connection_id
    assert data["customer_id"] == customer["id"]


def test_get_connection_not_found():
    cleanup_data()

    response = client.get(
        f"{CONNECTIONS_URL}/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


def test_create_connection_for_nonexistent_customer():
    cleanup_data()

    payload = connection_payload(
        customer_id=999999
    )

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_duplicate_connection_number():
    cleanup_data()

    customer = create_customer()

    first_payload = connection_payload(
        customer["id"]
    )

    first_response = client.post(
        CONNECTIONS_URL,
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_payload = connection_payload(
        customer["id"]
    )

    second_payload["connection_number"] = (
        first_payload["connection_number"]
    )

    response = client.post(
        CONNECTIONS_URL,
        json=second_payload,
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Connection number already exists"
    )


def test_same_customer_can_have_multiple_connections():
    cleanup_data()

    customer = create_customer()

    first_payload = connection_payload(
        customer["id"]
    )

    second_payload = connection_payload(
        customer["id"]
    )

    second_payload["connection_type"] = "Commercial"

    first_response = client.post(
        CONNECTIONS_URL,
        json=first_payload,
    )

    second_response = client.post(
        CONNECTIONS_URL,
        json=second_payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert (
        first_response.json()["customer_id"]
        == second_response.json()["customer_id"]
    )

    assert (
        first_response.json()["id"]
        != second_response.json()["id"]
    )


def test_update_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    create_response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    update_payload = {
        "connection_type": "Commercial",
        "sanctioned_load": 10.0,
        "tariff_type": "Commercial Tariff",
    }

    response = client.put(
        f"{CONNECTIONS_URL}/{connection_id}",
        json=update_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["connection_type"] == "Commercial"
    assert data["sanctioned_load"] == 10.0
    assert data["tariff_type"] == "Commercial Tariff"


def test_update_connection_status_to_suspended():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    create_response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    response = client.put(
        f"{CONNECTIONS_URL}/{connection_id}",
        json={
            "status": "Suspended",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Suspended"


def test_disconnect_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    create_response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    response = client.post(
        f"{CONNECTIONS_URL}/{connection_id}/disconnect"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == connection_id
    assert data["status"] == "Disconnected"


def test_disconnect_already_disconnected_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    create_response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    first_response = client.post(
        f"{CONNECTIONS_URL}/{connection_id}/disconnect"
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"{CONNECTIONS_URL}/{connection_id}/disconnect"
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Connection is already disconnected"
    )


def test_disconnect_nonexistent_connection():
    cleanup_data()

    response = client.post(
        f"{CONNECTIONS_URL}/999999/disconnect"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Connection not found"
    )


def test_invalid_connection_type():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["connection_type"] = "InvalidType"

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_connection_status():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["status"] = "InvalidStatus"

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_negative_sanctioned_load():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["sanctioned_load"] = -5

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_zero_sanctioned_load():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["sanctioned_load"] = 0

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_create_commercial_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["connection_type"] = "Commercial"

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["connection_type"] == "Commercial"


def test_create_industrial_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["connection_type"] = "Industrial"

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["connection_type"] == "Industrial"


def test_create_suspended_connection():
    cleanup_data()

    customer = create_customer()

    payload = connection_payload(
        customer["id"]
    )

    payload["status"] = "Suspended"

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "Suspended"


# ============================================================
# LEVEL 13 - FILTERING TESTS
# ============================================================


def test_filter_connections_by_tariff_type():
    cleanup_data()

    customer = create_customer()

    domestic = create_connection(
        customer["id"],
        tariff_type="Domestic",
    )

    commercial = create_connection(
        customer["id"],
        connection_type="Commercial",
        tariff_type="Commercial Tariff",
    )

    response = client.get(
        f"{CONNECTIONS_URL}?tariff_type=Domestic"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert isinstance(data["items"], list)

    assert data["total"] == 1

    assert data["items"][0]["id"] == domestic["id"]
    assert data["items"][0]["tariff_type"] == "Domestic"

    assert commercial["id"] != domestic["id"]


def test_filter_connections_by_connection_type():
    cleanup_data()

    customer = create_customer()

    residential = create_connection(
        customer["id"],
        connection_type="Residential",
    )

    commercial = create_connection(
        customer["id"],
        connection_type="Commercial",
    )

    response = client.get(
        f"{CONNECTIONS_URL}?connection_type=Commercial"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0]["id"] == commercial["id"]
    assert data["items"][0]["connection_type"] == "Commercial"

    assert commercial["id"] != residential["id"]


def test_filter_connections_by_status():
    cleanup_data()

    customer = create_customer()

    active = create_connection(
        customer["id"],
        status="Active",
    )

    suspended = create_connection(
        customer["id"],
        status="Suspended",
    )

    response = client.get(
        f"{CONNECTIONS_URL}?status=Suspended"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0]["id"] == suspended["id"]
    assert data["items"][0]["status"] == "Suspended"

    assert suspended["id"] != active["id"]


def test_filter_connections_with_multiple_filters():
    cleanup_data()

    customer = create_customer()

    matching = create_connection(
        customer["id"],
        connection_type="Residential",
        tariff_type="Domestic",
        status="Active",
    )

    create_connection(
        customer["id"],
        connection_type="Residential",
        tariff_type="Domestic",
        status="Suspended",
    )

    create_connection(
        customer["id"],
        connection_type="Commercial",
        tariff_type="Commercial Tariff",
        status="Active",
    )

    response = client.get(
        f"{CONNECTIONS_URL}"
        "?tariff_type=Domestic"
        "&connection_type=Residential"
        "&status=Active"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0]["id"] == matching["id"]
    assert data["items"][0]["tariff_type"] == "Domestic"
    assert data["items"][0]["connection_type"] == "Residential"
    assert data["items"][0]["status"] == "Active"


# ============================================================
# LEVEL 13 - PAGINATION TESTS
# ============================================================


def test_connections_pagination():
    cleanup_data()

    customer = create_customer()

    for load in [5.0, 10.0, 15.0, 20.0, 25.0]:
        create_connection(
            customer["id"],
            sanctioned_load=load,
        )

    response = client.get(
        f"{CONNECTIONS_URL}?page=1&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 2


def test_connections_second_page():
    cleanup_data()

    customer = create_customer()

    for load in [5.0, 10.0, 15.0, 20.0, 25.0]:
        create_connection(
            customer["id"],
            sanctioned_load=load,
        )

    response = client.get(
        f"{CONNECTIONS_URL}?page=2&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 2


def test_connections_last_page():
    cleanup_data()

    customer = create_customer()

    for load in [5.0, 10.0, 15.0, 20.0, 25.0]:
        create_connection(
            customer["id"],
            sanctioned_load=load,
        )

    response = client.get(
        f"{CONNECTIONS_URL}?page=3&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 3
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 1


def test_connections_page_beyond_available_pages():
    cleanup_data()

    customer = create_customer()

    create_connection(
        customer["id"]
    )

    response = client.get(
        f"{CONNECTIONS_URL}?page=10&limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 10
    assert data["limit"] == 10
    assert data["total"] == 1
    assert data["items"] == []


# ============================================================
# LEVEL 13 - SORTING TESTS
# ============================================================


def test_connections_sort_by_sanctioned_load_ascending():
    cleanup_data()

    customer = create_customer()

    create_connection(
        customer["id"],
        sanctioned_load=20.0,
    )

    create_connection(
        customer["id"],
        sanctioned_load=5.0,
    )

    create_connection(
        customer["id"],
        sanctioned_load=10.0,
    )

    response = client.get(
        f"{CONNECTIONS_URL}"
        "?sort_by=sanctioned_load"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    loads = [
        item["sanctioned_load"]
        for item in data["items"]
    ]

    assert loads == sorted(loads)


def test_connections_sort_by_sanctioned_load_descending():
    cleanup_data()

    customer = create_customer()

    create_connection(
        customer["id"],
        sanctioned_load=20.0,
    )

    create_connection(
        customer["id"],
        sanctioned_load=5.0,
    )

    create_connection(
        customer["id"],
        sanctioned_load=10.0,
    )

    response = client.get(
        f"{CONNECTIONS_URL}"
        "?sort_by=sanctioned_load"
        "&sort_order=desc"
    )

    assert response.status_code == 200

    data = response.json()

    loads = [
        item["sanctioned_load"]
        for item in data["items"]
    ]

    assert loads == sorted(
        loads,
        reverse=True,
    )


def test_connections_sort_by_connection_number():
    cleanup_data()

    customer = create_customer()

    create_connection(
        customer["id"]
    )

    create_connection(
        customer["id"]
    )

    response = client.get(
        f"{CONNECTIONS_URL}"
        "?sort_by=connection_number"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    connection_numbers = [
        item["connection_number"]
        for item in data["items"]
    ]

    assert connection_numbers == sorted(
        connection_numbers
    )


def test_connections_invalid_sort_field_uses_default_sort():
    cleanup_data()

    customer = create_customer()

    create_connection(
        customer["id"]
    )

    response = client.get(
        f"{CONNECTIONS_URL}"
        "?sort_by=invalid_field"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert isinstance(data["items"], list)


# ============================================================
# LEVEL 13 - FILTER + PAGINATION + SORTING TOGETHER
# ============================================================


def test_connections_filter_pagination_and_sorting_together():
    cleanup_data()

    customer = create_customer()

    create_connection(
        customer["id"],
        connection_type="Residential",
        tariff_type="Domestic",
        status="Active",
        sanctioned_load=20.0,
    )

    create_connection(
        customer["id"],
        connection_type="Residential",
        tariff_type="Domestic",
        status="Active",
        sanctioned_load=5.0,
    )

    create_connection(
        customer["id"],
        connection_type="Residential",
        tariff_type="Domestic",
        status="Active",
        sanctioned_load=10.0,
    )

    create_connection(
        customer["id"],
        connection_type="Commercial",
        tariff_type="Commercial Tariff",
        status="Active",
        sanctioned_load=50.0,
    )

    response = client.get(
        f"{CONNECTIONS_URL}"
        "?connection_type=Residential"
        "&tariff_type=Domestic"
        "&status=Active"
        "&page=1"
        "&limit=2"
        "&sort_by=sanctioned_load"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2

    assert len(data["items"]) == 2

    loads = [
        item["sanctioned_load"]
        for item in data["items"]
    ]

    assert loads == [5.0, 10.0]

    for item in data["items"]:
        assert item["connection_type"] == "Residential"
        assert item["tariff_type"] == "Domestic"
        assert item["status"] == "Active"