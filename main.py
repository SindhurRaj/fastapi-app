import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Render injects DATABASE_URL into environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

class UserSchema(BaseModel):
    username: str
    email: str

@app.get("/")
def home():
    return {"message": "API is running ✅"}

@app.post("/register")
def register(user: UserSchema):
    db = SessionLocal()
    db_user = User(username=user.username, email=user.email)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"id": db_user.id, "username": db_user.username, "email": db_user.email}
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        db.close()

@app.get("/users")
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]
