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


def teardown_module(module):
    db = SessionLocal()

    try:
        db.execute(text("DELETE FROM tariffs"))
        db.commit()
    finally:
        db.close()


def create_tariff(
    tariff_name="Residential 0-100",
    connection_type="Residential",
    minimum_units=0,
    maximum_units=100,
    rate_per_unit=5,
    fixed_charge=50,
    effective_from="2026-01-01",
    effective_to=None,
    status=True,
):
    payload = {
        "tariff_name": tariff_name,
        "connection_type": connection_type,
        "minimum_units": minimum_units,
        "maximum_units": maximum_units,
        "rate_per_unit": rate_per_unit,
        "fixed_charge": fixed_charge,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "status": status,
    }

    return client.post(
        "/api/v1/tariffs",
        json=payload,
    )


def test_create_tariff():
    response = create_tariff()

    assert response.status_code == 201

    data = response.json()

    assert data["tariff_name"] == "Residential 0-100"
    assert data["connection_type"] == "Residential"
    assert data["minimum_units"] == 0
    assert data["maximum_units"] == 100
    assert data["rate_per_unit"] == 5
    assert data["fixed_charge"] == 50
    assert data["status"] is True


def test_create_commercial_tariff():
    response = create_tariff(
        tariff_name="Commercial 0-100",
        connection_type="Commercial",
        rate_per_unit=8,
        fixed_charge=100,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_type"] == "Commercial"
    assert data["rate_per_unit"] == 8


def test_create_industrial_tariff():
    response = create_tariff(
        tariff_name="Industrial 0-500",
        connection_type="Industrial",
        minimum_units=0,
        maximum_units=500,
        rate_per_unit=10,
        fixed_charge=200,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_type"] == "Industrial"


def test_create_open_ended_tariff():
    response = create_tariff(
        tariff_name="Residential 500+",
        connection_type="Residential",
        minimum_units=501,
        maximum_units=None,
        rate_per_unit=12,
        fixed_charge=150,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["minimum_units"] == 501
    assert data["maximum_units"] is None


def test_get_all_tariffs():
    response = client.get(
        "/api/v1/tariffs"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_update_tariff():
    create_response = create_tariff(
        tariff_name="Tariff To Update",
        rate_per_unit=6,
    )

    assert create_response.status_code == 201

    tariff_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tariffs/{tariff_id}",
        json={
            "tariff_name": "Updated Tariff",
            "rate_per_unit": 7,
            "fixed_charge": 75,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tariff_name"] == "Updated Tariff"
    assert data["rate_per_unit"] == 7
    assert data["fixed_charge"] == 75


def test_update_tariff_status():
    create_response = create_tariff(
        tariff_name="Status Tariff",
    )

    assert create_response.status_code == 201

    tariff_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tariffs/{tariff_id}",
        json={
            "status": False,
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] is False


def test_update_nonexistent_tariff():
    response = client.put(
        "/api/v1/tariffs/999999",
        json={
            "rate_per_unit": 10,
        },
    )

    assert response.status_code == 404


def test_delete_tariff():
    create_response = create_tariff(
        tariff_name="Tariff To Delete",
    )

    assert create_response.status_code == 201

    tariff_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/tariffs/{tariff_id}"
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/tariffs/{tariff_id}"
    )

    assert get_response.status_code == 404


def test_delete_nonexistent_tariff():
    response = client.delete(
        "/api/v1/tariffs/999999"
    )

    assert response.status_code == 404


def test_invalid_maximum_units():
    response = create_tariff(
        tariff_name="Invalid Units",
        minimum_units=200,
        maximum_units=100,
    )

    assert response.status_code == 422


def test_negative_minimum_units():
    response = create_tariff(
        tariff_name="Negative Minimum",
        minimum_units=-1,
    )

    assert response.status_code == 422


def test_negative_rate():
    response = create_tariff(
        tariff_name="Negative Rate",
        rate_per_unit=-5,
    )

    assert response.status_code == 422


def test_negative_fixed_charge():
    response = create_tariff(
        tariff_name="Negative Fixed Charge",
        fixed_charge=-10,
    )

    assert response.status_code == 422


def test_invalid_effective_dates():
    response = create_tariff(
        tariff_name="Invalid Dates",
        effective_from="2026-12-31",
        effective_to="2026-01-01",
    )

    assert response.status_code == 422


def test_inactive_tariff():
    response = create_tariff(
        tariff_name="Inactive Tariff",
        status=False,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] is False


def test_multiple_slabs():
    slabs = [
        {
            "tariff_name": "Residential 0-100",
            "minimum_units": 0,
            "maximum_units": 100,
            "rate_per_unit": 5,
        },
        {
            "tariff_name": "Residential 101-200",
            "minimum_units": 101,
            "maximum_units": 200,
            "rate_per_unit": 7,
        },
        {
            "tariff_name": "Residential 201-500",
            "minimum_units": 201,
            "maximum_units": 500,
            "rate_per_unit": 9,
        },
        {
            "tariff_name": "Residential 500+",
            "minimum_units": 501,
            "maximum_units": None,
            "rate_per_unit": 12,
        },
    ]

    for slab in slabs:
        response = create_tariff(
            tariff_name=slab["tariff_name"],
            connection_type="Residential",
            minimum_units=slab["minimum_units"],
            maximum_units=slab["maximum_units"],
            rate_per_unit=slab["rate_per_unit"],
        )

        assert response.status_code == 201


def test_tariff_response_has_all_fields():
    response = create_tariff(
        tariff_name="Complete Tariff",
    )

    assert response.status_code == 201

    data = response.json()

    expected_fields = {
        "id",
        "tariff_name",
        "connection_type",
        "minimum_units",
        "maximum_units",
        "rate_per_unit",
        "fixed_charge",
        "effective_from",
        "effective_to",
        "status",
    }

    assert expected_fields.issubset(data.keys())


def test_update_invalid_unit_range():
    create_response = create_tariff(
        tariff_name="Range Update Test",
    )

    assert create_response.status_code == 201

    tariff_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tariffs/{tariff_id}",
        json={
            "minimum_units": 300,
            "maximum_units": 100,
        },
    )

    assert response.status_code == 400


def test_update_invalid_effective_dates():
    create_response = create_tariff(
        tariff_name="Date Update Test",
    )

    assert create_response.status_code == 201

    tariff_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tariffs/{tariff_id}",
        json={
            "effective_from": "2026-12-31",
            "effective_to": "2026-01-01",
        },
    )

    assert response.status_code == 400