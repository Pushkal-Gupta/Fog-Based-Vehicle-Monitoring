"""Generate synthetic cloud data and train persisted model artifacts."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cloud_ai.pipeline import run_training_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full cloud AI training pipeline")
    parser.add_argument("--output-dir", default=".", help="Directory for CSV and model artifacts")
    parser.add_argument("--rows", type=int, default=1000, help="Synthetic dataset row count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    result = run_training_pipeline(output_dir=args.output_dir, rows=args.rows, seed=args.seed)
    print("Pipeline complete:")
    for key, value in result.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
