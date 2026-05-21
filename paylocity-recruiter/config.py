import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

EMAIL    = os.environ.get("PAYLOCITY_EMAIL", "")
PASSWORD = os.environ.get("PAYLOCITY_PASSWORD", "")
OUTPUT_DIR = pathlib.Path(os.environ.get("OUTPUT_DIR", "output"))

PAYLOCITY_URL = "https://www.paylocity.com"
LOGIN_URL     = f"{PAYLOCITY_URL}/portal/"

PAGE_TIMEOUT_MS = 30_000
