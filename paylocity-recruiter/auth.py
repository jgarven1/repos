"""
auth.py — Log into Paylocity and handle MFA pause.
"""
from playwright.sync_api import Page
from config import USERNAME, PASSWORD

LOGIN_URL = "https://access.paylocity.com/"


def login(page: Page) -> None:
    """Navigate to Paylocity login, fill credentials, then pause for MFA."""
    print("→ Navigating to Paylocity login…")
    page.goto(LOGIN_URL, wait_until="networkidle")

    # Fill username
    page.locator("input#Username, input[name='Username'], input[type='email']").first.fill(USERNAME)

    # Fill password
    page.locator("input#Password, input[name='Password'], input[type='password']").first.fill(PASSWORD)

    # Click login / submit
    page.locator("button[type='submit'], input[type='submit'], button:has-text('Log In')").first.click()

    print("✔ Credentials submitted.")
    print()
    print("━" * 60)
    print("  MFA STEP — complete the verification in the browser window,")
    print("  then come back here and press Enter to continue.")
    print("━" * 60)
    input("  Press Enter when you're past the MFA screen… ")
    print()

    # Wait for the page to settle after MFA
    page.wait_for_load_state("networkidle")
    print("✔ Login complete.")
