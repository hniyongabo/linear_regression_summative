# Import FastAPI and create the app instance
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import pandas as pd
import io
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
    year: int = Field(..., ge=1990, le=2030, description="Year to predict for", json_schema_extra={"example": 2005})
    income_group_num: int = Field(..., ge=0, le=3, description="0=Low, 1=Lower middle, 2=Upper middle, 3=High income", json_schema_extra={"example": 2})
    region: str = Field(..., description="One of: East Asia & Pacific, Europe & Central Asia, Latin America & Caribbean, Middle East & North Africa, North America, South Asia, Sub-Saharan Africa", json_schema_extra={"example": "Latin America & Caribbean"})
    
# Load the trained model, scaler, and country metadata once, when the API starts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")

model = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
meta = pd.read_csv(os.path.join(MODEL_DIR, "Metadata_Country.csv"))

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

# Ordinal mapping for income groups, low to high
income_order = {
    "Low income": 0,
    "Lower middle income": 1,
    "Upper middle income": 2,
    "High income": 3
}

# Core prediction logic, shared by the API endpoint
def predict_electricity_access(year, income_group_num, region):
    if region not in VALID_REGIONS:
        raise HTTPException(status_code=400, detail=f"Invalid region. Must be one of: {VALID_REGIONS}")

    region_dummies = [1 if col == f"Region_{region}" else 0 for col in REGION_COLUMNS]
    feature_cols = ["Year", "IncomeGroup_num"] + REGION_COLUMNS
    features = pd.DataFrame([[year, income_group_num] + region_dummies], columns=feature_cols)

    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)
    return float(prediction[0])

# Try reading the file as a raw World Bank export first; if that fails, try reading it as-is
def read_flexible_csv(contents):
    try:
        df = pd.read_csv(io.BytesIO(contents), skiprows=4)
        if "Country Name" not in df.columns:
            raise ValueError("not in expected format")
        return df
    except Exception:
        return pd.read_csv(io.BytesIO(contents))

# Reshape wide-format data to long format, merge region/income info, and clean quietly
def clean_new_data(df):
    year_cols = [c for c in df.columns if str(c).strip().isdigit()]

    if year_cols:
        long_df = df.melt(
            id_vars=["Country Name", "Country Code"],
            value_vars=year_cols,
            var_name="Year",
            value_name="Electricity_Access"
        )
    else:
        long_df = df.copy()

    long_df = long_df.merge(meta[["Country Code", "Region", "IncomeGroup"]], on="Country Code", how="left")

    long_df["Year"] = pd.to_numeric(long_df["Year"], errors="coerce")
    long_df["Electricity_Access"] = pd.to_numeric(long_df["Electricity_Access"], errors="coerce")
    long_df["IncomeGroup_num"] = long_df["IncomeGroup"].map(income_order)

    region_dummies_new = pd.get_dummies(long_df["Region"], prefix="Region", drop_first=True)
    for col in REGION_COLUMNS:
        if col not in region_dummies_new.columns:
            region_dummies_new[col] = 0
    long_df = pd.concat([long_df, region_dummies_new[REGION_COLUMNS]], axis=1)

    feature_cols = ["Year", "IncomeGroup_num"] + REGION_COLUMNS
    clean_df = long_df[feature_cols + ["Electricity_Access"]].dropna()

    return clean_df

# API endpoint that accepts prediction requests
@app.post("/predict")
def predict(input_data: PredictionInput):
    result = predict_electricity_access(
        input_data.year,
        input_data.income_group_num,
        input_data.region
    )
    return {"predicted_electricity_access_percent": result}

# Endpoint that accepts a new CSV file, cleans it, and retrains the model on it
@app.post("/retrain")
async def retrain(file: UploadFile = File(...)):
    global model, scaler

    try:
        contents = await file.read()
        raw_df = read_flexible_csv(contents)
        clean_df = clean_new_data(raw_df)

        if len(clean_df) < 5:
            raise HTTPException(status_code=400, detail="Not enough usable rows after cleaning to retrain (need at least 5).")

        feature_cols = ["Year", "IncomeGroup_num"] + REGION_COLUMNS
        X_new = clean_df[feature_cols]
        y_new = clean_df["Electricity_Access"]

        new_scaler = StandardScaler()
        X_new_scaled = new_scaler.fit_transform(X_new)

        new_model = RandomForestRegressor(random_state=42)
        new_model.fit(X_new_scaled, y_new)

        joblib.dump(new_model, os.path.join(MODEL_DIR, "best_model.pkl"))
        joblib.dump(new_scaler, os.path.join(MODEL_DIR, "scaler.pkl"))

        model = new_model
        scaler = new_scaler

        return {"message": "Model retrained successfully", "rows_used": len(clean_df)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Retraining failed: {str(e)}")

# Redirect the root URL straight to Swagger UI
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

# Year=2005, IncomeGroup=Upper middle income, Region=Latin America & Caribbean
# Actual recorded Electricity Access for this row: 87.5%
if __name__ == "__main__":
    result = predict_electricity_access(2005, 2, "Latin America & Caribbean")
    print("Predicted electricity access:", result)
    print("Actual electricity access (from test set):", 87.5)
    print("Difference:", abs(result - 87.5))