import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import time

print("Loading a safe 250k row sample into RAM...")
start_time = time.time()

# 1. Load the data safely
df = pd.read_csv('100_Batches_IndPenSim_V3.csv', nrows=250000)

# 2. Slice off the 2,000 Raman Spectroscopy columns (Keep only the first 37 core columns)
df = df.iloc[:, :37]

# 3. DEFINE YOUR EXACT TARGET AND TIME COLUMNS
TARGET = 'Offline Biomass concentratio(X_offline:X(g L^{-1}))'
TIME_COL = 'Time (h)'

# 4. Clean the data for training
# We drop Time from the training features (X) because time itself doesn't cause growth, the sensors do.
# We also drop text/ID columns that will crash Scikit-Learn.
cols_to_drop = [
    TARGET, TIME_COL, 'Batch ID', 'Batch reference(Batch_ref:Batch ref)', 'Fault reference(Fault_ref:Fault ref)',
    'Penicillin concentration(P:g/L)', 'Offline Penicillin concentration(P_offline:P(g L^{-1}))', 
    'Carbon evolution rate(CER:g/h)', 'carbon dioxide percent in off-gas(CO2outgas:%)', 'Viscosity(Viscosity_offline:centPoise)'
]

# Drop the columns if they exist in the dataframe
X = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

# Force drop any remaining accidental string/text columns
X = X.select_dtypes(include=['number']) 
y = df[TARGET]

# Drop rows where the target (Biomass) might be missing (NaN)
valid_indices = y.dropna().index
X = X.loc[valid_indices]
y = y.loc[valid_indices]

print(f"Data loaded and cleaned in {round(time.time() - start_time, 2)} seconds. Training RF model...")

# 5. Train the model using all Mac CPU cores (n_jobs=-1)
model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X, y)

# 6. Extract the Top 8 Features
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': model.feature_importances_
}).sort_values(by='Importance', ascending=False)

print("\n=== YOUR 8 PRODUCTION FEATURES FOR BIOMASS ===")
print(importances.head(8))