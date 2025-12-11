import os

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
