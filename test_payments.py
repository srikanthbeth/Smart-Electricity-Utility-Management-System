import os
from datetime import date, datetime

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
        db.execute(text("DELETE FROM payments"))
        db.execute(text("DELETE FROM bills"))
        db.execute(text("DELETE FROM meter_readings"))
        db.execute(text("DELETE FROM meters"))
        db.execute(text("DELETE FROM tariffs"))
        db.execute(text("DELETE FROM connections"))
        db.execute(text("DELETE FROM customers"))

        db.commit()
    finally:
        db.close()


def teardown_module(module):
    db = SessionLocal()

    try:
        db.execute(text("DELETE FROM payments"))
        db.execute(text("DELETE FROM bills"))
        db.execute(text("DELETE FROM meter_readings"))
        db.execute(text("DELETE FROM meters"))
        db.execute(text("DELETE FROM tariffs"))
        db.execute(text("DELETE FROM connections"))
        db.execute(text("DELETE FROM customers"))

        db.commit()
    finally:
        db.close()


def create_customer():
    response = client.post(
        "/api/v1/customers",
        json={
            "customer_number": "CUST-PAY-001",
            "full_name": "Payment Customer",
            "email": "payment.customer@example.com",
            "phone": "9876543210",
            "address": "Payment Street",
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
            "connection_number": "CONN-PAY-001",
            "connection_type": "Residential",
            "tariff_type": "Residential",
            "sanctioned_load": 5,
            "address": "Payment Street",
            "connection_date": "2026-09-22",
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
            "meter_number": "METER-PAY-001",
            "meter_type": "Smart",
            "initial_reading": 0,
            "current_reading": 150,
            "installation_date": "2026-01-01",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_meter_reading(meter_id):
    response = client.post(
        "/api/v1/meter-readings",
        json={
            "meter_id": meter_id,
            "reading_date": "2026-01-31",
            "previous_reading": 0,
            "current_reading": 150,
            "reading_source": "Manual",
            "remarks": "Payment test reading",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_tariff():
    response = client.post(
        "/api/v1/tariffs",
        json={
            "tariff_name": "Residential Payment Tariff",
            "connection_type": "Residential",
            "minimum_units": 101,
            "maximum_units": 200,
            "rate_per_unit": 7,
            "fixed_charge": 50,
            "effective_from": "2026-01-01",
            "effective_to": None,
            "status": True,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_bill():
    customer = create_customer()

    connection = create_connection(
        customer["id"]
    )

    meter = create_meter(
        connection["id"]
    )

    create_meter_reading(
        meter["id"]
    )

    create_tariff()

    response = client.post(
        "/api/v1/bills/generate",
        json={
            "connection_id": connection["id"],
            "billing_month": "2026-01-01",
            "tax": 100,
            "late_fee": 0,
            "discount": 20,
            "due_date": "2026-02-15",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_payment(
    bill_id,
    amount,
    transaction_id,
    payment_method="UPI",
    payment_status="Pending",
):
    response = client.post(
        f"/api/v1/payments/{bill_id}",
        json={
            "amount": amount,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "payment_date": "2026-01-31T10:00:00",
            "payment_status": payment_status,
        },
    )

    return response


def test_create_pending_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        bill["total_amount"],
        "TXN-PAY-001",
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["bill_id"] == bill["id"]
    assert data["amount"] == bill["total_amount"]
    assert data["payment_method"] == "UPI"
    assert data["transaction_id"] == "TXN-PAY-001"
    assert data["payment_status"] == "Pending"


def test_create_success_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        bill["total_amount"],
        "TXN-PAY-002",
        payment_status="Success",
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["payment_status"] == "Success"

    bill_response = client.get(
        f"/api/v1/bills/{bill['id']}"
    )

    assert bill_response.status_code == 200

    updated_bill = bill_response.json()

    assert updated_bill["bill_status"] == "Paid"


def test_failed_payment_does_not_update_bill():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        bill["total_amount"],
        "TXN-PAY-003",
        payment_status="Failed",
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["payment_status"] == "Failed"

    bill_response = client.get(
        f"/api/v1/bills/{bill['id']}"
    )

    assert bill_response.status_code == 200

    updated_bill = bill_response.json()

    assert updated_bill["bill_status"] == "Generated"


def test_payment_cannot_exceed_bill_amount():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        bill["total_amount"] + 1,
        "TXN-PAY-004",
    )

    assert response.status_code == 400
    assert (
        "cannot exceed"
        in response.json()["detail"].lower()
    )


def test_duplicate_transaction_is_prevented():
    bill = create_bill()

    first_response = create_payment(
        bill["id"],
        bill["total_amount"],
        "TXN-PAY-DUPLICATE",
    )

    assert first_response.status_code == 201

    second_response = create_payment(
        bill["id"],
        bill["total_amount"],
        "TXN-PAY-DUPLICATE",
    )

    assert second_response.status_code == 409

    assert (
        "duplicate"
        in second_response.json()["detail"].lower()
    )


def test_payment_for_nonexistent_bill():
    response = create_payment(
        999999,
        100,
        "TXN-PAY-005",
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Bill not found"
    )


def test_get_all_payments():
    bill = create_bill()

    create_payment(
        bill["id"],
        100,
        "TXN-PAY-006",
    )

    response = client.get(
        "/api/v1/payments"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["transaction_id"] == "TXN-PAY-006"


def test_get_payment_by_id():
    bill = create_bill()

    create_response = create_payment(
        bill["id"],
        100,
        "TXN-PAY-007",
    )

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/payments/{payment_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["bill_id"] == bill["id"]


def test_get_payment_not_found():
    response = client.get(
        "/api/v1/payments/999999"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Payment not found"
    )


def test_get_payments_by_bill():
    bill = create_bill()

    create_payment(
        bill["id"],
        100,
        "TXN-PAY-008",
    )

    create_payment(
        bill["id"],
        200,
        "TXN-PAY-009",
    )

    response = client.get(
        f"/api/v1/bills/{bill['id']}/payments"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    transaction_ids = {
        payment["transaction_id"]
        for payment in data
    }

    assert "TXN-PAY-008" in transaction_ids
    assert "TXN-PAY-009" in transaction_ids


def test_get_payments_for_nonexistent_bill():
    response = client.get(
        "/api/v1/bills/999999/payments"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Bill not found"
    )


def test_upi_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-UPI-001",
        payment_method="UPI",
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "UPI"


def test_card_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-CARD-001",
        payment_method="Card",
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Card"


def test_net_banking_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-NET-001",
        payment_method="Net Banking",
    )

    assert response.status_code == 201
    assert (
        response.json()["payment_method"]
        == "Net Banking"
    )


def test_wallet_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-WALLET-001",
        payment_method="Wallet",
    )

    assert response.status_code == 201
    assert (
        response.json()["payment_method"]
        == "Wallet"
    )


def test_invalid_payment_method():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-INVALID-METHOD",
        payment_method="Cash",
    )

    assert response.status_code == 422


def test_invalid_payment_status():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-INVALID-STATUS",
        payment_status="Completed",
    )

    assert response.status_code == 422


def test_zero_payment_amount():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        0,
        "TXN-ZERO",
    )

    assert response.status_code == 422


def test_negative_payment_amount():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        -100,
        "TXN-NEGATIVE",
    )

    assert response.status_code == 422


def test_refunded_payment():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-REFUND-001",
        payment_status="Refunded",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_status"] == "Refunded"

    bill_response = client.get(
        f"/api/v1/bills/{bill['id']}"
    )

    assert bill_response.status_code == 200

    updated_bill = bill_response.json()

    assert updated_bill["bill_status"] == "Generated"


def test_payment_response_contains_all_fields():
    bill = create_bill()

    response = create_payment(
        bill["id"],
        100,
        "TXN-FIELDS-001",
        payment_method="Card",
        payment_status="Success",
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert "bill_id" in data
    assert "amount" in data
    assert "payment_method" in data
    assert "transaction_id" in data
    assert "payment_date" in data
    assert "payment_status" in data