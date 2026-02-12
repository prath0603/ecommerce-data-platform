from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List


# ================= USER =================
class UserCreate(BaseModel):
    email: str
    full_name: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ================= PRODUCT =================
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    created_at: datetime

    class Config:
        from_attributes = True


# ================= ORDER ITEM =================
class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    price_at_purchase: float

    class Config:
        from_attributes = True


# ================= ORDER =================
class OrderCreate(BaseModel):
    user_id: UUID
    items: List[OrderItemCreate]


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
