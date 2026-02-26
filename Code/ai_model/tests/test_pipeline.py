import os
import tempfile
import unittest

from cloud_ai.pipeline import run_training_pipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_persists_dataset_and_models(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_training_pipeline(output_dir=tmpdir, rows=220, seed=9)

            self.assertTrue(os.path.exists(result["dataset"]))
            self.assertTrue(os.path.exists(result["rul_model"]))
            self.assertTrue(os.path.exists(result["failure_model"]))


if __name__ == "__main__":
    unittest.main()
