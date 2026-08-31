from datetime import datetime
from typing import Annotated, List, Optional, Sequence
from typing_extensions import TypedDict
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, description="User password (8-72 characters)")

class UserLogin(UserBase):
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or query")
    thread_id: Optional[str] = Field(default="default_session", description="LangGraph session thread ID")

class ChatResponse(BaseModel):
    response: str
    thread_id: str

class OrderBase(BaseModel):
    item_name: str
    status: str = Field(..., description="Order status (e.g., Processing, Shipped, Delivered)")
    price: float = Field(..., gt=0, description="Price of the item")
    shipping_address: str

class OrderCreate(OrderBase):
    id: str = Field(..., description="Order ID, e.g., ORD-232")
    user_id: int

class OrderResponse(OrderBase):
    id: str
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderLookupInput(BaseModel):
    order_id: str = Field(..., description="The unique order identifier, e.g., ORD-232")

class OrderRefundInput(BaseModel):
    order_id: str = Field(..., description="The unique order identifier to process refund for")
    reason: str = Field(..., description="Reason for the refund request")

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]