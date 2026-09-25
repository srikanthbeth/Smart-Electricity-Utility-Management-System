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
READINGS_URL = "/api/v1/meter-readings"


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def cleanup_data():
    db = SessionLocal()

    try:
        db.execute(text("DELETE FROM meter_readings"))
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
        "full_name": "Reading Customer",
        "email": f"reading_{unique_id}@example.com",
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


def create_meter(connection_id):
    unique_id = uuid4().hex[:8]

    payload = {
        "connection_id": connection_id,
        "meter_number": f"MTR-{unique_id}",
        "meter_type": "Smart Meter",
        "installation_date": str(date.today()),
        "initial_reading": 100.0,
        "current_reading": 100.0,
        "meter_status": "Active",
    }

    response = client.post(
        METERS_URL,
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_reading_payload(
    meter_id,
    reading_date=None,
):
    if reading_date is None:
        reading_date = date.today()

    return {
        "meter_id": meter_id,
        "reading_date": str(reading_date),
        "previous_reading": 100.0,
        "current_reading": 150.0,
        "reading_source": "Manual",
        "remarks": "Monthly meter reading",
    }


def create_reading(
    meter_id,
    reading_date=None,
):
    payload = create_reading_payload(
        meter_id,
        reading_date,
    )

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_meter_setup():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    return customer, connection, meter


def test_create_meter_reading():
    cleanup_data()

    _, connection, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["meter_id"] == meter["id"]
    assert data["previous_reading"] == 100.0
    assert data["current_reading"] == 150.0

    # 150 - 100 = 50
    assert data["units_consumed"] == 50.0

    assert data["reading_source"] == "Manual"
    assert data["remarks"] == "Monthly meter reading"


def test_units_consumed_is_calculated_automatically():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["previous_reading"] = 250.0
    payload["current_reading"] = 325.0

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["units_consumed"] == 75.0


def test_get_all_meter_readings():
    cleanup_data()

    _, _, meter = create_meter_setup()

    create_reading(meter["id"])

    response = client.get(
        READINGS_URL
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["meter_id"] == meter["id"]


def test_get_readings_by_meter():
    cleanup_data()

    _, _, meter = create_meter_setup()

    create_reading(meter["id"])

    response = client.get(
        f"{METERS_URL}/{meter['id']}/readings"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["meter_id"] == meter["id"]


def test_get_readings_by_nonexistent_meter():
    cleanup_data()

    response = client.get(
        f"{METERS_URL}/999999/readings"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Meter not found"
    )


def test_get_readings_by_connection():
    cleanup_data()

    _, connection, meter = create_meter_setup()

    create_reading(meter["id"])

    response = client.get(
        f"{CONNECTIONS_URL}/{connection['id']}/readings"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["meter_id"] == meter["id"]


def test_get_readings_by_nonexistent_connection():
    cleanup_data()

    response = client.get(
        f"{CONNECTIONS_URL}/999999/readings"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Connection not found"
    )


def test_current_reading_cannot_be_lower_than_previous():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["previous_reading"] = 200.0
    payload["current_reading"] = 150.0

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Current reading cannot be lower than previous reading"
    )


def test_negative_consumption_is_not_allowed():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["previous_reading"] = 500.0
    payload["current_reading"] = 400.0

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Current reading cannot be lower than previous reading"
    )


def test_duplicate_reading_same_billing_period():
    cleanup_data()

    _, _, meter = create_meter_setup()

    reading_date = date(2026, 9, 10)

    first_payload = create_reading_payload(
        meter["id"],
        reading_date,
    )

    first_response = client.post(
        READINGS_URL,
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_payload = create_reading_payload(
        meter["id"],
        date(2026, 9, 25),
    )

    second_response = client.post(
        READINGS_URL,
        json=second_payload,
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Reading already exists for this meter and billing period"
    )


def test_readings_allowed_for_different_months():
    cleanup_data()

    _, _, meter = create_meter_setup()

    september = create_reading(
        meter["id"],
        date(2026, 9, 10),
    )

    october = create_reading(
        meter["id"],
        date(2026, 10, 10),
    )

    assert september["units_consumed"] == 50.0
    assert october["units_consumed"] == 50.0


def test_readings_allowed_for_different_meters():
    cleanup_data()

    customer_one = create_customer()
    connection_one = create_connection(
        customer_one["id"]
    )
    meter_one = create_meter(
        connection_one["id"]
    )

    customer_two = create_customer()
    connection_two = create_connection(
        customer_two["id"]
    )
    meter_two = create_meter(
        connection_two["id"]
    )

    reading_one = create_reading(
        meter_one["id"],
        date(2026, 9, 10),
    )

    reading_two = create_reading(
        meter_two["id"],
        date(2026, 9, 10),
    )

    assert reading_one["meter_id"] != reading_two["meter_id"]


def test_manual_reading_source():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["reading_source"] = "Manual"

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["reading_source"] == "Manual"


def test_smart_meter_reading_source():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["reading_source"] = "Smart Meter"

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["reading_source"] == "Smart Meter"


def test_field_technician_reading_source():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["reading_source"] = "Field Technician"

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201
    assert (
        response.json()["reading_source"]
        == "Field Technician"
    )


def test_invalid_reading_source():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["reading_source"] = "Invalid Source"

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_nonexistent_meter():
    cleanup_data()

    payload = create_reading_payload(
        999999
    )

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Meter not found"
    )


def test_faulty_meter_cannot_receive_reading():
    cleanup_data()

    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    unique_id = uuid4().hex[:8]

    meter_payload = {
        "connection_id": connection["id"],
        "meter_number": f"MTR-{unique_id}",
        "meter_type": "Smart Meter",
        "installation_date": str(date.today()),
        "initial_reading": 100.0,
        "current_reading": 100.0,
        "meter_status": "Faulty",
    }

    meter_response = client.post(
        METERS_URL,
        json=meter_payload,
    )

    assert meter_response.status_code == 201

    meter = meter_response.json()

    payload = create_reading_payload(
        meter["id"]
    )

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Only active meters can receive readings"
    )


def test_removed_meter_cannot_receive_reading():
    cleanup_data()

    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    unique_id = uuid4().hex[:8]

    meter_payload = {
        "connection_id": connection["id"],
        "meter_number": f"MTR-{unique_id}",
        "meter_type": "Smart Meter",
        "installation_date": str(date.today()),
        "initial_reading": 100.0,
        "current_reading": 100.0,
        "meter_status": "Removed",
    }

    meter_response = client.post(
        METERS_URL,
        json=meter_payload,
    )

    assert meter_response.status_code == 201

    meter = meter_response.json()

    payload = create_reading_payload(
        meter["id"]
    )

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Only active meters can receive readings"
    )


def test_zero_consumption_is_allowed():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["previous_reading"] = 200.0
    payload["current_reading"] = 200.0

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201

    assert response.json()["units_consumed"] == 0.0


def test_negative_previous_reading_validation():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["previous_reading"] = -10.0

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_negative_current_reading_validation():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["current_reading"] = -10.0

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 422


def test_reading_with_remarks():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload["remarks"] = (
        "Reading taken by field technician"
    )

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["remarks"]
        == "Reading taken by field technician"
    )


def test_reading_without_remarks():
    cleanup_data()

    _, _, meter = create_meter_setup()

    payload = create_reading_payload(
        meter["id"]
    )

    payload.pop("remarks")

    response = client.post(
        READINGS_URL,
        json=payload,
    )

    assert response.status_code == 201

    assert response.json()["remarks"] is None