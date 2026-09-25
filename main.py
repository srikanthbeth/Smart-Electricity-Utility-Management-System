from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router

from routes.customers import router as customers_router

from routes.connections import router as connections_router

from routes.meters import router as meters_router

from routes.meter_readings import (
    router as meter_readings_router,
    meter_reading_meter_router,
    meter_reading_connection_router,
)

from routes.tariffs import router as tariffs_router

from routes.bills import (
    router as bills_router,
    customer_bill_router,
    connection_bill_router,
)

from routes.payments import (
    router as payments_router,
    bill_payment_router,
)

from routes.complaints import router as complaints_router

from routes.technicians import router as technicians_router

from routes.service_requests import (
    router as service_requests_router,
)

from routes.analytics import router as analytics_router

from routes.dashboard import router as dashboard_router

from routes.reports import router as reports_router

from routes.audit_logs import router as audit_logs_router


app = FastAPI(
    title="Smart Electricity Utility Management System",
    description="Electricity Utility Management API",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API PREFIX
# ============================================================

API_V1_PREFIX = "/api/v1"


# ============================================================
# AUTH ROUTES
# ============================================================

app.include_router(
    auth_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# CUSTOMER ROUTES
# ============================================================

app.include_router(
    customers_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# CONNECTION ROUTES
# ============================================================

app.include_router(
    connections_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# METER ROUTES
# ============================================================

app.include_router(
    meters_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# METER READING ROUTES
# ============================================================

app.include_router(
    meter_readings_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    meter_reading_meter_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    meter_reading_connection_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# TARIFF ROUTES
# ============================================================

app.include_router(
    tariffs_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# BILL ROUTES
# ============================================================

app.include_router(
    bills_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    customer_bill_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    connection_bill_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# PAYMENT ROUTES
# ============================================================

app.include_router(
    payments_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    bill_payment_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# COMPLAINT ROUTES
# ============================================================

app.include_router(
    complaints_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# TECHNICIAN ROUTES
# ============================================================

app.include_router(
    technicians_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# SERVICE REQUEST ROUTES
# ============================================================

app.include_router(
    service_requests_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# ANALYTICS ROUTES
# ============================================================

app.include_router(
    analytics_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# DASHBOARD ROUTES
# ============================================================

app.include_router(
    dashboard_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# REPORT ROUTES
# ============================================================

app.include_router(
    reports_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# AUDIT LOG ROUTES
# ============================================================

app.include_router(
    audit_logs_router,
    prefix=API_V1_PREFIX,
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Smart Electricity Utility Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_version": "/api/v1",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
    }