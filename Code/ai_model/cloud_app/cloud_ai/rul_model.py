"""Train Gradient Boosting regressor for future engine RUL prediction."""

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

RUL_FEATURES = [
    "thermal_stress_index",
    "brake_health_index",
    "mechanical_vibration_anomaly_score",
    "electrical_charging_efficiency_score",
    "vehicle_health_score",
]
RUL_TARGETS = {
    "engine": "engine_rul_pct_future",
    "brake": "brake_rul_pct_future",
    "battery": "battery_rul_pct_future",
}


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    if "brake_health_index" not in working.columns:
        if "brake_rul_pct" in working.columns:
            working["brake_health_index"] = (working["brake_rul_pct"] / 100.0).clip(0.0, 1.0)
        else:
            raise ValueError("Missing required feature 'brake_health_index' or fallback 'brake_rul_pct'.")
    return working


def train_rul_models(data_path: str = "cloud_health_history.csv") -> None:
    df = _prepare_dataframe(pd.read_csv(data_path))

    X = df[RUL_FEATURES]

    for prefix, target in RUL_TARGETS.items():
        print(f"\n--- Training {prefix.upper()} RUL Model ---")
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
        )

        model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
        )

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        print(f"RUL MAE: {mean_absolute_error(y_test, predictions):.4f}")
        print(f"RUL R2: {r2_score(y_test, predictions):.4f}")

        model_path = f"{prefix}_rul_model.pkl"
        # For backward compatibility, save engine model as rul_model.pkl as well
        if prefix == "engine":
            joblib.dump(model, "rul_model.pkl")
            print("Saved model to rul_model.pkl (backward compatibility)")
        joblib.dump(model, model_path)
        print(f"Saved model to {model_path}")

if __name__ == "__main__":
    train_rul_models()
