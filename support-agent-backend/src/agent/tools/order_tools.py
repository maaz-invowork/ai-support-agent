from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import Order

@tool
async def get_order_status(order_id: str) -> str:
    """Fetch status and full details for a given order ID (e.g., ORD-1001)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return f"Order '{order_id}' was not found in our database. Please double-check the Order ID."
        
        details = (
            f"Order ID: {order.id}\n"
            f"Item Name: {order.item_name or 'N/A'}\n"
            f"Status: {order.status}\n"
            f"Total Amount: ${order.total_amount:.2f}\n"
            f"Description: {order.status_description or 'N/A'}"
        )
        if order.tracking_number:
            details += f"\nTracking Number: {order.tracking_number}"
        if order.cancellation_reason:
            details += f"\nCancellation Reason: {order.cancellation_reason}"
            
        return details


@tool
async def cancel_order(order_id: str, reason: str = "Requested by user") -> str:
    """Cancel an eligible order if it has not yet shipped or been delivered."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            return f"Order {order_id} was not found."
            
        if order.status.lower() in ["shipped", "delivered"]:
            return f"Order {order_id} ({order.item_name or 'Item'}) cannot be cancelled because its status is '{order.status}'."
            
        order.status = "Cancelled"
        order.cancellation_reason = reason
        order.status_description = f"Order cancelled. Reason: {reason}"
        await session.commit()
        
        return f"Successfully cancelled Order {order.id} ({order.item_name or 'Item'}). Reason: {reason}"