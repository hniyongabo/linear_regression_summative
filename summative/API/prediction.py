# Import FastAPI and create the app instance
# Redirect the root URL straight to Swagger UI
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import os

app = FastAPI(title="Electricity Access Prediction API")

# Allow requests from any origin so the Flutter app (running on a different domain/port) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the shape and constraints of data the /predict endpoint will accept
class PredictionInput(BaseModel):
    year: int = Field(..., ge=1990, le=2030, description="Year to predict for")
    income_group_num: int = Field(..., ge=0, le=3, description="0=Low, 1=Lower middle, 2=Upper middle, 3=High income")
    region: str = Field(..., description="One of: East Asia & Pacific, Europe & Central Asia, Latin America & Caribbean, Middle East & North Africa, North America, South Asia, Sub-Saharan Africa")

# Load the trained model and scaler once, when the API starts (not on every request)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")

model = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))

# The list of region columns, in the exact order used during training
REGION_COLUMNS = [
    "Region_Europe & Central Asia",
    "Region_Latin America & Caribbean",
    "Region_Middle East & North Africa",
    "Region_North America",
    "Region_South Asia",
    "Region_Sub-Saharan Africa",
]

# All valid region names, including the baseline one dropped during training
VALID_REGIONS = [
    "East Asia & Pacific",
    "Europe & Central Asia",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
]

# Core prediction logic, shared by the API endpoint
def predict_electricity_access(year, income_group_num, region):
    if region not in VALID_REGIONS:
        raise HTTPException(status_code=400, detail=f"Invalid region. Must be one of: {VALID_REGIONS}")

    # build the one-hot region values based on which region was selected
    region_dummies = [1 if col == f"Region_{region}" else 0 for col in REGION_COLUMNS]

    feature_cols = ["Year", "IncomeGroup_num"] + REGION_COLUMNS
    features = pd.DataFrame([[year, income_group_num] + region_dummies], columns=feature_cols)

    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)
    return float(prediction[0])

# API endpoint that accepts prediction requests
@app.post("/predict")
def predict(input_data: PredictionInput):
    result = predict_electricity_access(
        input_data.year,
        input_data.income_group_num,
        input_data.region
    )
    return {"predicted_electricity_access_percent": result}


@app.get("/")
def root():
    return RedirectResponse(url="/docs")

# Example: run this file directly to test a sample prediction (Task 1.4 requirement)
if __name__ == "__main__":
    result = predict_electricity_access(2025, 2, "Sub-Saharan Africa")
    print("Predicted electricity access:", result)