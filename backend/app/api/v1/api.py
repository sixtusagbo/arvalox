from fastapi import APIRouter

from app.api.v1 import auth, customers, invoices, payments, reports, subscriptions, webhooks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    customers.router, prefix="/customers", tags=["customers"]
)
api_router.include_router(
    invoices.router, prefix="/invoices", tags=["invoices"]
)
api_router.include_router(
    payments.router, prefix="/payments", tags=["payments"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
