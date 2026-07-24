# Import FastAPI and create the app instance
from fastapi import FastAPI

app = FastAPI(title="Electricity Access Prediction API")

# Allow requests from any origin so the Flutter app (running on a different domain/port) can call this API
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)