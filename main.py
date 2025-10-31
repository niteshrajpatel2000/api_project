from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, FastAPI is working!"}
@app.get("/welcome")
def hello():
    return {"message": "👋 Welcome to your FastAPI server on Render! 🚀"}
