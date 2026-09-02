from typing import Optional
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import Order, User
from tasks import send_order_cancellation_email

@tool
async def get_my_orders(user_id: Annotated[int, InjectedState("user_id")]) -> str:
    """Fetch all orders belonging to the currently authenticated user with full details."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        if not orders:
            return "No orders were found for your account."

        order_details = []
        for order in orders:
            order_details.append(
                f"Order ID: {order.id}\n"
                f"Item Name: {order.item_name or 'N/A'}\n"
                f"Status: {order.status}\n"
                f"Tracking Number: {order.tracking_number or 'N/A'}\n"
                f"Total Amount: ${order.total_amount:.2f}\n"
                f"Status Description: {order.status_description or 'N/A'}\n"
                f"Shipping Address: {order.shipping_address or 'N/A'}\n"
                f"Cancellation Reason: {order.cancellation_reason or 'N/A'}\n"
                f"Created At: {order.created_at or 'N/A'}"
            )

        return "Your orders:\n\n" + "\n\n".join(order_details)

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
        
        # Get user email before updating order
        user_email = None
        if order.user_id:
            user_result = await session.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                user_email = user.email
            
        order.status = "Cancelled"
        order.cancellation_reason = reason
        order.status_description = f"Order cancelled. Reason: {reason}"
        await session.commit()
        
        if user_email:
            send_order_cancellation_email.delay(order_id, reason, user_email)
        
        return f"Successfully cancelled Order {order.id} ({order.item_name or 'Item'}). Reason: {reason}"