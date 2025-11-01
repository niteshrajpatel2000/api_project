from fastapi import FastAPI
from fastapi.params import Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

app = FastAPI()
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/")
def home():
    return {"message": "Hello, FastAPI is working!"}
@app.get("/welcome")
def welcome_message():
    return {"message": "👋 Welcome to your FastAPI server on Render! 🚀"}

@app.post("/add_user")
def add_user(name: str, email: str, db: Session = Depends(get_db)):
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "✅ User added successfully!", "user": {"id": user.id, "name": user.name,"email": user.email}}

# ✅ Get all users
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users