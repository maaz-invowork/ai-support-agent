from core.celery_app import celery_app
from core.email_service import EmailService
from db.database import AsyncSessionLocal
from db.models import User, Order
from sqlalchemy import select


@celery_app.task(name="send_order_cancellation_email")
def send_order_cancellation_email(order_id: str, reason: str, user_email: str = None):    
    if not user_email:
        print(f"No user email found for order {order_id}")
        return False
    
    success = EmailService.send_order_cancellation_email(user_email, order_id, reason)
    return success
