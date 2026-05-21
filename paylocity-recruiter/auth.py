import config
from playwright.sync_api import Page


def login(page: Page) -> None:
    """Navigate to Paylocity and log in. Pauses for manual MFA completion."""
    page.goto(config.PAYLOCITY_URL)
    page.wait_for_load_state("networkidle")

    # Fill credentials
    page.fill('input[name="Username"], input[id*="user"], input[type="email"]', config.USERNAME)
    page.fill('input[name="Password"], input[id*="pass"], input[type="password"]', config.PASSWORD)
    page.click('button[type="submit"], input[type="submit"]')

    print("\n[MFA] Complete the MFA prompt in the browser window, then press Enter here to continue...")
    input()

    # Wait for the dashboard to confirm login succeeded
    page.wait_for_load_state("networkidle")
    print("[Auth] Login confirmed.")
