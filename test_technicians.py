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


def unique_employee_id():
    return f"EMP-{uuid4().hex[:8].upper()}"


def create_technician(
    name="John Technician",
    specialization="Meter Installation",
    availability_status="Available",
):
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": name,
            "employee_id": unique_employee_id(),
            "phone": "9876543210",
            "specialization": specialization,
            "availability_status": availability_status,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


# ============================================================
# CREATE
# ============================================================


def test_create_technician():
    technician = create_technician()

    assert technician["id"] is not None
    assert technician["name"] == "John Technician"
    assert technician["employee_id"]
    assert technician["phone"] == "9876543210"
    assert technician["specialization"] == "Meter Installation"
    assert technician["availability_status"] == "Available"


def test_duplicate_employee_id():
    employee_id = unique_employee_id()

    response1 = client.post(
        "/api/v1/technicians",
        json={
            "name": "First Technician",
            "employee_id": employee_id,
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )

    assert response1.status_code == 201, response1.text

    response2 = client.post(
        "/api/v1/technicians",
        json={
            "name": "Second Technician",
            "employee_id": employee_id,
            "phone": "9876543211",
            "specialization": "Meter Replacement",
            "availability_status": "Available",
        },
    )

    assert response2.status_code == 409


# ============================================================
# SPECIALIZATIONS
# ============================================================


def test_meter_installation_specialization():
    technician = create_technician(
        specialization="Meter Installation"
    )

    assert (
        technician["specialization"]
        == "Meter Installation"
    )


def test_meter_replacement_specialization():
    technician = create_technician(
        specialization="Meter Replacement"
    )

    assert (
        technician["specialization"]
        == "Meter Replacement"
    )


def test_connection_inspection_specialization():
    technician = create_technician(
        specialization="Connection Inspection"
    )

    assert (
        technician["specialization"]
        == "Connection Inspection"
    )


def test_complaint_resolution_specialization():
    technician = create_technician(
        specialization="Complaint Resolution"
    )

    assert (
        technician["specialization"]
        == "Complaint Resolution"
    )


def test_invalid_specialization():
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": "Invalid Technician",
            "employee_id": unique_employee_id(),
            "phone": "9876543210",
            "specialization": "Invalid Specialization",
            "availability_status": "Available",
        },
    )

    assert response.status_code == 422


# ============================================================
# AVAILABILITY
# ============================================================


def test_available_technician():
    technician = create_technician(
        availability_status="Available"
    )

    assert technician["availability_status"] == "Available"


def test_busy_technician():
    technician = create_technician(
        availability_status="Busy"
    )

    assert technician["availability_status"] == "Busy"


def test_on_leave_technician():
    technician = create_technician(
        availability_status="On Leave"
    )

    assert technician["availability_status"] == "On Leave"


def test_unavailable_technician():
    technician = create_technician(
        availability_status="Unavailable"
    )

    assert technician["availability_status"] == "Unavailable"


def test_invalid_availability_status():
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": "Invalid Status Technician",
            "employee_id": unique_employee_id(),
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Unknown",
        },
    )

    assert response.status_code == 422


def test_update_availability_to_busy():
    technician = create_technician()

    response = client.put(
        f"/api/v1/technicians/{technician['id']}/availability",
        json={
            "availability_status": "Busy",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["availability_status"] == "Busy"


def test_update_availability_to_available():
    technician = create_technician(
        availability_status="Busy"
    )

    response = client.put(
        f"/api/v1/technicians/{technician['id']}/availability",
        json={
            "availability_status": "Available",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["availability_status"]
        == "Available"
    )


def test_update_availability_to_on_leave():
    technician = create_technician()

    response = client.put(
        f"/api/v1/technicians/{technician['id']}/availability",
        json={
            "availability_status": "On Leave",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["availability_status"]
        == "On Leave"
    )


def test_update_availability_to_unavailable():
    technician = create_technician()

    response = client.put(
        f"/api/v1/technicians/{technician['id']}/availability",
        json={
            "availability_status": "Unavailable",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["availability_status"]
        == "Unavailable"
    )


def test_invalid_availability_update():
    technician = create_technician()

    response = client.put(
        f"/api/v1/technicians/{technician['id']}/availability",
        json={
            "availability_status": "Invalid",
        },
    )

    assert response.status_code == 422


# ============================================================
# GET
# ============================================================


def test_get_technicians():
    create_technician(
        name="Technician One"
    )

    create_technician(
        name="Technician Two",
        specialization="Meter Replacement",
    )

    response = client.get(
        "/api/v1/technicians"
    )

    assert response.status_code == 200

    technicians = response.json()

    assert len(technicians) == 2


def test_get_technician_by_id():
    technician = create_technician()

    response = client.get(
        f"/api/v1/technicians/{technician['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == technician["id"]
    assert data["name"] == technician["name"]
    assert data["employee_id"] == technician["employee_id"]


def test_get_technician_not_found():
    response = client.get(
        "/api/v1/technicians/999999"
    )

    assert response.status_code == 404


def test_update_technician_not_found():
    response = client.put(
        "/api/v1/technicians/999999/availability",
        json={
            "availability_status": "Busy",
        },
    )

    assert response.status_code == 404


# ============================================================
# VALIDATION
# ============================================================


def test_missing_name():
    response = client.post(
        "/api/v1/technicians",
        json={
            "employee_id": unique_employee_id(),
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )

    assert response.status_code == 422


def test_missing_employee_id():
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": "Technician",
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )

    assert response.status_code == 422


def test_missing_phone():
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": "Technician",
            "employee_id": unique_employee_id(),
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )

    assert response.status_code == 422


def test_missing_specialization():
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": "Technician",
            "employee_id": unique_employee_id(),
            "phone": "9876543210",
            "availability_status": "Available",
        },
    )

    assert response.status_code == 422


def test_default_availability_is_available():
    response = client.post(
        "/api/v1/technicians",
        json={
            "name": "Default Technician",
            "employee_id": unique_employee_id(),
            "phone": "9876543210",
            "specialization": "Meter Installation",
        },
    )

    assert response.status_code == 201, response.text

    assert (
        response.json()["availability_status"]
        == "Available"
    )


def test_technician_response_contains_all_fields():
    technician = create_technician()

    expected_fields = {
        "id",
        "name",
        "employee_id",
        "phone",
        "specialization",
        "availability_status",
    }

    assert expected_fields.issubset(
        technician.keys()
    )