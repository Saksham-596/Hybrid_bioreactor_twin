import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

def train_xgboost_hybrid():
    print("Loading reality data...")
    df = pd.read_csv("bioreactor_training_data.csv")

    # Inputs: Time and Toxicity | Output: The Error (Residual)
    X = df[['time', 'toxicity_factor']]
    y = df['error_X']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training XGBoost Regressor...")
    # These parameters are 'tuned' for biological decay patterns
    model = xgb.XGBRegressor(
        n_estimators=200,    # 200 trees fixing each other's mistakes
        learning_rate=0.05,  # How fast it learns (lower is more precise)
        max_depth=6,         # How deep each tree goes
        subsample=0.8,       # Uses 80% of data per tree to prevent 'memorizing'
        random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluation
    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    
    print(f"\n--- XGBoost Performance ---")
    print(f"R-squared Accuracy: {r2:.5f}")

    # Export the brain
    joblib.dump(model, "hybrid_error_predictor.pkl")
    print("\n'hybrid_error_predictor.pkl' is ready.")

if __name__ == "__main__":
    train_xgboost_hybrid()