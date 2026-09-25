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
METERS_URL = "/api/v1/meters"


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def cleanup_data():
    db = SessionLocal()

    try:
        db.execute(text("DELETE FROM meters"))
        db.execute(text("DELETE FROM connections"))
        db.execute(text("DELETE FROM customers"))
        db.commit()
    finally:
        db.close()


def create_customer():
    unique_id = uuid4().hex[:8]

    payload = {
        "customer_number": f"CUST-{unique_id}",
        "full_name": "Meter Customer",
        "email": f"meter_{unique_id}@example.com",
        "phone": "9876543210",
        "address": "123 Main Street",
        "city": "Hyderabad",
        "status": "Active",
    }

    response = client.post(
        CUSTOMERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_connection(customer_id):
    unique_id = uuid4().hex[:8]

    payload = {
        "customer_id": customer_id,
        "connection_number": f"CONN-{unique_id}",
        "connection_type": "Residential",
        "sanctioned_load": 5.0,
        "tariff_type": "Domestic",
        "connection_date": str(date.today()),
        "status": "Active",
    }

    response = client.post(
        CONNECTIONS_URL,
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def meter_payload(connection_id):
    unique_id = uuid4().hex[:8]

    return {
        "connection_id": connection_id,
        "meter_number": f"MTR-{unique_id}",
        "meter_type": "Smart Meter",
        "installation_date": str(date.today()),
        "initial_reading": 100.0,
        "current_reading": 150.0,
        "meter_status": "Active",
    }


def create_meter(connection_id):
    response = client.post(
        METERS_URL,
        json=meter_payload(connection_id),
    )

    assert response.status_code == 201

    return response.json()


def test_create_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(connection["id"])

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_id"] == connection["id"]
    assert data["meter_number"] == payload["meter_number"]
    assert data["meter_type"] == "Smart Meter"
    assert data["initial_reading"] == 100.0
    assert data["current_reading"] == 150.0
    assert data["meter_status"] == "Active"


def test_get_meters():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.get(
        METERS_URL
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert any(
        item["id"] == meter["id"]
        for item in data
    )


def test_get_meter_by_id():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.get(
        f"{METERS_URL}/{meter['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == meter["id"]
    assert data["connection_id"] == connection["id"]
    assert data["meter_number"] == meter["meter_number"]


def test_get_meter_not_found():
    cleanup_data()

    response = client.get(
        f"{METERS_URL}/999999"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Meter not found"
    )


def test_create_meter_for_nonexistent_connection():
    cleanup_data()

    payload = meter_payload(
        connection_id=999999
    )

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Connection not found"
    )


def test_duplicate_meter_number():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    first_payload = meter_payload(
        connection["id"]
    )

    first_response = client.post(
        METERS_URL,
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_customer = create_customer()
    second_connection = create_connection(
        second_customer["id"]
    )

    second_payload = meter_payload(
        second_connection["id"]
    )

    second_payload["meter_number"] = (
        first_payload["meter_number"]
    )

    response = client.post(
        METERS_URL,
        json=second_payload,
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Meter number already exists"
    )


def test_connection_cannot_have_multiple_active_meters():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    first_response = client.post(
        METERS_URL,
        json=meter_payload(connection["id"]),
    )

    assert first_response.status_code == 201

    second_payload = meter_payload(
        connection["id"]
    )

    response = client.post(
        METERS_URL,
        json=second_payload,
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Connection already has an active meter"
    )


def test_create_faulty_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(
        connection["id"]
    )

    payload["meter_status"] = "Faulty"

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    assert response.json()["meter_status"] == "Faulty"


def test_create_removed_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(
        connection["id"]
    )

    payload["meter_status"] = "Removed"

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    assert response.json()["meter_status"] == "Removed"


def test_current_reading_cannot_be_less_than_initial_reading():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(
        connection["id"]
    )

    payload["initial_reading"] = 200
    payload["current_reading"] = 100

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Current reading cannot be less than initial reading"
    )


def test_update_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.put(
        f"{METERS_URL}/{meter['id']}",
        json={
            "meter_type": "Advanced Smart Meter",
            "current_reading": 200,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meter_type"] == "Advanced Smart Meter"
    assert data["current_reading"] == 200.0


def test_update_meter_status_to_faulty():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.put(
        f"{METERS_URL}/{meter['id']}",
        json={
            "meter_status": "Faulty",
        },
    )

    assert response.status_code == 200

    assert response.json()["meter_status"] == "Faulty"


def test_update_meter_status_to_removed():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.put(
        f"{METERS_URL}/{meter['id']}",
        json={
            "meter_status": "Removed",
        },
    )

    assert response.status_code == 200

    assert response.json()["meter_status"] == "Removed"


def test_update_meter_not_found():
    cleanup_data()

    response = client.put(
        f"{METERS_URL}/999999",
        json={
            "meter_type": "Smart Meter",
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Meter not found"
    )


def test_update_meter_reading_validation():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.put(
        f"{METERS_URL}/{meter['id']}",
        json={
            "current_reading": 50,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Current reading cannot be less than initial reading"
    )


def test_replace_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    response = client.post(
        f"{METERS_URL}/{meter['id']}/replace"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == meter["id"]
    assert data["meter_status"] == "Removed"


def test_replacement_allows_new_active_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    old_meter = create_meter(connection["id"])

    replace_response = client.post(
        f"{METERS_URL}/{old_meter['id']}/replace"
    )

    assert replace_response.status_code == 200

    new_payload = meter_payload(
        connection["id"]
    )

    new_response = client.post(
        METERS_URL,
        json=new_payload,
    )

    assert new_response.status_code == 201

    data = new_response.json()

    assert data["meter_status"] == "Active"
    assert data["connection_id"] == connection["id"]


def test_replace_already_removed_meter():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])
    meter = create_meter(connection["id"])

    first_response = client.post(
        f"{METERS_URL}/{meter['id']}/replace"
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"{METERS_URL}/{meter['id']}/replace"
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Meter is already removed"
    )


def test_replace_nonexistent_meter():
    cleanup_data()

    response = client.post(
        f"{METERS_URL}/999999/replace"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Meter not found"
    )


def test_invalid_meter_status():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(
        connection["id"]
    )

    payload["meter_status"] = "InvalidStatus"

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_negative_initial_reading():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(
        connection["id"]
    )

    payload["initial_reading"] = -1

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_negative_current_reading():
    cleanup_data()

    customer = create_customer()
    connection = create_connection(customer["id"])

    payload = meter_payload(
        connection["id"]
    )

    payload["current_reading"] = -1

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 422