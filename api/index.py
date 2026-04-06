import os
import sys

# Append backend directory to module path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Signal to backend that it is running in serverless environment
os.environ["VERCEL"] = "1"

from app import create_app
app = create_app()
