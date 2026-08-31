from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import Order

@tool
async def get_order_status(order_id: str) -> str:
    """
    Retrieve the current status, items, and tracking details of a customer order by its Order ID.
    
    Args:
        order_id: The unique ID string of the order (e.g. 'ORD-12345').
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).where(Order.order_id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return f"Order '{order_id}' was not found in our database. Please double-check the Order ID."
        
        tracking_info = f" (Tracking Number: {order.tracking_number})" if getattr(order, 'tracking_number', None) else ""
        return (
            f"Order ID: {order.order_id}\n"
            f"Status: {order.status}\n"
            f"Placed On: {order.created_at.strftime('%Y-%m-%d %H:%M') if getattr(order, 'created_at', None) else 'N/A'}\n"
            f"Total Amount: ${order.total_amount:.2f}\n"
            f"Details: {order.status_description or 'No extra details'}{tracking_info}"
        )


@tool
async def cancel_order(order_id: str, reason: Optional[str] = None) -> str:
    """
    Cancel an existing order if it has not shipped yet.
    
    Args:
        order_id: The unique ID of the order to cancel.
        reason: Optional reason for cancellation provided by the customer.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).where(Order.order_id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return f"Order '{order_id}' not found. Cannot perform cancellation."
            
        if order.status.lower() in ["shipped", "delivered", "completed"]:
            return f"Cannot cancel Order '{order_id}' because its status is already '{order.status}'. You must request a return instead once received."
            
        if order.status.lower() == "cancelled":
            return f"Order '{order_id}' is already cancelled."
            
        # Update order status in DB
        order.status = "Cancelled"
        if hasattr(order, "cancellation_reason"):
            order.cancellation_reason = reason or "Customer requested cancellation via AI assistant"
            
        await session.commit()
        return f"Order '{order_id}' has been successfully cancelled."