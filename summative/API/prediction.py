# Import libraries needed to load the model and handle input arrays
import joblib
import numpy as np
import os

# Build a path to the model folder that works no matter where this script is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")

# Load the trained model and the scaler used during training
model = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))

# Function that takes raw input values and returns a predicted electricity access %
def predict_electricity_access(year, income_group_num, region_dummies):
    features = np.array([[year, income_group_num] + region_dummies])
    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)
    return prediction[0]

# Example: run this file directly to test a sample prediction
if __name__ == "__main__":
    # region_dummies order: [Europe & Central Asia, Latin America & Caribbean,
    #                         Middle East & North Africa, North America,
    #                         South Asia, Sub-Saharan Africa]
    result = predict_electricity_access(2025, 2, [0, 0, 0, 0, 0, 1])
    print("Predicted electricity access:", result)