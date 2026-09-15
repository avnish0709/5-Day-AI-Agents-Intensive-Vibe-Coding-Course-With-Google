import os

# Configuration for ambient expense-approval agent
APPROVAL_THRESHOLD = 100.0
MODEL_NAME = os.getenv("EXPENSE_MODEL_NAME", "gemini-3.1-flash-lite")
