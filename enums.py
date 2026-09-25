from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "Super Admin"
    BILLING_OFFICER = "Billing Officer"
    FIELD_TECHNICIAN = "Field Technician"
    CUSTOMER_SERVICE_AGENT = "Customer Service Agent"
    CUSTOMER = "Customer"