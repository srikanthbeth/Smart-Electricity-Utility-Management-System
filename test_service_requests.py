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


def create_customer():
    response = client.post(
        "/api/v1/customers",
        json={
            "customer_number": unique_customer_number(),
            "full_name": "Service Request Customer",
            "email": (
                f"customer-{uuid4().hex[:8]}"
                "@example.com"
            ),
            "phone": "9876543210",
            "address": "Service Request Street",
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
            "address": "Service Request Street",
            "connection_date": "2026-09-22",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_service_request(
    customer_id,
    connection_id=None,
    request_type="New Connection",
):
    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer_id,
            "connection_id": connection_id,
            "request_type": request_type,
            "description": (
                f"Request for {request_type}"
            ),
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


# ============================================================
# CREATE
# ============================================================


def test_create_new_connection_request():
    customer = create_customer()

    request = create_service_request(
        customer_id=customer["id"],
        request_type="New Connection",
    )

    assert request["id"] is not None
    assert request["customer_id"] == customer["id"]
    assert request["connection_id"] is None
    assert request["request_type"] == "New Connection"
    assert request["status"] == "Submitted"


def test_create_load_change_request():
    customer = create_customer()
    connection = create_connection(customer["id"])

    request = create_service_request(
        customer_id=customer["id"],
        connection_id=connection["id"],
        request_type="Load Change",
    )

    assert request["request_type"] == "Load Change"
    assert request["connection_id"] == connection["id"]


def test_create_meter_replacement_request():
    customer = create_customer()
    connection = create_connection(customer["id"])

    request = create_service_request(
        customer_id=customer["id"],
        connection_id=connection["id"],
        request_type="Meter Replacement",
    )

    assert request["request_type"] == "Meter Replacement"


def test_create_name_change_request():
    customer = create_customer()
    connection = create_connection(customer["id"])

    request = create_service_request(
        customer_id=customer["id"],
        connection_id=connection["id"],
        request_type="Name Change",
    )

    assert request["request_type"] == "Name Change"


def test_create_address_change_request():
    customer = create_customer()
    connection = create_connection(customer["id"])

    request = create_service_request(
        customer_id=customer["id"],
        connection_id=connection["id"],
        request_type="Address Change",
    )

    assert request["request_type"] == "Address Change"


def test_create_disconnection_request():
    customer = create_customer()
    connection = create_connection(customer["id"])

    request = create_service_request(
        customer_id=customer["id"],
        connection_id=connection["id"],
        request_type="Disconnection",
    )

    assert request["request_type"] == "Disconnection"


def test_create_reconnection_request():
    customer = create_customer()
    connection = create_connection(customer["id"])

    request = create_service_request(
        customer_id=customer["id"],
        connection_id=connection["id"],
        request_type="Reconnection",
    )

    assert request["request_type"] == "Reconnection"


# ============================================================
# VALIDATION
# ============================================================


def test_invalid_request_type():
    customer = create_customer()

    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer["id"],
            "request_type": "Invalid Request",
            "description": "Invalid request",
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 422


def test_customer_not_found():
    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": 999999,
            "request_type": "New Connection",
            "description": "New connection request",
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 404


def test_connection_not_found():
    customer = create_customer()

    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer["id"],
            "connection_id": 999999,
            "request_type": "Load Change",
            "description": "Load change request",
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 404


def test_connection_must_belong_to_customer():
    customer1 = create_customer()
    customer2 = create_customer()

    connection = create_connection(
        customer1["id"]
    )

    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer2["id"],
            "connection_id": connection["id"],
            "request_type": "Load Change",
            "description": "Load change request",
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 400


def test_connection_required_for_non_new_connection():
    customer = create_customer()

    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer["id"],
            "request_type": "Load Change",
            "description": "Load change request",
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 400


def test_description_cannot_be_empty():
    customer = create_customer()

    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer["id"],
            "request_type": "New Connection",
            "description": "   ",
            "requested_date": "2026-10-01",
        },
    )

    assert response.status_code == 422


def test_requested_date_is_required():
    customer = create_customer()

    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": customer["id"],
            "request_type": "New Connection",
            "description": "New connection request",
        },
    )

    assert response.status_code == 422


# ============================================================
# GET
# ============================================================


def test_get_service_requests():
    customer = create_customer()
    connection = create_connection(
        customer["id"]
    )

    create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    create_service_request(
        customer["id"],
        connection["id"],
        "Meter Replacement",
    )

    response = client.get(
        "/api/v1/service-requests"
    )

    assert response.status_code == 200

    requests = response.json()

    assert len(requests) == 2


def test_get_service_request_by_id():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    response = client.get(
        f"/api/v1/service-requests/{request['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request["id"]
    assert data["customer_id"] == customer["id"]
    assert data["request_type"] == "New Connection"


def test_get_service_request_not_found():
    response = client.get(
        "/api/v1/service-requests/999999"
    )

    assert response.status_code == 404


# ============================================================
# APPROVE
# ============================================================


def test_approve_service_request():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/approve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Approved"


def test_approve_request_only_from_submitted():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/approve"
    )

    response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/approve"
    )

    assert response.status_code == 400


# ============================================================
# REJECT
# ============================================================


def test_reject_service_request():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/reject"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Rejected"


def test_reject_request_only_from_submitted():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/reject"
    )

    response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/reject"
    )

    assert response.status_code == 400


# ============================================================
# COMPLETE
# ============================================================


def test_complete_approved_request():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    approve_response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/approve"
    )

    assert approve_response.status_code == 200

    complete_response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/complete"
    )

    assert complete_response.status_code == 200

    data = complete_response.json()

    assert data["status"] == "Completed"


def test_cannot_complete_submitted_request():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/complete"
    )

    assert response.status_code == 400


def test_cannot_complete_rejected_request():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    reject_response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/reject"
    )

    assert reject_response.status_code == 200

    response = client.put(
        f"/api/v1/service-requests/"
        f"{request['id']}/complete"
    )

    assert response.status_code == 400


# ============================================================
# RESPONSE FIELDS
# ============================================================


def test_service_request_response_contains_all_fields():
    customer = create_customer()

    request = create_service_request(
        customer["id"],
        request_type="New Connection",
    )

    expected_fields = {
        "id",
        "customer_id",
        "connection_id",
        "request_type",
        "description",
        "requested_date",
        "status",
    }

    assert expected_fields.issubset(
        request.keys()
    )