import os

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
    with SessionLocal() as db:
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


def test_dashboard():
    response = client.get(
        "/api/v1/dashboard"
    )

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "total_customers",
        "active_connections",
        "disconnected_connections",
        "total_meters",
        "faulty_meters",
        "monthly_units_consumed",
        "monthly_revenue",
        "pending_bills",
        "overdue_bills",
        "open_complaints",
        "resolved_complaints",
    }

    assert expected_fields.issubset(
        data.keys()
    )


def test_dashboard_values_are_numeric():
    response = client.get(
        "/api/v1/dashboard"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["total_customers"],
        int,
    )

    assert isinstance(
        data["active_connections"],
        int,
    )

    assert isinstance(
        data["total_meters"],
        int,
    )

    assert isinstance(
        data["faulty_meters"],
        int,
    )

    assert isinstance(
        data["monthly_units_consumed"],
        (int, float),
    )

    assert isinstance(
        data["monthly_revenue"],
        (int, float),
    )

    assert isinstance(
        data["pending_bills"],
        int,
    )

    assert isinstance(
        data["overdue_bills"],
        int,
    )

    assert isinstance(
        data["open_complaints"],
        int,
    )

    assert isinstance(
        data["resolved_complaints"],
        int,
    )