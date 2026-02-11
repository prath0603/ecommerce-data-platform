from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.schemas import ProductResponse
from app.db.models import Product

app = FastAPI()   # 👈 MUST COME BEFORE ROUTES


@app.get("/")
def root():
    return {"message": "Ecommerce API Running 🚀"}


@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}


@app.post("/products", response_model=ProductResponse)
def create_product():
    return {"message": "Product endpoint ready"}
