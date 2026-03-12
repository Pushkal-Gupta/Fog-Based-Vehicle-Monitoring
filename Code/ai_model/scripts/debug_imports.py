"""
Debug Imports Script
=====================
Testing imports to find where it hangs.
"""
import sys
import os

print("🔹 Step 0: Starting import check...")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloud_ai.schemas import CloudInput, CloudOutput, Recommendation
print("🔹 Step 1: schemas imported")

from cloud_ai.rul_model import RUL_FEATURES
print("🔹 Step 2: rul_model imported")

from cloud_ai.failure_model import FAILURE_FEATURES
print("🔹 Step 3: failure_model imported")

from cloud_ai.history import InMemoryHistoryProvider, summarize_history
print("🔹 Step 4: history imported")

from cloud_ai.explanation import explain_fault
print("🔹 Step 5: explanation imported")

from cloud_ai.recommendation import recommend_action
print("🔹 Step 6: recommendation imported")

print("✅ ALL IMPORTS SUCCESSFUL")
