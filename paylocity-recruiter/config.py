"""
config.py — Load credentials and output path from .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("PAYLOCITY_USERNAME", "")
PASSWORD = os.getenv("PAYLOCITY_PASSWORD", "")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))

if not USERNAME or not PASSWORD:
    raise EnvironmentError(
        "PAYLOCITY_USERNAME and PAYLOCITY_PASSWORD must be set in your .env file."
    )
