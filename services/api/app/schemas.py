from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    created_at: datetime

    class Config:
        from_attributes = True
