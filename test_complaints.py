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

COMPLAINTS_URL = "/api/v1/complaints"
CUSTOMERS_URL = "/api/v1/customers"


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
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )

        db.commit()

    finally:
        db.close()


def unique_email(prefix="user"):
    return (
        f"{prefix}_{uuid4().hex[:8]}"
        "@example.com"
    )


def create_customer(
    city="Nandyal",
    status="Active",
):
    response = client.post(
        CUSTOMERS_URL,
        json={
            "customer_number": (
                f"CUST-{uuid4().hex[:8]}"
            ),
            "full_name": "Complaint Customer",
            "email": unique_email("customer"),
            "phone": "9876543210",
            "address": "Complaint Street",
            "city": city,
            "status": status,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_connection(customer_id):
    response = client.post(
        "/api/v1/connections",
        json={
            "customer_id": customer_id,
            "connection_number": (
                f"CONN-{uuid4().hex[:8]}"
            ),
            "connection_type": "Residential",
            "tariff_type": "Residential",
            "sanctioned_load": 5,
            "address": "Complaint Street",
            "connection_date": "2026-09-22",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_technician(
    full_name="Available Technician",
    is_active=True,
):
    db = SessionLocal()

    try:
        from models.user import User

        technician = User(
            full_name=full_name,
            email=unique_email("technician"),
            hashed_password="test_hashed_password",
            role="Technician",
            is_active=is_active,
        )

        db.add(technician)
        db.commit()
        db.refresh(technician)

        return technician.id

    finally:
        db.close()


def create_complaint(
    customer_id=None,
    connection_id=None,
    complaint_type="Power Failure",
    description="Power supply is not available.",
    priority="Medium",
):
    if customer_id is None:
        customer = create_customer()
        customer_id = customer["id"]

    if connection_id is None:
        connection = create_connection(
            customer_id
        )
        connection_id = connection["id"]

    response = client.post(
        COMPLAINTS_URL,
        json={
            "customer_id": customer_id,
            "connection_id": connection_id,
            "complaint_type": complaint_type,
            "description": description,
            "priority": priority,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def update_complaint_status(
    complaint_id,
    complaint_status,
):
    response = client.put(
        f"{COMPLAINTS_URL}/{complaint_id}/status",
        json={
            "status": complaint_status,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


# ============================================================
# CREATE COMPLAINT
# ============================================================


def test_create_complaint():
    complaint = create_complaint()

    assert complaint["id"] is not None
    assert (
        complaint["complaint_type"]
        == "Power Failure"
    )
    assert (
        complaint["description"]
        == "Power supply is not available."
    )
    assert complaint["priority"] == "Medium"
    assert complaint["assigned_to"] is None
    assert complaint["status"] == "Open"


def test_create_power_failure_complaint():
    complaint = create_complaint(
        complaint_type="Power Failure",
    )

    assert (
        complaint["complaint_type"]
        == "Power Failure"
    )


def test_create_voltage_issue_complaint():
    complaint = create_complaint(
        complaint_type="Voltage Issue",
    )

    assert (
        complaint["complaint_type"]
        == "Voltage Issue"
    )


def test_create_meter_issue_complaint():
    complaint = create_complaint(
        complaint_type="Meter Issue",
    )

    assert (
        complaint["complaint_type"]
        == "Meter Issue"
    )


def test_create_billing_issue_complaint():
    complaint = create_complaint(
        complaint_type="Billing Issue",
    )

    assert (
        complaint["complaint_type"]
        == "Billing Issue"
    )


def test_create_connection_issue_complaint():
    complaint = create_complaint(
        complaint_type="Connection Issue",
    )

    assert (
        complaint["complaint_type"]
        == "Connection Issue"
    )


def test_create_other_complaint():
    complaint = create_complaint(
        complaint_type="Other",
    )

    assert (
        complaint["complaint_type"]
        == "Other"
    )


# ============================================================
# PRIORITY
# ============================================================


def test_low_priority_complaint():
    complaint = create_complaint(
        priority="Low",
    )

    assert complaint["priority"] == "Low"


def test_medium_priority_complaint():
    complaint = create_complaint(
        priority="Medium",
    )

    assert complaint["priority"] == "Medium"


def test_high_priority_complaint():
    complaint = create_complaint(
        priority="High",
    )

    assert complaint["priority"] == "High"


def test_emergency_complaint_has_highest_priority():
    complaint = create_complaint(
        priority="Emergency",
    )

    assert complaint["priority"] == "Emergency"


# ============================================================
# VALIDATION
# ============================================================


def test_invalid_complaint_type():
    customer = create_customer()
    connection = create_connection(
        customer["id"]
    )

    response = client.post(
        COMPLAINTS_URL,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Invalid Type",
            "description": "Test complaint",
            "priority": "Medium",
        },
    )

    assert response.status_code == 422


def test_invalid_priority():
    customer = create_customer()
    connection = create_connection(
        customer["id"]
    )

    response = client.post(
        COMPLAINTS_URL,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Power Failure",
            "description": "Test complaint",
            "priority": "Critical",
        },
    )

    assert response.status_code == 422


def test_empty_description():
    customer = create_customer()
    connection = create_connection(
        customer["id"]
    )

    response = client.post(
        COMPLAINTS_URL,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Power Failure",
            "description": "",
            "priority": "Medium",
        },
    )

    assert response.status_code == 422


def test_nonexistent_customer():
    response = client.post(
        COMPLAINTS_URL,
        json={
            "customer_id": 999999,
            "connection_id": 999999,
            "complaint_type": "Power Failure",
            "description": "Test complaint",
            "priority": "Medium",
        },
    )

    assert response.status_code == 404


def test_nonexistent_connection():
    customer = create_customer()

    response = client.post(
        COMPLAINTS_URL,
        json={
            "customer_id": customer["id"],
            "connection_id": 999999,
            "complaint_type": "Power Failure",
            "description": "Test complaint",
            "priority": "Medium",
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
        COMPLAINTS_URL,
        json={
            "customer_id": customer2["id"],
            "connection_id": connection["id"],
            "complaint_type": "Power Failure",
            "description": "Test complaint",
            "priority": "Medium",
        },
    )

    assert response.status_code == 400


# ============================================================
# GET COMPLAINTS
# ============================================================


def test_get_complaints():
    first_complaint = create_complaint()

    second_complaint = create_complaint(
        complaint_type="Voltage Issue",
    )

    response = client.get(
        COMPLAINTS_URL
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert "items" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] == 2
    assert data["total_pages"] == 1

    complaints = data["items"]

    assert isinstance(complaints, list)
    assert len(complaints) == 2

    complaint_ids = [
        complaint["id"]
        for complaint in complaints
    ]

    assert first_complaint["id"] in complaint_ids
    assert second_complaint["id"] in complaint_ids


def test_get_complaint_by_id():
    complaint = create_complaint()

    response = client.get(
        f"{COMPLAINTS_URL}/{complaint['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == complaint["id"]
    assert (
        data["customer_id"]
        == complaint["customer_id"]
    )
    assert (
        data["connection_id"]
        == complaint["connection_id"]
    )


def test_get_complaint_not_found():
    response = client.get(
        f"{COMPLAINTS_URL}/999999"
    )

    assert response.status_code == 404


# ============================================================
# TECHNICIAN ASSIGNMENT
# ============================================================


def test_assign_available_technician():
    complaint = create_complaint()

    technician_id = create_technician()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/assign",
        json={
            "technician_id": technician_id,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["assigned_to"] == technician_id
    assert data["status"] == "Assigned"


def test_assign_nonexistent_technician():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/assign",
        json={
            "technician_id": 999999,
        },
    )

    assert response.status_code == 404


def test_assign_non_technician_user():
    complaint = create_complaint()

    db = SessionLocal()

    try:
        from models.user import User

        user = User(
            full_name="Normal Customer User",
            email=unique_email("normal"),
            hashed_password="test_hashed_password",
            role="Customer",
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

    finally:
        db.close()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/assign",
        json={
            "technician_id": user_id,
        },
    )

    assert response.status_code == 400


def test_unavailable_technician_cannot_be_assigned():
    complaint = create_complaint()

    technician_id = create_technician(
        full_name="Unavailable Technician",
        is_active=False,
    )

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/assign",
        json={
            "technician_id": technician_id,
        },
    )

    assert response.status_code == 400


def test_assign_nonexistent_complaint():
    technician_id = create_technician()

    response = client.put(
        f"{COMPLAINTS_URL}/999999/assign",
        json={
            "technician_id": technician_id,
        },
    )

    assert response.status_code == 404


# ============================================================
# STATUS
# ============================================================


def test_update_status_to_in_progress():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "In Progress",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "In Progress"


def test_update_status_to_resolved():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Resolved",
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "Resolved"


def test_update_status_to_closed():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Closed",
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "Closed"


def test_invalid_complaint_status():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Invalid Status",
        },
    )

    assert response.status_code == 422


def test_update_status_for_nonexistent_complaint():
    response = client.put(
        f"{COMPLAINTS_URL}/999999/status",
        json={
            "status": "Resolved",
        },
    )

    assert response.status_code == 404


def test_same_status_cannot_be_set_again():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Open",
        },
    )

    assert response.status_code == 400


# ============================================================
# COMPLAINT HISTORY
# ============================================================


def test_complaint_history_created():
    complaint = create_complaint()

    response = client.get(
        f"{COMPLAINTS_URL}/{complaint['id']}/history"
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) >= 1

    assert (
        history[0]["complaint_id"]
        == complaint["id"]
    )
    assert history[0]["action"] == "Created"
    assert history[0]["new_value"] == "Open"


def test_assignment_is_recorded_in_history():
    complaint = create_complaint()

    technician_id = create_technician()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/assign",
        json={
            "technician_id": technician_id,
        },
    )

    assert response.status_code == 200

    history_response = client.get(
        f"{COMPLAINTS_URL}/{complaint['id']}/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    actions = [
        item["action"]
        for item in history
    ]

    assert "Created" in actions
    assert "Assigned" in actions
    assert "Status Changed" in actions


def test_status_change_is_recorded_in_history():
    complaint = create_complaint()

    response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Resolved",
        },
    )

    assert response.status_code == 200

    history_response = client.get(
        f"{COMPLAINTS_URL}/{complaint['id']}/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    status_history = [
        item
        for item in history
        if item["action"] == "Status Changed"
    ]

    assert len(status_history) == 1

    assert (
        status_history[0]["old_value"]
        == "Open"
    )
    assert (
        status_history[0]["new_value"]
        == "Resolved"
    )


def test_complete_complaint_history():
    complaint = create_complaint()

    technician_id = create_technician()

    assign_response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/assign",
        json={
            "technician_id": technician_id,
        },
    )

    assert assign_response.status_code == 200

    status_response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "In Progress",
        },
    )

    assert status_response.status_code == 200

    status_response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Resolved",
        },
    )

    assert status_response.status_code == 200

    status_response = client.put(
        f"{COMPLAINTS_URL}/{complaint['id']}/status",
        json={
            "status": "Closed",
        },
    )

    assert status_response.status_code == 200

    history_response = client.get(
        f"{COMPLAINTS_URL}/{complaint['id']}/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) >= 5

    actions = [
        item["action"]
        for item in history
    ]

    assert actions[0] == "Created"
    assert "Assigned" in actions
    assert actions.count("Status Changed") >= 4


def test_history_for_nonexistent_complaint():
    response = client.get(
        f"{COMPLAINTS_URL}/999999/history"
    )

    assert response.status_code == 404


# ============================================================
# RESPONSE FIELDS
# ============================================================


def test_complaint_response_contains_all_fields():
    complaint = create_complaint()

    expected_fields = {
        "id",
        "customer_id",
        "connection_id",
        "complaint_type",
        "description",
        "priority",
        "assigned_to",
        "status",
    }

    assert expected_fields.issubset(
        complaint.keys()
    )


# ============================================================
# LEVEL 13
# FILTER BY PRIORITY
# ============================================================


def test_filter_complaints_by_priority():
    high_complaint = create_complaint(
        priority="High"
    )

    create_complaint(
        priority="Low"
    )

    create_complaint(
        priority="Medium"
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "priority": "High",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["total_pages"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == high_complaint["id"]
    )
    assert data["items"][0]["priority"] == "High"


# ============================================================
# LEVEL 13
# FILTER BY STATUS
# ============================================================


def test_filter_complaints_by_status():
    open_complaint = create_complaint()

    resolved_complaint = create_complaint(
        complaint_type="Voltage Issue"
    )

    update_complaint_status(
        resolved_complaint["id"],
        "Resolved",
    )

    closed_complaint = create_complaint(
        complaint_type="Billing Issue"
    )

    update_complaint_status(
        closed_complaint["id"],
        "Closed",
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "status": "Open",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == open_complaint["id"]
    )
    assert data["items"][0]["status"] == "Open"


# ============================================================
# LEVEL 13
# FILTER BY COMPLAINT TYPE
# ============================================================


def test_filter_complaints_by_type():
    power_complaint = create_complaint(
        complaint_type="Power Failure"
    )

    create_complaint(
        complaint_type="Voltage Issue"
    )

    create_complaint(
        complaint_type="Billing Issue"
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "complaint_type": "Power Failure",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == power_complaint["id"]
    )
    assert (
        data["items"][0]["complaint_type"]
        == "Power Failure"
    )


# ============================================================
# LEVEL 13
# FILTER BY ASSIGNED TECHNICIAN
# ============================================================


def test_filter_complaints_by_assigned_technician():
    first_complaint = create_complaint()

    technician_id = create_technician()

    response = client.put(
        f"{COMPLAINTS_URL}/{first_complaint['id']}/assign",
        json={
            "technician_id": technician_id,
        },
    )

    assert response.status_code == 200

    second_complaint = create_complaint(
        complaint_type="Voltage Issue"
    )

    second_technician_id = create_technician(
        full_name="Second Technician"
    )

    response = client.put(
        f"{COMPLAINTS_URL}/{second_complaint['id']}/assign",
        json={
            "technician_id": second_technician_id,
        },
    )

    assert response.status_code == 200

    response = client.get(
        COMPLAINTS_URL,
        params={
            "assigned_to": technician_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == first_complaint["id"]
    )
    assert (
        data["items"][0]["assigned_to"]
        == technician_id
    )


# ============================================================
# LEVEL 13
# MULTIPLE FILTERS
# ============================================================


def test_filter_complaints_by_multiple_filters():
    matching = create_complaint(
        complaint_type="Power Failure",
        priority="High",
    )

    create_complaint(
        complaint_type="Power Failure",
        priority="Low",
    )

    create_complaint(
        complaint_type="Voltage Issue",
        priority="High",
    )

    resolved = create_complaint(
        complaint_type="Power Failure",
        priority="High",
    )

    update_complaint_status(
        resolved["id"],
        "Resolved",
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "complaint_type": "Power Failure",
            "priority": "High",
            "status": "Open",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert (
        data["items"][0]["id"]
        == matching["id"]
    )

    assert (
        data["items"][0]["complaint_type"]
        == "Power Failure"
    )
    assert data["items"][0]["priority"] == "High"
    assert data["items"][0]["status"] == "Open"


# ============================================================
# LEVEL 13
# PAGINATION
# ============================================================


def test_complaint_pagination():
    for _ in range(5):
        create_complaint()

    response = client.get(
        COMPLAINTS_URL,
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


def test_complaint_second_page():
    for _ in range(5):
        create_complaint()

    response = client.get(
        COMPLAINTS_URL,
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


def test_complaint_last_page():
    for _ in range(5):
        create_complaint()

    response = client.get(
        COMPLAINTS_URL,
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
# LEVEL 13
# SORTING
# ============================================================


def test_sort_complaints_by_id_ascending():
    first = create_complaint(
        complaint_type="Power Failure"
    )

    second = create_complaint(
        complaint_type="Voltage Issue"
    )

    third = create_complaint(
        complaint_type="Billing Issue"
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "sort_by": "id",
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    data = response.json()

    ids = [
        item["id"]
        for item in data["items"]
    ]

    assert ids == [
        first["id"],
        second["id"],
        third["id"],
    ]


def test_sort_complaints_by_id_descending():
    first = create_complaint(
        complaint_type="Power Failure"
    )

    second = create_complaint(
        complaint_type="Voltage Issue"
    )

    third = create_complaint(
        complaint_type="Billing Issue"
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "sort_by": "id",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200

    data = response.json()

    ids = [
        item["id"]
        for item in data["items"]
    ]

    assert ids == [
        third["id"],
        second["id"],
        first["id"],
    ]


# ============================================================
# LEVEL 13
# FILTER + PAGINATION + SORTING
# ============================================================


def test_complaint_filter_pagination_and_sorting():
    first = create_complaint(
        complaint_type="Power Failure",
        priority="High",
    )

    second = create_complaint(
        complaint_type="Power Failure",
        priority="High",
    )

    third = create_complaint(
        complaint_type="Power Failure",
        priority="High",
    )

    # Non-matching complaints
    create_complaint(
        complaint_type="Power Failure",
        priority="Low",
    )

    create_complaint(
        complaint_type="Voltage Issue",
        priority="High",
    )

    response = client.get(
        COMPLAINTS_URL,
        params={
            "complaint_type": "Power Failure",
            "priority": "High",
            "status": "Open",
            "page": 1,
            "limit": 2,
            "sort_by": "id",
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

    ids = [
        item["id"]
        for item in data["items"]
    ]

    assert ids == [
        first["id"],
        second["id"],
    ]

    for complaint in data["items"]:
        assert (
            complaint["complaint_type"]
            == "Power Failure"
        )
        assert complaint["priority"] == "High"
        assert complaint["status"] == "Open"


# ============================================================
# LEVEL 13
# INVALID PAGINATION
# ============================================================


def test_complaint_invalid_page():
    response = client.get(
        COMPLAINTS_URL,
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_complaint_invalid_limit():
    response = client.get(
        COMPLAINTS_URL,
        params={
            "limit": 0,
        },
    )

    assert response.status_code == 422


def test_complaint_limit_greater_than_100():
    response = client.get(
        COMPLAINTS_URL,
        params={
            "limit": 101,
        },
    )

    assert response.status_code == 422


# ============================================================
# LEVEL 13
# INVALID SORT ORDER
# ============================================================


def test_complaint_invalid_sort_order():
    response = client.get(
        COMPLAINTS_URL,
        params={
            "sort_order": "invalid",
        },
    )

    assert response.status_code == 422