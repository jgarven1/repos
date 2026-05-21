from pathlib import Path
from playwright.sync_api import Page, BrowserContext

import config

SESSION_FILE = Path(__file__).parent / "session.json"


def ensure_logged_in(context: BrowserContext, page: Page) -> None:
    """Use saved session if available; otherwise do full login + MFA and save session."""
    if SESSION_FILE.exists():
        print("[Auth] Saved session found — skipping login.")
        page.goto(config.TALENT_URL)
        page.wait_for_load_state("load")
        # If we land on a login page the session expired — do full login
        if "login" in page.url.lower() or "access.paylocity" in page.url.lower():
            print("[Auth] Session expired, logging in again...")
            _full_login(context, page)
        else:
            print("[Auth] Session valid.")
    else:
        _full_login(context, page)


def _full_login(context: BrowserContext, page: Page) -> None:
    page.goto(config.PAYLOCITY_URL)
    page.wait_for_load_state("load")

    page.fill('input[name="CompanyId"], input[id*="company"], input[placeholder*="Company"]', config.COMPANY_ID)
    page.fill('input[name="Username"], input[id*="user"], input[type="email"]', config.USERNAME)
    page.fill('input[name="Password"], input[id*="pass"], input[type="password"]', config.PASSWORD)
    page.click('button[type="submit"], input[type="submit"]')

    print("\n[MFA] Complete the MFA prompt in the browser window, then press Enter here to continue...")
    input()

    # Save session so future runs skip MFA
    context.storage_state(path=str(SESSION_FILE))
    print(f"[Auth] Session saved to {SESSION_FILE}")
