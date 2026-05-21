"""
Login to Paylocity and handle MFA by pausing for manual completion.
"""

from playwright.sync_api import Page, TimeoutError as PWTimeoutError
import config


def login(page: Page) -> None:
    """
    Navigate to Paylocity, fill credentials, then pause so the user
    can complete MFA in the browser window. Press Enter to continue.
    """
    print("Navigating to Paylocity login...")
    page.goto(config.LOGIN_URL, timeout=config.PAGE_TIMEOUT_MS)

    # Fill email/username
    try:
        page.wait_for_selector(
            "input[type='email'], input[name='Username'], input[placeholder*='user' i]",
            timeout=config.PAGE_TIMEOUT_MS,
        )
        page.fill(
            "input[type='email'], input[name='Username'], input[placeholder*='user' i]",
            config.EMAIL,
        )
    except PWTimeoutError:
        raise RuntimeError("Could not find the username/email field on the login page.")

    # Fill password
    try:
        page.fill("input[type='password']", config.PASSWORD)
    except Exception:
        raise RuntimeError("Could not find the password field on the login page.")

    # Submit
    try:
        page.click(
            "button[type='submit'], button:has-text('Sign In'), button:has-text('Log In')",
            timeout=8_000,
        )
    except PWTimeoutError:
        raise RuntimeError("Could not find the login submit button.")

    # Pause for MFA
    print("\nIf MFA is required, complete it in the browser window now.")
    input("Press Enter once you are fully logged in and can see the Paylocity dashboard... ")
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
