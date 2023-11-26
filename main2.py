from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    create_engine,
    MetaData,
)
from pydantic import BaseModel

engine = create_engine("sqlite:///./.venv/server/master.db")
metadata = MetaData()
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
app = FastAPI()

origins = [
    "0.0.0.0:5173",
    "0.0.0.0:5174",
    "http://localhost:5171",
    "http://localhost:5172",
    'http://127.0.0.0:5173',
    "http://localhost:5174",
    "http://localhost:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
