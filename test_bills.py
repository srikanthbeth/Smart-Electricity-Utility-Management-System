import os
from datetime import date

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "smart_electricity_utility_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app


client = TestClient(app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def setup_function(function):
    db = SessionLocal()

    try:
        # Delete in dependency order
        db.execute(text("DELETE FROM bills"))
        db.execute(text("DELETE FROM meter_readings"))
        db.execute(text("DELETE FROM meters"))
        db.execute(text("DELETE FROM tariffs"))
        db.execute(text("DELETE FROM connections"))
        db.execute(text("DELETE FROM customers"))
        db.commit()
    finally:
        db.close()


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


def create_customer(
    customer_number="CUST-BILL-001",
    email="billcustomer@example.com",
):
    response = client.post(
        "/api/v1/customers",
        json={
            "customer_number": customer_number,
            "full_name": "Bill Test Customer",
            "email": email,
            "phone": "9876543210",
            "address": "Bill Test Address",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_connection(
    customer_id,
    connection_number="CONN-BILL-001",
    connection_type="Residential",
    status="Active",
):
    response = client.post(
        "/api/v1/connections",
        json={
            "customer_id": customer_id,
            "connection_number": connection_number,
            "connection_type": connection_type,
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": "2026-01-01",
            "status": status,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_meter(
    connection_id,
    meter_number="METER-BILL-001",
):
    response = client.post(
        "/api/v1/meters",
        json={
            "connection_id": connection_id,
            "meter_number": meter_number,
            "meter_type": "Smart",
            "installation_date": "2026-01-01",
            "initial_reading": 0,
            "current_reading": 150,
            "meter_status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_meter_reading(
    meter_id,
    reading_date="2026-01-31",
    previous_reading=0,
    current_reading=150,
    reading_source="Manual",
):
    response = client.post(
        "/api/v1/meter-readings",
        json={
            "meter_id": meter_id,
            "reading_date": reading_date,
            "previous_reading": previous_reading,
            "current_reading": current_reading,
            "reading_source": reading_source,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_tariff(
    tariff_name="Residential 101-200",
    connection_type="Residential",
    minimum_units=101,
    maximum_units=200,
    rate_per_unit=7,
    fixed_charge=50,
):
    response = client.post(
        "/api/v1/tariffs",
        json={
            "tariff_name": tariff_name,
            "connection_type": connection_type,
            "minimum_units": minimum_units,
            "maximum_units": maximum_units,
            "rate_per_unit": rate_per_unit,
            "fixed_charge": fixed_charge,
            "effective_from": "2026-01-01",
            "effective_to": None,
            "status": True,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_bill(
    connection_id,
    billing_month="2026-01-01",
    tax=100,
    late_fee=0,
    discount=20,
    due_date="2026-02-15",
):
    return client.post(
        "/api/v1/bills/generate",
        json={
            "connection_id": connection_id,
            "billing_month": billing_month,
            "tax": tax,
            "late_fee": late_fee,
            "discount": discount,
            "due_date": due_date,
        },
    )


def create_complete_bill_setup(
    customer_number="CUST-BILL-SETUP-001",
    email="billsetup@example.com",
    connection_number="CONN-BILL-SETUP-001",
    meter_number="METER-BILL-SETUP-001",
):
    customer = create_customer(
        customer_number=customer_number,
        email=email,
    )

    connection = create_connection(
        customer_id=customer["id"],
        connection_number=connection_number,
    )

    meter = create_meter(
        connection_id=connection["id"],
        meter_number=meter_number,
    )

    reading = create_meter_reading(
        meter_id=meter["id"],
    )

    tariff = create_tariff()

    return {
        "customer": customer,
        "connection": connection,
        "meter": meter,
        "reading": reading,
        "tariff": tariff,
    }


def update_bill_status(
    bill_id,
    bill_status,
):
    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                UPDATE bills
                SET bill_status = :bill_status
                WHERE id = :bill_id
                """
            ),
            {
                "bill_status": bill_status,
                "bill_id": bill_id,
            },
        )

        db.commit()
    finally:
        db.close()


# -------------------------------------------------------------------
# Bill creation
# -------------------------------------------------------------------


def test_generate_bill():
    setup = create_complete_bill_setup(
        customer_number="CUST-GEN-001",
        email="genbill@example.com",
        connection_number="CONN-GEN-001",
        meter_number="METER-GEN-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_id"] == setup["connection"]["id"]
    assert data["billing_month"] == "2026-01-01"
    assert data["units_consumed"] == 150
    assert data["bill_status"] == "Generated"


def test_energy_charge_calculated_automatically():
    setup = create_complete_bill_setup(
        customer_number="CUST-ENERGY-001",
        email="energy@example.com",
        connection_number="CONN-ENERGY-001",
        meter_number="METER-ENERGY-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=0,
        late_fee=0,
        discount=0,
    )

    assert response.status_code == 201

    data = response.json()

    # 150 units × ₹7
    assert data["energy_charge"] == 1050


def test_fixed_charge_taken_from_tariff():
    setup = create_complete_bill_setup(
        customer_number="CUST-FIXED-001",
        email="fixed@example.com",
        connection_number="CONN-FIXED-001",
        meter_number="METER-FIXED-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=0,
        late_fee=0,
        discount=0,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["fixed_charge"] == 50


def test_total_amount_calculated_correctly():
    setup = create_complete_bill_setup(
        customer_number="CUST-TOTAL-001",
        email="total@example.com",
        connection_number="CONN-TOTAL-001",
        meter_number="METER-TOTAL-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=100,
        late_fee=25,
        discount=20,
    )

    assert response.status_code == 201

    data = response.json()

    # 1050 + 50 + 100 + 25 - 20 = 1205
    assert data["total_amount"] == 1205


def test_bill_status_is_generated():
    setup = create_complete_bill_setup(
        customer_number="CUST-STATUS-001",
        email="status@example.com",
        connection_number="CONN-STATUS-001",
        meter_number="METER-STATUS-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert response.status_code == 201

    assert response.json()["bill_status"] == "Generated"


# -------------------------------------------------------------------
# Bill retrieval
# -------------------------------------------------------------------


def test_get_all_bills():
    setup = create_complete_bill_setup(
        customer_number="CUST-ALL-001",
        email="allbills@example.com",
        connection_number="CONN-ALL-001",
        meter_number="METER-ALL-001",
    )

    create_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/bills"
    )

    assert response.status_code == 200

    data = response.json()

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
        item["id"] == create_response.json()["id"]
        for item in data["items"]
    )


def test_get_bill_by_id():
    setup = create_complete_bill_setup(
        customer_number="CUST-BYID-001",
        email="byid@example.com",
        connection_number="CONN-BYID-001",
        meter_number="METER-BYID-001",
    )

    create_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert create_response.status_code == 201

    bill_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/bills/{bill_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == bill_id


def test_get_nonexistent_bill():
    response = client.get(
        "/api/v1/bills/999999"
    )

    assert response.status_code == 404


def test_get_customer_bills():
    setup = create_complete_bill_setup(
        customer_number="CUST-CUSTOMER-001",
        email="customerbills@example.com",
        connection_number="CONN-CUSTOMER-001",
        meter_number="METER-CUSTOMER-001",
    )

    create_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/customers/{setup['customer']['id']}/bills"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["connection_id"] == setup["connection"]["id"]


def test_get_connection_bills():
    setup = create_complete_bill_setup(
        customer_number="CUST-CONNECTION-001",
        email="connectionbills@example.com",
        connection_number="CONN-CONNECTION-001",
        meter_number="METER-CONNECTION-001",
    )

    create_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/connections/{setup['connection']['id']}/bills"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["connection_id"] == setup["connection"]["id"]


def test_get_bills_for_nonexistent_customer():
    response = client.get(
        "/api/v1/customers/999999/bills"
    )

    assert response.status_code == 200

    assert response.json() == []


def test_get_bills_for_nonexistent_connection():
    response = client.get(
        "/api/v1/connections/999999/bills"
    )

    assert response.status_code == 404


# -------------------------------------------------------------------
# Business rules
# -------------------------------------------------------------------


def test_duplicate_bill_for_same_connection_and_month():
    setup = create_complete_bill_setup(
        customer_number="CUST-DUP-001",
        email="duplicate@example.com",
        connection_number="CONN-DUP-001",
        meter_number="METER-DUP-001",
    )

    first_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert first_response.status_code == 201

    second_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert second_response.status_code == 409


def test_disconnected_connection_cannot_generate_bill():
    customer = create_customer(
        customer_number="CUST-DISC-001",
        email="disconnected@example.com",
    )

    connection = create_connection(
        customer_id=customer["id"],
        connection_number="CONN-DISC-001",
        status="Disconnected",
    )

    response = create_bill(
        connection_id=connection["id"],
    )

    assert response.status_code == 400


def test_nonexistent_connection_cannot_generate_bill():
    response = create_bill(
        connection_id=999999,
    )

    assert response.status_code == 404


def test_bill_requires_meter_reading():
    customer = create_customer(
        customer_number="CUST-NOREADING-001",
        email="noreading@example.com",
    )

    connection = create_connection(
        customer_id=customer["id"],
        connection_number="CONN-NOREADING-001",
    )

    create_tariff(
        tariff_name="No Reading Tariff",
    )

    response = create_bill(
        connection_id=connection["id"],
    )

    assert response.status_code == 404


def test_bill_requires_applicable_tariff():
    customer = create_customer(
        customer_number="CUST-NOTARIFF-001",
        email="notariff@example.com",
    )

    connection = create_connection(
        customer_id=customer["id"],
        connection_number="CONN-NOTARIFF-001",
    )

    meter = create_meter(
        connection_id=connection["id"],
        meter_number="METER-NOTARIFF-001",
    )

    create_meter_reading(
        meter_id=meter["id"],
    )

    # No tariff is created.

    response = create_bill(
        connection_id=connection["id"],
    )

    assert response.status_code == 404


def test_bill_amount_greater_than_zero():
    setup = create_complete_bill_setup(
        customer_number="CUST-POSITIVE-001",
        email="positive@example.com",
        connection_number="CONN-POSITIVE-001",
        meter_number="METER-POSITIVE-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert response.status_code == 201

    assert response.json()["total_amount"] > 0


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------


def test_negative_tax_rejected():
    setup = create_complete_bill_setup(
        customer_number="CUST-TAX-001",
        email="tax@example.com",
        connection_number="CONN-TAX-001",
        meter_number="METER-TAX-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=-10,
    )

    assert response.status_code == 422


def test_negative_late_fee_rejected():
    setup = create_complete_bill_setup(
        customer_number="CUST-LATE-001",
        email="late@example.com",
        connection_number="CONN-LATE-001",
        meter_number="METER-LATE-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        late_fee=-10,
    )

    assert response.status_code == 422


def test_negative_discount_rejected():
    setup = create_complete_bill_setup(
        customer_number="CUST-DISCOUNT-001",
        email="discount@example.com",
        connection_number="CONN-DISCOUNT-001",
        meter_number="METER-DISCOUNT-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        discount=-10,
    )

    assert response.status_code == 422


def test_billing_month_must_be_first_day():
    setup = create_complete_bill_setup(
        customer_number="CUST-DATE-001",
        email="billdate@example.com",
        connection_number="CONN-DATE-001",
        meter_number="METER-DATE-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
        billing_month="2026-01-15",
    )

    assert response.status_code == 422


def test_bill_response_contains_all_fields():
    setup = create_complete_bill_setup(
        customer_number="CUST-FIELDS-001",
        email="fields@example.com",
        connection_number="CONN-FIELDS-001",
        meter_number="METER-FIELDS-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert response.status_code == 201

    data = response.json()

    expected_fields = {
        "id",
        "connection_id",
        "billing_month",
        "units_consumed",
        "energy_charge",
        "fixed_charge",
        "tax",
        "late_fee",
        "discount",
        "total_amount",
        "due_date",
        "bill_status",
    }

    assert expected_fields.issubset(data.keys())


# ===================================================================
# LEVEL 13 - BILL FILTERING
# ===================================================================


def test_filter_bills_by_billing_month():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-MONTH-001",
        email="filtermonth@example.com",
        connection_number="CONN-FILTER-MONTH-001",
        meter_number="METER-FILTER-MONTH-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
        billing_month="2026-01-01",
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    response = client.get(
        "/api/v1/bills?billing_month=2026-01-01"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id
    assert data["items"][0]["billing_month"] == "2026-01-01"


def test_filter_bills_by_payment_status():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-STATUS-001",
        email="filterstatus@example.com",
        connection_number="CONN-FILTER-STATUS-001",
        meter_number="METER-FILTER-STATUS-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    update_bill_status(
        bill_id,
        "Paid",
    )

    response = client.get(
        "/api/v1/bills?payment_status=Paid"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id
    assert data["items"][0]["bill_status"] == "Paid"


def test_filter_bills_by_overdue_status():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-OVERDUE-001",
        email="filteroverdue@example.com",
        connection_number="CONN-FILTER-OVERDUE-001",
        meter_number="METER-FILTER-OVERDUE-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
        due_date="2026-02-15",
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    response = client.get(
        "/api/v1/bills?overdue_status=overdue"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id


def test_filter_bills_by_not_overdue_status():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-NOTOVERDUE-001",
        email="filternotoverdue@example.com",
        connection_number="CONN-FILTER-NOTOVERDUE-001",
        meter_number="METER-FILTER-NOTOVERDUE-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
        due_date="2099-12-31",
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    response = client.get(
        "/api/v1/bills?overdue_status=not_overdue"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id


def test_filter_bills_by_minimum_amount():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-MIN-001",
        email="filtermin@example.com",
        connection_number="CONN-FILTER-MIN-001",
        meter_number="METER-FILTER-MIN-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=100,
        late_fee=0,
        discount=20,
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    # Total = 1050 + 50 + 100 - 20 = 1180
    response = client.get(
        "/api/v1/bills?amount_min=1000"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id
    assert data["items"][0]["total_amount"] >= 1000


def test_filter_bills_by_maximum_amount():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-MAX-001",
        email="filtermax@example.com",
        connection_number="CONN-FILTER-MAX-001",
        meter_number="METER-FILTER-MAX-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=100,
        late_fee=0,
        discount=20,
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    # Total = 1180
    response = client.get(
        "/api/v1/bills?amount_max=1200"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id
    assert data["items"][0]["total_amount"] <= 1200


def test_filter_bills_by_amount_range():
    setup = create_complete_bill_setup(
        customer_number="CUST-FILTER-RANGE-001",
        email="filterrange@example.com",
        connection_number="CONN-FILTER-RANGE-001",
        meter_number="METER-FILTER-RANGE-001",
    )

    bill_response = create_bill(
        connection_id=setup["connection"]["id"],
        tax=100,
        late_fee=0,
        discount=20,
    )

    assert bill_response.status_code == 201

    bill_id = bill_response.json()["id"]

    # Total = 1180
    response = client.get(
        "/api/v1/bills?amount_min=1100&amount_max=1200"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == bill_id

    assert (
        1100
        <= data["items"][0]["total_amount"]
        <= 1200
    )


def test_invalid_bill_amount_range():
    response = client.get(
        "/api/v1/bills?amount_min=2000&amount_max=1000"
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "amount_min cannot be greater than amount_max"
    )


# ===================================================================
# LEVEL 13 - BILL PAGINATION
# ===================================================================


def test_bills_pagination():
    for index in range(5):
        setup = create_complete_bill_setup(
            customer_number=f"CUST-PAGE-{index}-001",
            email=f"page{index}@example.com",
            connection_number=f"CONN-PAGE-{index}-001",
            meter_number=f"METER-PAGE-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/bills?page=1&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 2


def test_bills_second_page():
    for index in range(5):
        setup = create_complete_bill_setup(
            customer_number=f"CUST-SECOND-{index}-001",
            email=f"second{index}@example.com",
            connection_number=f"CONN-SECOND-{index}-001",
            meter_number=f"METER-SECOND-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/bills?page=2&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 2


def test_bills_last_page():
    for index in range(5):
        setup = create_complete_bill_setup(
            customer_number=f"CUST-LAST-{index}-001",
            email=f"last{index}@example.com",
            connection_number=f"CONN-LAST-{index}-001",
            meter_number=f"METER-LAST-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/bills?page=3&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 3
    assert data["limit"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert len(data["items"]) == 1


def test_bills_page_beyond_available_pages():
    setup = create_complete_bill_setup(
        customer_number="CUST-BEYOND-001",
        email="beyond@example.com",
        connection_number="CONN-BEYOND-001",
        meter_number="METER-BEYOND-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/bills?page=10&limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 10
    assert data["limit"] == 10
    assert data["total"] == 1
    assert data["items"] == []


# ===================================================================
# LEVEL 13 - BILL SORTING
# ===================================================================


def test_bills_sort_by_total_amount_ascending():
    amounts = [
        (100, 0, 20),   # 1180
        (300, 0, 20),   # 1380
        (0, 0, 20),     # 1080
    ]

    for index, (
        tax,
        late_fee,
        discount,
    ) in enumerate(amounts):

        setup = create_complete_bill_setup(
            customer_number=f"CUST-SORT-ASC-{index}-001",
            email=f"sortasc{index}@example.com",
            connection_number=f"CONN-SORT-ASC-{index}-001",
            meter_number=f"METER-SORT-ASC-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
            tax=tax,
            late_fee=late_fee,
            discount=discount,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/bills"
        "?sort_by=total_amount"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    amounts = [
        item["total_amount"]
        for item in data["items"]
    ]

    assert amounts == sorted(amounts)


def test_bills_sort_by_total_amount_descending():
    amounts = [
        (100, 0, 20),   # 1180
        (300, 0, 20),   # 1380
        (0, 0, 20),     # 1080
    ]

    for index, (
        tax,
        late_fee,
        discount,
    ) in enumerate(amounts):

        setup = create_complete_bill_setup(
            customer_number=f"CUST-SORT-DESC-{index}-001",
            email=f"sortdesc{index}@example.com",
            connection_number=f"CONN-SORT-DESC-{index}-001",
            meter_number=f"METER-SORT-DESC-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
            tax=tax,
            late_fee=late_fee,
            discount=discount,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/bills"
        "?sort_by=total_amount"
        "&sort_order=desc"
    )

    assert response.status_code == 200

    data = response.json()

    amounts = [
        item["total_amount"]
        for item in data["items"]
    ]

    assert amounts == sorted(
        amounts,
        reverse=True,
    )


def test_bills_sort_by_due_date_ascending():
    due_dates = [
        "2026-03-15",
        "2026-02-15",
        "2026-04-15",
    ]

    for index, due_date in enumerate(due_dates):

        setup = create_complete_bill_setup(
            customer_number=f"CUST-DUE-ASC-{index}-001",
            email=f"dueasc{index}@example.com",
            connection_number=f"CONN-DUE-ASC-{index}-001",
            meter_number=f"METER-DUE-ASC-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
            due_date=due_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/bills"
        "?sort_by=due_date"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    due_dates = [
        item["due_date"]
        for item in data["items"]
    ]

    assert due_dates == sorted(due_dates)


def test_bills_invalid_sort_field_uses_default_sort():
    setup = create_complete_bill_setup(
        customer_number="CUST-INVALID-SORT-001",
        email="invalidsort@example.com",
        connection_number="CONN-INVALID-SORT-001",
        meter_number="METER-INVALID-SORT-001",
    )

    response = create_bill(
        connection_id=setup["connection"]["id"],
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/bills"
        "?sort_by=invalid_field"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert isinstance(data["items"], list)


# ===================================================================
# LEVEL 13 - FILTER + PAGINATION + SORTING
# ===================================================================


def test_bills_filter_pagination_and_sorting_together():
    bills = [
        {
            "tax": 100,
            "late_fee": 0,
            "discount": 20,
            "status": "Paid",
        },
        {
            "tax": 300,
            "late_fee": 0,
            "discount": 20,
            "status": "Paid",
        },
        {
            "tax": 200,
            "late_fee": 0,
            "discount": 20,
            "status": "Paid",
        },
        {
            "tax": 500,
            "late_fee": 0,
            "discount": 20,
            "status": "Generated",
        },
    ]

    paid_bill_ids = []

    for index, bill_data in enumerate(bills):

        setup = create_complete_bill_setup(
            customer_number=f"CUST-COMBINED-{index}-001",
            email=f"combined{index}@example.com",
            connection_number=f"CONN-COMBINED-{index}-001",
            meter_number=f"METER-COMBINED-{index}-001",
        )

        response = create_bill(
            connection_id=setup["connection"]["id"],
            tax=bill_data["tax"],
            late_fee=bill_data["late_fee"],
            discount=bill_data["discount"],
        )

        assert response.status_code == 201

        bill_id = response.json()["id"]

        if bill_data["status"] == "Paid":
            update_bill_status(
                bill_id,
                "Paid",
            )

            paid_bill_ids.append(bill_id)

    response = client.get(
        "/api/v1/bills"
        "?payment_status=Paid"
        "&amount_min=1100"
        "&amount_max=1400"
        "&page=1"
        "&limit=2"
        "&sort_by=total_amount"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    # Paid bills:
    # tax=100 -> 1180
    # tax=300 -> 1380
    # tax=200 -> 1280
    #
    # All three are inside 1100-1400.
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2

    assert len(data["items"]) == 2

    amounts = [
        item["total_amount"]
        for item in data["items"]
    ]

    assert amounts == sorted(amounts)

    for item in data["items"]:
        assert item["bill_status"] == "Paid"
        assert 1100 <= item["total_amount"] <= 1400