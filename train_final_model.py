import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
from xgboost import plot_importance
import time

print("--- STAGE 1: LOADING & CLEANING MASTER DATA ---")
start_time = time.time()

# 1. Load a massive 500k chunk. 
df = pd.read_csv('100_Batches_IndPenSim_V3.csv', nrows=500000)

TARGET = 'Offline Biomass concentratio(X_offline:X(g L^{-1}))'
features = [
    'Time (h)',
    'Aeration rate(Fg:L/h)',
    'Vessel Weight(Wt:Kg)',
    'Air head pressure(pressure:bar)',
    'Dissolved oxygen concentration(DO2:mg/L)',
    'Oil flow(Foil:L/hr)',
    'Vessel Volume(V:L)',
    'Substrate concentration(S:g/L)',
    'Oxygen in percent in off-gas(O2:O2  (%))'
]

# Force numeric to fix sensor glitches
for col in features + [TARGET]:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop empty rows so we only keep data where the lab tech actually measured Biomass
df_clean = df[features + [TARGET]].dropna()
print(f"Cleaned dataset: Found {len(df_clean)} verified biological lab samples out of 500,000 sensor logs.")

X = df_clean[features]
y = df_clean[TARGET]

print("\n--- STAGE 2: THE 3-WAY SPLIT ---")
# Split 1: Lock away 15% as completely blind data
X_temp, X_blind, y_temp, y_blind = train_test_split(X, y, test_size=0.15, random_state=42)

# Split 2: Divide the rest into Train (80%) and Validation (20%)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.2, random_state=42)

print("\n--- STAGE 3: TRAINING THE XGBOOST ENGINE ---")
model = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

val_preds = model.predict(X_val)
r2_val = r2_score(y_val, val_preds)
mae_val = mean_absolute_error(y_val, val_preds)
print(f"Validation R-Squared: {r2_val * 100:.2f}% (MAE: {mae_val:.4f} g/L)")

print("\n--- STAGE 4: THE BLIND HOLD-OUT TEST ---")
blind_preds = model.predict(X_blind)
r2_blind = r2_score(y_blind, blind_preds)
mae_blind = mean_absolute_error(y_blind, blind_preds)
rmse_blind = np.sqrt(mean_squared_error(y_blind, blind_preds))

print(f"=====================================")
print(f"BLIND TEST RESULTS ({len(X_blind)} unseen lab samples)")
print(f"R-Squared Score:                 {r2_blind * 100:.2f}%")
print(f"Mean Absolute Error (MAE):       {mae_blind:.4f} g/L")
print(f"Root Mean Squared Error (RMSE):  {rmse_blind:.4f} g/L")
print(f"=====================================\n")

print("--- STAGE 5: EXPORTING ARTIFACTS ---")
joblib.dump(model, 'bio_twin_model.pkl')
print("Saved: bio_twin_model.pkl")

plot_importance(model, max_num_features=8, importance_type='weight')
plt.savefig('xgboost_features.png', bbox_inches='tight')
print("Saved: xgboost_features.png")

print(f"\nPIPELINE COMPLETE in {round(time.time() - start_time, 2)} seconds.")