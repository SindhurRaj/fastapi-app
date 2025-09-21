import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")  # Render provides this

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------- DATABASE MODELS ----------
class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    phone = Column(String)
    menu_categories = relationship("MenuCategory", back_populates="restaurant")

class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    name = Column(String, nullable=False)
    restaurant = relationship("Restaurant", back_populates="menu_categories")
    menu_items = relationship("MenuItem", back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    category = relationship("MenuCategory", back_populates="menu_items")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    order_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    total_amount = Column(Float)
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")

# ----------------- 4. Create tables & insert sample data -----------------
# Create tables
Base.metadata.create_all(bind=engine)

# Insert sample data function
def init_sample_data():
    db = SessionLocal()
    try:
        # Only insert if no restaurant exists
        if not db.query(Restaurant).first():
            
            # ---- Restaurants ----
            r1 = Restaurant(name="Pizza Place", address="123 Main St", phone="1234567890")
            r2 = Restaurant(name="Burger Corner", address="456 Side St", phone="9876543210")
            db.add_all([r1, r2])
            db.commit()
            db.refresh(r1)
            db.refresh(r2)

            # ---- Categories ----
            cat1 = MenuCategory(name="Pizza", restaurant_id=r1.id)
            cat2 = MenuCategory(name="Drinks", restaurant_id=r1.id)
            cat3 = MenuCategory(name="Burgers", restaurant_id=r2.id)
            cat4 = MenuCategory(name="Drinks", restaurant_id=r2.id)
            db.add_all([cat1, cat2, cat3, cat4])
            db.commit()
            db.refresh(cat1)
            db.refresh(cat2)
            db.refresh(cat3)
            db.refresh(cat4)

            # ---- Menu Items ----
            items = [
                MenuItem(name="Margherita", description="Cheese pizza", price=5.99, category_id=cat1.id),
                MenuItem(name="Coke", description="Soft drink", price=1.5, category_id=cat2.id),
                MenuItem(name="Veggie Burger", description="Tasty veggie burger", price=4.5, category_id=cat3.id),
                MenuItem(name="Pepsi", description="Soft drink", price=1.5, category_id=cat4.id)
            ]
            db.add_all(items)
            db.commit()

            # ---- Customer ----
            customer = Customer(name="Sindhur", email="sindhur@example.com", phone="1122334455")
            db.add(customer)
            db.commit()

            print("Sample data inserted successfully ✅")
    finally:
        db.close()

# Call this function once at app startup
init_sample_data()

# ----------------- 5. FastAPI app -----------------
app = FastAPI()

# ----------------- 6. Endpoints -----------------
@app.get("/")
def health():
    return {"message": "API is running ✅"}

@app.get("/restaurants")
def get_restaurants():
    db = SessionLocal()
    try:
        data = [{"id": r.id, "name": r.name, "address": r.address, "phone": r.phone} 
                for r in db.query(Restaurant).all()]
        return data
    finally:
        db.close()

@app.get("/menu/{restaurant_id}")
def get_menu(restaurant_id: int):
    db = SessionLocal()
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        menu = []
        for cat in restaurant.menu_categories:
            items = [{"id": i.id, "name": i.name, "price": i.price} for i in cat.menu_items]
            menu.append({"category": cat.name, "items": items})
        return menu
    finally:
        db.close()