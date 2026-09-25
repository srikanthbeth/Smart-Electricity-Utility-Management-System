import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "smart_electricity_utility_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app
from models.meter_reading import MeterReading


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def setup_function():
    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    service_requests,
                    complaint_history,
                    complaints,
                    payments,
                    bills,
                    meter_readings,
                    meters,
                    tariffs,
                    connections,
                    customers,
                    technicians,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )

        db.commit()

    finally:
        db.close()


def unique_customer_number():
    return f"CUST-{uuid4().hex[:8].upper()}"


def unique_connection_number():
    return f"CONN-{uuid4().hex[:8].upper()}"


def unique_meter_number():
    return f"METER-{uuid4().hex[:8].upper()}"


def create_customer():
    response = client.post(
        "/api/v1/customers",
        json={
            "customer_number": unique_customer_number(),
            "full_name": "Analytics Customer",
            "email": (
                f"analytics-{uuid4().hex[:8]}"
                "@example.com"
            ),
            "phone": "9876543210",
            "address": "Analytics Street",
            "city": "Nandyal",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_connection(customer_id):
    response = client.post(
        "/api/v1/connections",
        json={
            "customer_id": customer_id,
            "connection_number": unique_connection_number(),
            "connection_type": "Residential",
            "tariff_type": "Residential",
            "sanctioned_load": 5,
            "address": "Analytics Street",
            "connection_date": "2026-01-01",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_meter(connection_id):
    response = client.post(
        "/api/v1/meters",
        json={
            "connection_id": connection_id,
            "meter_number": unique_meter_number(),
            "meter_type": "Smart",
            "installation_date": "2026-01-01",
            "initial_reading": 0,
            "current_reading": 0,
            "meter_status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_reading(
    meter_id,
    reading_date,
    previous_reading,
    current_reading,
):
    response = client.post(
        "/api/v1/meter-readings",
        json={
            "meter_id": meter_id,
            "reading_date": reading_date,
            "previous_reading": previous_reading,
            "current_reading": current_reading,
            "reading_source": "Manual",
            "remarks": "Analytics test reading",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_bill(
    connection_id,
    billing_month,
    units_consumed,
    total_amount,
):
    db = SessionLocal()

    try:
        from models.bill import Bill

        bill = Bill(
            connection_id=connection_id,
            billing_month=billing_month,
            units_consumed=units_consumed,
            energy_charge=total_amount,
            fixed_charge=0,
            tax=0,
            late_fee=0,
            discount=0,
            total_amount=total_amount,
            due_date="2026-02-15",
            bill_status="Generated",
        )

        db.add(bill)
        db.commit()
        db.refresh(bill)

        return bill

    finally:
        db.close()


# ============================================================
# MONTHLY
# ============================================================


def test_connection_monthly_consumption():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_reading(
        meter["id"],
        "2026-01-31",
        0,
        100,
    )

    response = client.get(
        f"/api/v1/analytics/"
        f"connections/{connection['id']}/monthly"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["month"] == "2026-01"
    assert data[0]["units_consumed"] == 100


def test_monthly_response_contains_required_fields():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_reading(
        meter["id"],
        "2026-01-31",
        0,
        150,
    )

    response = client.get(
        f"/api/v1/analytics/"
        f"connections/{connection['id']}/monthly"
    )

    assert response.status_code == 200

    item = response.json()[0]

    assert {
        "month",
        "units_consumed",
        "bill_amount",
    }.issubset(item.keys())


def test_monthly_consumption_multiple_months():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_reading(
        meter["id"],
        "2026-01-31",
        0,
        100,
    )

    create_reading(
        meter["id"],
        "2026-02-28",
        100,
        250,
    )

    response = client.get(
        f"/api/v1/analytics/"
        f"connections/{connection['id']}/monthly"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["month"] == "2026-01"
    assert data[0]["units_consumed"] == 100

    assert data[1]["month"] == "2026-02"
    assert data[1]["units_consumed"] == 150


# ============================================================
# YEARLY
# ============================================================


def test_connection_yearly_consumption():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_reading(
        meter["id"],
        "2026-01-31",
        0,
        100,
    )

    create_reading(
        meter["id"],
        "2026-02-28",
        100,
        250,
    )

    response = client.get(
        f"/api/v1/analytics/"
        f"connections/{connection['id']}/yearly"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["year"] == 2026
    assert data[0]["units_consumed"] == 250


# ============================================================
# CONNECTION USAGE
# ============================================================


def test_connection_usage():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_reading(
        meter["id"],
        "2026-01-31",
        0,
        100,
    )

    create_reading(
        meter["id"],
        "2026-02-28",
        100,
        250,
    )

    response = client.get(
        f"/api/v1/analytics/"
        f"connections/{connection['id']}/usage"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["connection_id"] == connection["id"]
    assert data["connection_number"] == (
        connection["connection_number"]
    )
    assert data["units_consumed"] == 250


def test_connection_not_found():
    response = client.get(
        "/api/v1/analytics/"
        "connections/999999/monthly"
    )

    assert response.status_code == 404


# ============================================================
# CUSTOMER USAGE
# ============================================================


def test_customer_usage():
    customer = create_customer()

    connection1 = create_connection(
        customer["id"]
    )

    connection2 = create_connection(
        customer["id"]
    )

    meter1 = create_meter(
        connection1["id"]
    )

    meter2 = create_meter(
        connection2["id"]
    )

    create_reading(
        meter1["id"],
        "2026-01-31",
        0,
        100,
    )

    create_reading(
        meter2["id"],
        "2026-01-31",
        0,
        200,
    )

    response = client.get(
        f"/api/v1/analytics/"
        f"customers/{customer['id']}/usage"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == customer["id"]
    assert data["units_consumed"] == 300


def test_customer_not_found():
    response = client.get(
        "/api/v1/analytics/"
        "customers/999999/usage"
    )

    assert response.status_code == 404


# ============================================================
# HIGHEST CONSUMING CONNECTIONS
# ============================================================


def test_highest_consuming_connections():
    customer = create_customer()

    connection1 = create_connection(
        customer["id"]
    )

    connection2 = create_connection(
        customer["id"]
    )

    meter1 = create_meter(
        connection1["id"]
    )

    meter2 = create_meter(
        connection2["id"]
    )

    create_reading(
        meter1["id"],
        "2026-01-31",
        0,
        100,
    )

    create_reading(
        meter2["id"],
        "2026-01-31",
        0,
        500,
    )

    response = client.get(
        "/api/v1/analytics/"
        "highest-consuming-connections"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["connection_id"] == (
        connection2["id"]
    )

    assert data[0]["units_consumed"] == 500

    assert data[1]["connection_id"] == (
        connection1["id"]
    )

    assert data[1]["units_consumed"] == 100


# ============================================================
# AVERAGE MONTHLY
# ============================================================


def test_average_monthly_consumption():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_reading(
        meter["id"],
        "2026-01-31",
        0,
        100,
    )

    create_reading(
        meter["id"],
        "2026-02-28",
        100,
        300,
    )

    response = client.get(
        "/api/v1/analytics/"
        "average-monthly-consumption"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["average_monthly_consumption"] == 150


def test_average_monthly_consumption_without_data():
    response = client.get(
        "/api/v1/analytics/"
        "average-monthly-consumption"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["average_monthly_consumption"] == 0.0