from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from uuid import UUID
from .kafka_producer import send_order_event
from app.db.session import engine
from app.db.models import Base
from .db.session import get_db
from .db.models import User, Product, Order, OrderItem
from .schemas import (
    UserCreate, UserResponse,
    ProductCreate, ProductResponse,
    OrderCreate, OrderResponse
)


app = FastAPI(title="Ecommerce API 🚀")
Base.metadata.create_all(bind=engine)



@app.get("/")
def root():
    return {"message": "Ecommerce API Running 🚀"}


@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}


# ================= USERS =================
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


# ================= PRODUCTS =================
@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products", response_model=List[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ================= ORDERS =================
@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):

    # 1️⃣ Check if user exists
    user = db.query(User).filter(User.id == order.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_amount = 0

    # 2️⃣ Create Order (without committing yet)
    db_order = Order(user_id=order.user_id, total_amount=0)
    db.add(db_order)
    db.flush()  # Generates order ID before commit

    order_items_payload = []  # This will go to Kafka

    # 3️⃣ Process order items
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        item_total = float(product.price) * item.quantity
        total_amount += item_total

        db_item = OrderItem(
            order_id=db_order.id,
            product_id=product.id,
            quantity=item.quantity,
            price_at_purchase=product.price
        )
        db.add(db_item)

        # Prepare item data for Kafka event
        order_items_payload.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "price": float(product.price)
        })

    # 4️⃣ Update total amount
    db_order.total_amount = total_amount

    # 5️⃣ Commit DB transaction FIRST (important for consistency)
    db.commit()
    db.refresh(db_order)

    # 6️⃣ Send event to Kafka AFTER successful commit
    send_order_event({
        "event_type": "ORDER_CREATED",
        "order_id": db_order.id,
        "user_id": db_order.user_id,
        "total_amount": float(db_order.total_amount),
        "items": order_items_payload
    })

    return db_order



@app.get("/orders", response_model=List[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: UUID, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
