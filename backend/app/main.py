import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import Base, apply_schema_updates, engine
from app import models
from app.routers import account, auth, messages, social


Base.metadata.create_all(bind=engine)
apply_schema_updates()

app = FastAPI()

origins = os.getenv("ALLOW_ORIGINS", "").split(",")

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


app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(social.router)
app.include_router(account.router)
