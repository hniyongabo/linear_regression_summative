# Electricity Access Prediction

## Mission & Problem
This project supports the broader mission of understanding and closing infrastructure gaps that limit tech access and economic opportunity, particularly across Africa. Reliable electricity access is a foundational requirement for internet connectivity, digital literacy, and participation in the tech economy. This project uses World Bank data to build a regression model predicting a country's electricity access percentage based on year, income group, and region — surfacing patterns in which regions and income levels are furthest from full access.

**Dataset source:** World Bank Open Data — [Access to electricity indicator](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS), merged with [Country Metadata] (included in the zip file) for Region and Income Group classification.

## API — Public Swagger UI
🔗 **https://linear-regression-summative-iu9s.onrender.com/**

Test predictions directly via the `/predict` endpoint, or trigger retraining with new data via `/retrain` — both available and testable through the Swagger UI above.

## Model Performance

Four regression approaches were trained and compared on the same features (Year, Income Group, Region):

| Model | Train MSE | Test MSE |
|---|---|---|
| SGD (Stochastic Gradient Descent) | 185.76 | 189.96 |
| Linear Regression | 184.89 | 190.13 |
| Random Forest | 83.03 | 144.38 |
| Decision Tree | 82.70 | 152.97 |

**Best model: Random Forest** — lowest Test MSE (144.38), meaning it generalizes better than the alternatives. SGD and Linear Regression perform almost identically (as expected, since SGD is an iterative solver for the same underlying linear model) and show no overfitting, but underfit the data overall. Random Forest and Decision Tree fit training data much more closely but show a wider train-test gap, indicating some overfitting — Random Forest's averaging across many trees reduces this compared to a single Decision Tree, which is why it was selected as the deployed model.

## Video Demo
🔗 **[https://youtu.be/yJ0nN0hrGhk]**

## Running the Mobile App

**Requirements:** Flutter SDK installed ([install guide](https://docs.flutter.dev/get-started/install))

1. Clone this repository
2. Navigate to the Flutter app folder:

cd summative/flutter_app

3. Install dependencies:

flutter pub get

4. Run the app (choose your target device):

flutter run -d windows

or for a connected Android device:

flutter run

5. Select **Year**, **Income Group**, and **Region** from the dropdowns, then tap **Predict** to see the model's prediction.

The app connects to the live deployed API automatically — no local server setup needed to use the app.
