"""Train Random Forest classifier for near-term failure probability."""

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

FAILURE_FEATURES = [
    "engine_rul_pct",
    "brake_rul_pct",
    "battery_rul_pct",
    "thermal_stress_index",
    "mechanical_vibration_anomaly_score",
]
FAILURE_TARGET = "failure_next_7_days"


def train_failure_model(
    data_path: str = "cloud_health_history.csv",
    model_path: str = "failure_model.pkl",
) -> None:
    df = pd.read_csv(data_path)

    X = df[FAILURE_FEATURES]
    y = df[FAILURE_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        class_weight="balanced",
        random_state=42,
    )

    clf.fit(X_train, y_train)
    auc = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])

    print(f"Failure model AUC: {auc:.4f}")

    joblib.dump(clf, model_path)
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    train_failure_model()
