# Smart Electricity Utility Management System

A real-world **Smart Electricity Utility Management System** built using **FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT Authentication, Role-Based Authorization, and Pytest**.

The system manages customers, electricity connections, meters, meter readings, tariffs, bills, payments, complaints, technicians, service requests, analytics, dashboards, and audit logs.

---

## Project Overview

The Smart Electricity Utility Management System provides REST APIs for managing the complete electricity utility lifecycle.

### Main Flow

```text
User Registration
       ↓
Customer Creation
       ↓
Connection Creation
       ↓
Meter Installation
       ↓
Meter Reading
       ↓
Tariff Application
       ↓
Bill Generation
       ↓
Payment
       ↓
Complaint
       ↓
Technician
       ↓
Service Request
       ↓
Approve Service Request
       ↓
Complete Service Request
       ↓
Consumption Analytics
       ↓
Dashboard
```

---

## Technologies Used

* Python 3.11
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Pydantic
* JWT Authentication
* Passlib / Bcrypt
* Pytest
* FastAPI TestClient
* Uvicorn
* Psycopg
* CORS Middleware

---

## Project Structure

```text
smart_electricity_utility/
│
├── alembic/
│   ├── versions/
│   │   ├── migration files
│   │   └── repair migrations
│   └── env.py
│
├── models/
│   ├── user.py
│   ├── customer.py
│   ├── connection.py
│   ├── meter.py
│   ├── meter_reading.py
│   ├── tariff.py
│   ├── bill.py
│   ├── payment.py
│   ├── complaint.py
│   ├── complaint_history.py
│   ├── technician.py
│   ├── service_request.py
│   └── audit_log.py
│
├── schemas/
│   ├── auth.py
│   ├── customer.py
│   ├── connection.py
│   ├── meter.py
│   ├── meter_reading.py
│   ├── tariff.py
│   ├── bill.py
│   ├── payment.py
│   ├── complaint.py
│   ├── technician.py
│   ├── service_request.py
│   ├── audit_log.py
│   └── ...
│
├── repositories/
│   ├── user_repository.py
│   ├── customer_repository.py
│   ├── connection_repository.py
│   ├── meter_repository.py
│   ├── meter_reading_repository.py
│   ├── tariff_repository.py
│   ├── bill_repository.py
│   ├── payment_repository.py
│   ├── complaint_repository.py
│   ├── technician_repository.py
│   ├── service_request_repository.py
│   └── audit_log_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── customer_service.py
│   ├── connection_service.py
│   ├── meter_service.py
│   ├── meter_reading_service.py
│   ├── tariff_service.py
│   ├── bill_service.py
│   ├── payment_service.py
│   ├── complaint_service.py
│   ├── technician_service.py
│   ├── service_request_service.py
│   ├── analytics_service.py
│   ├── dashboard_service.py
│   └── audit_log_service.py
│
├── routes/
│   ├── auth.py
│   ├── customers.py
│   ├── connections.py
│   ├── meters.py
│   ├── meter_readings.py
│   ├── tariffs.py
│   ├── bills.py
│   ├── payments.py
│   ├── complaints.py
│   ├── technicians.py
│   ├── service_requests.py
│   ├── analytics.py
│   ├── dashboard.py
│   ├── reports.py
│   └── audit_logs.py
│
├── utils/
│   ├── security.py
│   ├── dependencies.py
│   ├── enums.py
│   └── exceptions.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_customers.py
│   ├── test_connections.py
│   ├── test_meters.py
│   ├── test_meter_readings.py
│   ├── test_tariffs.py
│   ├── test_bills.py
│   ├── test_payments.py
│   ├── test_complaints.py
│   ├── test_technicians.py
│   ├── test_service_requests.py
│   ├── test_analytics.py
│   ├── test_dashboard.py
│   └── ...
│
├── config.py
├── database.py
├── main.py
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# Architecture

The application follows a layered architecture:

```text
Routes
   ↓
Services
   ↓
Repositories
   ↓
Models
   ↓
PostgreSQL
```

### Models

Models define the database tables and relationships.

### Schemas

Schemas validate incoming requests and outgoing responses using Pydantic.

### Repositories

Repositories handle database operations such as create, read, update, and delete.

### Services

Services contain the business logic and validation rules.

### Routes

Routes expose the application functionality through REST APIs.

### Utils

Utilities contain reusable functionality such as:

* JWT authentication
* Password hashing
* Role-based authorization
* Exception helpers
* Enums
* Dependencies

---

# Database

The project uses **PostgreSQL**.

Example database URL:

```text
postgresql+psycopg://postgres:<password>@localhost:5433/smart_electricity_utility
```

The test database can be configured separately.

Example:

```text
postgresql+psycopg://postgres:<password>@localhost:5433/smart_electricity_utility_test
```

---

# Database Migrations

Alembic is used for database schema migrations.

### Check migration heads

```powershell
alembic heads
```

### Check current migration

```powershell
alembic current
```

### View migration history

```powershell
alembic history
```

### Apply migrations

```powershell
alembic upgrade head
```

### Create a new migration

```powershell
alembic revision -m "migration description"
```

The current database migration reaches the latest project head.

---

# Authentication

The application uses JWT-based authentication.

Authentication endpoints include:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

JWT tokens contain information such as:

```text
sub
role
type
iat
exp
```

Two token types are supported:

* Access Token
* Refresh Token

---

# Password Security

Passwords are hashed using bcrypt.

The application also validates the bcrypt password size limitation.

Passwords greater than **72 UTF-8 bytes** are rejected instead of allowing bcrypt to fail unexpectedly.

Password verification also safely handles passwords exceeding the bcrypt limit.

---

# Roles

The application supports the following roles:

```text
Super Admin
Billing Officer
Field Technician
Customer Service Agent
Customer
```

Role-based authorization is implemented using FastAPI dependencies.

Example:

```python
require_roles(UserRole.SUPER_ADMIN)
```

---

# CORS

CORS middleware is enabled in `main.py`.

The current configuration allows:

```text
Origins: *
Methods: *
Headers: *
Credentials: true
```

This allows frontend applications to communicate with the FastAPI backend.

---

# Global Exception Handling

The application provides centralized exception handling for common API errors.

Examples include:

```text
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
500 Internal Server Error
```

Reusable exception helpers are maintained in:

```text
utils/exceptions.py
```

---

# Main Modules

## Customers

Customer management includes:

```text
POST /api/v1/customers
GET  /api/v1/customers
GET  /api/v1/customers/{customer_id}
PUT  /api/v1/customers/{customer_id}
```

Customers are associated with electricity connections.

---

## Connections

Connections contain information such as:

* Customer
* Connection number
* Connection type
* Sanctioned load
* Tariff type
* Connection date
* Status

---

## Meters

Meters are associated with connections.

Meter information includes:

* Meter number
* Meter type
* Installation date
* Initial reading
* Current reading
* Meter status

Supported meter statuses include:

```text
Active
Faulty
Removed
```

---

# Meter Readings

Meter readings contain:

* Meter ID
* Reading date
* Previous reading
* Current reading
* Units consumed
* Reading source
* Remarks
* Billing year
* Billing month

Supported reading sources include:

```text
Manual
Smart Meter
Field Technician
```

Consumption is calculated from:

```text
Current Reading - Previous Reading
```

Example:

```text
1250 - 1000 = 250 units
```

A unique constraint prevents duplicate readings for the same meter and billing period.

---

# Tariffs

Tariffs contain:

* Tariff name
* Connection type
* Minimum units
* Maximum units
* Rate per unit
* Fixed charge
* Effective dates
* Status

Example tariff used in the demo:

```text
Tariff Name: Domestic Tariff 2026
Connection Type: Residential
Rate Per Unit: 6.5
Fixed Charge: 100
Effective From: 2026-09-01
Effective To: 2026-12-31
```

---

# Bills

Bills are generated using the connection, meter reading, tariff, taxes, discounts, late fees, and due date.

Demo calculation:

```text
Units consumed = 250
Rate per unit = ₹6.50

Energy charge:
250 × 6.50 = ₹1,625

Fixed charge:
₹100

Total:
₹1,625 + ₹100 = ₹1,725
```

The demo bill was successfully generated for:

```text
₹1,725
```

---

# Payments

Payments are associated with bills.

Supported payment statuses include:

```text
Pending
Success
Failed
Refunded
```

Demo payment:

```text
Amount: ₹1,725
Payment Method: UPI
Transaction ID: TXN-DEMO-20260925-001
Payment Status: Success
```

The payment was successfully created with:

```text
HTTP 201 Created
```

---

# Complaints

Customers can raise complaints related to their connections.

Complaint information includes:

* Customer
* Connection
* Complaint type
* Description
* Priority
* Status

A complaint was successfully created during the end-to-end demonstration.

---

# Technicians

Technicians can be registered with:

* Name
* Employee ID
* Phone
* Specialization
* Availability status

Supported technician specializations include:

```text
Meter Installation
Meter Replacement
Connection Inspection
Complaint Resolution
```

Demo technician:

```text
Name: Ramesh Kumar
Employee ID: TECH-DEMO-001
Phone: 9876543211
Specialization: Complaint Resolution
Availability: Available
```

---

# Service Requests

Service requests support the following request types:

```text
New Connection
Load Change
Meter Replacement
Name Change
Address Change
Disconnection
Reconnection
```

Service request statuses follow the workflow:

```text
Submitted
    ↓
Approved
    ↓
Completed
```

Demo service request:

```text
Request Type: Meter Replacement
Status: Completed
```

The complete workflow was successfully tested:

```text
Submitted → Approved → Completed
```

---

# Analytics

The system provides several analytics APIs.

### Monthly Consumption

```text
GET /api/v1/analytics/connections/{connection_id}/monthly
```

### Yearly Consumption

```text
GET /api/v1/analytics/connections/{connection_id}/yearly
```

### Connection Usage

```text
GET /api/v1/analytics/connections/{connection_id}/usage
```

### Customer Usage

```text
GET /api/v1/analytics/customers/{customer_id}/usage
```

### Highest Consuming Connections

```text
GET /api/v1/analytics/highest-consuming-connections
```

### Average Monthly Consumption

```text
GET /api/v1/analytics/average-monthly-consumption
```

---

# Analytics Demo Result

For Connection ID `1`, the monthly consumption API returned:

```json
[
  {
    "month": "2026-09",
    "units_consumed": 250,
    "bill_amount": 1725
  }
]
```

This confirms that the meter reading, bill, and analytics calculations are working together correctly.

---

# Dashboard

Dashboard endpoint:

```text
GET /api/v1/dashboard
```

Successful demo response:

```json
{
  "total_customers": 1,
  "active_connections": 1,
  "disconnected_connections": 0,
  "total_meters": 1,
  "faulty_meters": 0,
  "monthly_units_consumed": 250,
  "monthly_revenue": 1725,
  "pending_bills": 0,
  "overdue_bills": 0,
  "open_complaints": 1,
  "resolved_complaints": 0
}
```

---

# Audit Logs

Audit logging is implemented to record important system actions.

Audit logs contain:

* User ID
* Action
* Entity type
* Entity ID
* Details
* Created timestamp

Super Admin authorization is used for audit log access.

Endpoints include:

```text
GET /api/v1/audit-logs
GET /api/v1/audit-logs/user/{user_id}
```

---

# Data Integrity

The project uses PostgreSQL constraints and SQLAlchemy relationships to maintain data integrity.

Implemented constraints include:

* Primary keys
* Foreign keys
* Unique constraints
* Not-null constraints
* Cascading relationships
* Unique meter reading per billing period
* Unique customer email
* Unique meter number

---

# Testing

The project uses **Pytest** and FastAPI `TestClient`.

Run all tests:

```powershell
python -m pytest -q
```

Run tests with verbose output:

```powershell
python -m pytest -v
```

Run a specific test file:

```powershell
python -m pytest tests/test_auth.py -v -s
```

Run dashboard tests:

```powershell
python -m pytest tests/test_dashboard.py -v -s
```

Run bill tests:

```powershell
python -m pytest tests/test_bills.py -v -s
```

---

# Test Result

The complete test suite was successfully executed.

```text
334 passed, 2 warnings
```

The warnings are dependency/deprecation warnings from the testing stack and did not cause test failures.

---

# End-to-End Demo Result

The complete manual Swagger workflow was successfully tested.

```text
✅ Register
✅ Create Customer
✅ Create Connection
✅ Install Meter
✅ Add Meter Reading
✅ Apply Tariff
✅ Generate Bill
✅ Make Payment
✅ Raise Complaint
✅ Create Technician
✅ Create Service Request
✅ Approve Service Request
✅ Complete Service Request
✅ Consumption Analytics
✅ Dashboard
```

---

# Demo Data

## Customer

```text
Customer ID: 1
Name: Ravi Kumar
Email: ravi.demo@example.com
Phone: 9876543210
City: Nandyal
Status: Active
```

## Connection

```text
Connection ID: 1
Connection Number: CONN-DEMO-001
Type: Residential
Sanctioned Load: 5
Tariff Type: Domestic
Status: Active
```

## Meter

```text
Meter ID: 1
Meter Number: METER-DEMO-001
Type: Smart
Initial Reading: 1000
Current Reading: 1000
Status: Active
```

## Meter Reading

```text
Previous Reading: 1000
Current Reading: 1250
Units Consumed: 250
Reading Source: Manual
```

## Tariff

```text
Tariff Name: Domestic Tariff 2026
Rate Per Unit: ₹6.50
Fixed Charge: ₹100
```

## Bill

```text
Bill Amount: ₹1,725
```

## Payment

```text
Amount: ₹1,725
Method: UPI
Status: Success
```

## Service Request

```text
Request Type: Meter Replacement
Status: Completed
```

---

# Running the Application

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Run the FastAPI application:

```powershell
uvicorn main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

# Environment Configuration

The application uses environment/database configuration for settings such as:

```text
DATABASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
```

Sensitive values such as database passwords and JWT secret keys should not be committed to source control.

---

# Security Features

Implemented security features include:

* JWT authentication
* Access tokens
* Refresh tokens
* Password hashing
* Password validation
* 72-byte bcrypt password protection
* Role-based authorization
* Active-user validation
* Foreign key constraints
* Unique constraints
* Global exception handling
* CORS
* Audit logging

---

# Future Enhancements

The following features can be implemented as future improvements:

* Soft delete
* Rate limiting
* More advanced request validation
* Database transaction improvements
* Technician assignment directly to service requests
* Complaint resolution workflow
* Notification system
* Email/SMS notifications
* Advanced billing slabs
* Payment refunds
* Production deployment
* Monitoring and logging
* Frontend dashboard

---

# API Documentation

Interactive Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The Swagger interface can be used to:

* Register users
* Authenticate
* Create customers
* Manage connections
* Manage meters
* Record readings
* Create tariffs
* Generate bills
* Make payments
* Create complaints
* Manage technicians
* Manage service requests
* View analytics
* View dashboard information
* View audit logs

---

# Project Status

```text
Project Status: Successfully Implemented

Backend: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Migration Tool: Alembic
Authentication: JWT
Authorization: RBAC
Testing: Pytest
API Documentation: Swagger / OpenAPI

Test Result:
334 passed, 2 warnings

End-to-End Demo:
Successfully Completed
```

---

## Author

**Srikanth Bethamcharla**
