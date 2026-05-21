import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("PAYLOCITY_USERNAME", "")
PASSWORD = os.getenv("PAYLOCITY_PASSWORD", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

PAYLOCITY_URL = "https://access.paylocity.com"
