import os
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import logging
logging.basicConfig(level=logging.DEBUG)

from cloud_ai.recommendation import recommend_action

res = recommend_action(
    failure_prob=0.8,
    engine_rul_pct=30.0,
    brake_rul_pct=20.0,
    battery_rul_pct=50.0,
    fault_primary="TEST_FAULT",
    contributing_factors=["factor1", "factor2"]
)

print(f"Result: {res}")
