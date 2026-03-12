"""Utilities to run full cloud AI training pipeline with persisted artifacts."""

from pathlib import Path

from cloud_ai.data_generation import generate_synthetic_cloud_history
from cloud_ai.failure_model import train_failure_model
from cloud_ai.rul_model import train_rul_models


def run_training_pipeline(output_dir: str = ".", rows: int = 1000, seed: int = 42) -> dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = target_dir / "cloud_health_history.csv"
    rul_model_path = target_dir / "rul_model.pkl"
    failure_model_path = target_dir / "failure_model.pkl"

    generate_synthetic_cloud_history(
        output_path=str(dataset_path),
        rows=rows,
        seed=seed,
    )
    train_rul_models(data_path=str(dataset_path))
    train_failure_model(data_path=str(dataset_path), model_path=str(failure_model_path))

    return {
        "dataset": str(dataset_path),
        "rul_model": str(rul_model_path),
        "failure_model": str(failure_model_path),
    }
