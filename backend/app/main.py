import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat_router, user_router

app = FastAPI()

origins = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello Hackathon"}


app.include_router(user_router.router)
app.include_router(chat_router.router)
