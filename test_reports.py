import os

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "smart_electricity_utility_test"
)

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_daily_collection_report():
    response = client.get(
        "/api/v1/reports/daily-collection"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_monthly_revenue_report():
    response = client.get(
        "/api/v1/reports/monthly-revenue"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_customer_billing_report():
    response = client.get(
        "/api/v1/reports/customer-billing"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_connection_consumption_report():
    response = client.get(
        "/api/v1/reports/connection-consumption"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_technician_performance_report():
    response = client.get(
        "/api/v1/reports/technician-performance"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_complaint_resolution_report():
    response = client.get(
        "/api/v1/reports/complaint-resolution"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_outstanding_payment_report():
    response = client.get(
        "/api/v1/reports/outstanding-payments"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_customer_billing_fields():
    response = client.get(
        "/api/v1/reports/customer-billing"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert {
            "customer_id",
            "customer_name",
            "total_billed",
            "total_paid",
            "outstanding_amount",
        }.issubset(data[0].keys())

        assert isinstance(
            data[0]["customer_id"],
            int,
        )

        assert isinstance(
            data[0]["customer_name"],
            str,
        )

        assert isinstance(
            data[0]["total_billed"],
            (int, float),
        )

        assert isinstance(
            data[0]["total_paid"],
            (int, float),
        )

        assert isinstance(
            data[0]["outstanding_amount"],
            (int, float),
        )


def test_connection_consumption_fields():
    response = client.get(
        "/api/v1/reports/connection-consumption"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert {
            "connection_id",
            "connection_number",
            "units_consumed",
            "bill_amount",
        }.issubset(data[0].keys())

        assert isinstance(
            data[0]["connection_id"],
            int,
        )

        assert isinstance(
            data[0]["connection_number"],
            str,
        )

        assert isinstance(
            data[0]["units_consumed"],
            (int, float),
        )

        assert isinstance(
            data[0]["bill_amount"],
            (int, float),
        )


def test_outstanding_payment_fields():
    response = client.get(
        "/api/v1/reports/outstanding-payments"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert {
            "bill_id",
            "connection_id",
            "billing_month",
            "total_amount",
            "paid_amount",
            "outstanding_amount",
        }.issubset(data[0].keys())

        assert isinstance(
            data[0]["bill_id"],
            int,
        )

        assert isinstance(
            data[0]["connection_id"],
            int,
        )

        assert isinstance(
            data[0]["billing_month"],
            str,
        )

        assert isinstance(
            data[0]["total_amount"],
            (int, float),
        )

        assert isinstance(
            data[0]["paid_amount"],
            (int, float),
        )

        assert isinstance(
            data[0]["outstanding_amount"],
            (int, float),
        )