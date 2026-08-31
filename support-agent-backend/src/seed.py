import asyncio
from sqlalchemy import select
from db.database import AsyncSessionLocal, engine
from db.models import Base, Order, Policy

INITIAL_POLICIES = [
    {
        "title": "Return & Refund Policy",
        "category": "returns",
        "content": "Customers can return any physical item within 30 days of delivery for a full refund. Items must be unopened and in original packaging. Return shipping costs are free for defective items, otherwise covered by the customer. Refunds take 3-5 business days after inspection."
    },
    {
        "title": "Shipping Policy",
        "category": "shipping",
        "content": "Standard shipping takes 3-5 business days within the continental US. Express shipping takes 1-2 business days. Free standard shipping applies to orders over $50. International shipping times range from 7-14 business days depending on customs."
    },
    {
        "title": "Cancellation Policy",
        "category": "cancellation",
        "content": "Orders can be canceled within 2 hours of placement without penalty if they haven't entered the processing state. Once shipped, orders cannot be canceled and must follow the standard return process."
    },
    {
        "title": "Warranty & Replacement Policy",
        "category": "warranty",
        "content": "All electronic products come with a 1-year limited manufacturer warranty covering hardware defects. Accidental damage or water damage is not covered under the standard warranty."
    }
]

INITIAL_ORDERS = [
    {
        "id": "ORD-1001",
        "status": "Processing",
        "item_name": "polo blue shirt",
        "tracking_number": "TRK987654123",
        "total_amount": 129.99,
        "status_description": "Order received and being prepared in warehouse.",
        "shipping_address": "54 Gulberg, Lahore."

    },
    {
        "id": "ORD-1002",
        "status": "Shipped",
        "item_name": "remote control rc car",
        "tracking_number": "TRK987654124",
        "total_amount": 49.50,
        "status_description": "Package handed over to carrier.",
        "shipping_address": "98 Eden Park, Sailkot."
    },
    {
        "id": "ORD-1003",
        "status": "delivered",
        "item_name": "water bottle stainless steel",
        "tracking_number": "TRK987654125",
        "total_amount": 68.50,
        "status_description": "Package delivered at home.",
        "shipping_address": "892 Nawa Shair, Multan."
    }
]

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Seed Policies
        for policy_data in INITIAL_POLICIES:
            existing = await session.execute(
                select(Policy).where(Policy.title == policy_data["title"])
            )
            if not existing.scalar_one_or_none():
                session.add(Policy(**policy_data))

        # Seed Sample Orders
        for order_data in INITIAL_ORDERS:
            existing_order = await session.execute(
                select(Order).where(Order.id == order_data["id"])
            )
            if not existing_order.scalar_one_or_none():
                session.add(Order(**order_data))

        await session.commit()
        print("Successfully seeded PostgreSQL database with policies and sample orders!")

if __name__ == "__main__":
    asyncio.run(seed_data())