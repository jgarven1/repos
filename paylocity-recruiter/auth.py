"""
Login to Paylocity and handle MFA by pausing for manual completion.
"""

from playwright.sync_api import Page, TimeoutError as PWTimeoutError
import config


def login(page: Page) -> None:
    """
    Open talent.paylocity.com and wait for the user to log in manually.
    This handles SSO, MFA, and any other auth method without needing
    credentials in the .env file.
    """
    print("Opening Paylocity Recruiting in the browser...")
    page.goto(config.LOGIN_URL, timeout=config.PAGE_TIMEOUT_MS)

    print("\nLog in to Paylocity Recruiting in the browser window (use your normal method).")
    print("Once you can see the Jobs Dashboard or Recruiting home page, come back here.")
    input("Press Enter to continue... ")
    print("Continuing...\n")


def is_logged_in(page: Page) -> bool:
    """Return True if the dashboard/home page is visible."""
    try:
        page.wait_for_selector(
            "[data-testid='home'], nav, .dashboard, #mainContent",
            timeout=8_000,
        )
        return True
    except PWTimeoutError:
        return False
