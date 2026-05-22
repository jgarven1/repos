"""
Login to Paylocity and handle MFA by pausing for manual completion.
"""

from playwright.sync_api import Page, TimeoutError as PWTimeoutError
import config


def login(page: Page) -> None:
    """
    Establish sessions on both Paylocity subdomains:
      1. talent.paylocity.com  — Jobs Dashboard
      2. go.paylocity.com      — Job detail / candidate pages

    Both require authentication. The user logs in manually so any
    SSO or MFA method is supported.
    """
    # Step 1: log in on talent.paylocity.com
    print("Opening Paylocity Recruiting (talent.paylocity.com)...")
    page.goto(config.LOGIN_URL, timeout=config.PAGE_TIMEOUT_MS)
    print("\nLog in using your normal method (SSO, MFA, etc.).")
    print("Once you can see the Jobs Dashboard, come back here.")
    input("Press Enter once logged in to talent.paylocity.com... ")

    # Step 2: also authenticate on go.paylocity.com
    print("\nNow opening go.paylocity.com to establish that session too...")
    page.goto("https://go.paylocity.com/recruiting/", timeout=config.PAGE_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=config.PAGE_TIMEOUT_MS)
    print("If you see a login page, log in again. If you see Paylocity content, you're good.")
    input("Press Enter once go.paylocity.com is loaded and showing Paylocity content... ")

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
