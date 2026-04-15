"""
Plaud Web Transcript Automation
--------------------------------
Logs in to app.plaud.ai, iterates over every recording, triggers
AI transcript generation for any recording that does not yet have one,
and exports each finished transcript to a local directory.

Configuration (via environment variables or a .env file):
    PLAUD_EMAIL       – your Plaud account e-mail (only needed for email/password login)
    PLAUD_PASSWORD    – your Plaud account password (only needed for email/password login)
    EXPORT_DIR        – directory where transcripts are saved (default: ./transcripts)
    HEADLESS          – run browser without a visible window ("true"/"false", default: true)
    TRANSCRIPT_FORMAT – export format: "txt" or "docx" (default: txt)
    SESSION_FILE      – path to saved browser session (default: .plaud_session.json)

Google / SSO users
------------------
Run once with --setup to log in manually in a real browser window.
The session is saved to SESSION_FILE and reused on every subsequent run.

    python3 plaud_transcripts.py --setup
    python3 plaud_transcripts.py          # uses saved session from now on
"""

import os
import re
import sys
import time
import pathlib
import logging

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

EMAIL = os.environ.get("PLAUD_EMAIL", "")
PASSWORD = os.environ.get("PLAUD_PASSWORD", "")
EXPORT_DIR = pathlib.Path(os.environ.get("EXPORT_DIR", "transcripts"))
HEADLESS = os.environ.get("HEADLESS", "true").lower() not in ("false", "0", "no")
TRANSCRIPT_FORMAT = os.environ.get("TRANSCRIPT_FORMAT", "txt").lower()
SESSION_FILE = pathlib.Path(os.environ.get("SESSION_FILE", ".plaud_session.json"))

PLAUD_URL = "https://app.plaud.ai"
TRANSCRIPT_GENERATION_TIMEOUT_MS = 5 * 60 * 1000   # 5 minutes per recording
PAGE_LOAD_TIMEOUT_MS = 30_000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_filename(name: str) -> str:
    """Strip characters that are unsafe in filenames."""
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    return name.strip()


def wait_and_click(page, selector: str, timeout: int = PAGE_LOAD_TIMEOUT_MS):
    page.wait_for_selector(selector, timeout=timeout)
    page.click(selector)


def is_logged_in(page) -> bool:
    """Return True if the recording list is already visible (session is active)."""
    try:
        page.wait_for_selector(
            "[class*='record'], [class*='card'], [data-testid*='record'], li[class*='item']",
            timeout=8_000,
        )
        return True
    except PWTimeoutError:
        return False


# ---------------------------------------------------------------------------
# Setup mode — one-time manual login to save a session
# ---------------------------------------------------------------------------

def run_setup(pw):
    """
    Open a visible browser window so the user can log in (including via Google/SSO).
    Saves the authenticated session to SESSION_FILE when the user presses Enter.
    """
    log.info("=== SETUP MODE ===")
    log.info("A browser window will open. Log in to Plaud however you normally do.")
    log.info("When you are fully logged in and can see your recordings, come back here")
    log.info("and press Enter to save the session.")

    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.goto(PLAUD_URL, timeout=PAGE_LOAD_TIMEOUT_MS)

    input("\nPress Enter once you are logged in and can see your recordings... ")

    context.storage_state(path=str(SESSION_FILE))
    log.info("Session saved to '%s'.", SESSION_FILE)
    log.info("You can now run the script normally: python3 plaud_transcripts.py")

    context.close()
    browser.close()


# ---------------------------------------------------------------------------
# Login (email/password fallback)
# ---------------------------------------------------------------------------

def login_with_credentials(page):
    log.info("Logging in with email/password as %s", EMAIL)

    # Accept any cookie banner if present
    try:
        page.click("button:has-text('Accept')", timeout=5_000)
    except PWTimeoutError:
        pass

    page.wait_for_selector(
        "input[type='email'], input[name='email'], input[placeholder*='mail' i]",
        timeout=PAGE_LOAD_TIMEOUT_MS,
    )
    page.fill("input[type='email'], input[name='email'], input[placeholder*='mail' i]", EMAIL)
    page.fill("input[type='password']", PASSWORD)
    page.click("button[type='submit'], button:has-text('Sign in'), button:has-text('Log in')")

    page.wait_for_selector(
        "[class*='record'], [class*='card'], [data-testid*='record'], li[class*='item']",
        timeout=PAGE_LOAD_TIMEOUT_MS,
    )
    log.info("Login successful")


# ---------------------------------------------------------------------------
# Recording list
# ---------------------------------------------------------------------------

def get_recording_cards(page) -> list:
    """Return all recording card element handles visible on the page."""
    selectors = [
        "[class*='recordCard']",
        "[class*='record-card']",
        "[class*='noteCard']",
        "[class*='note-card']",
        "[class*='RecordItem']",
        "[data-testid='record-item']",
    ]
    for sel in selectors:
        cards = page.query_selector_all(sel)
        if cards:
            log.info("Found %d recording(s) using selector '%s'", len(cards), sel)
            return cards

    # Fallback: any element that contains an audio duration marker (e.g. "0:23")
    cards = page.query_selector_all("li, div")
    matched = [c for c in cards if re.search(r'\d+:\d{2}', c.inner_text())]
    log.info("Fallback: found %d recording(s) by duration pattern", len(matched))
    return matched


# ---------------------------------------------------------------------------
# Per-recording transcript workflow
# ---------------------------------------------------------------------------

def ensure_transcript_and_export(page, index: int, card) -> bool:
    """
    Open a recording, generate transcript if needed, export it.
    Returns True on success, False if the recording was skipped/errored.
    """
    try:
        label = card.query_selector("[class*='title'], [class*='name'], h3, h4").inner_text().strip()
    except Exception:
        label = f"recording_{index + 1}"
    label = safe_filename(label) or f"recording_{index + 1}"

    log.info("[%d] Opening '%s'", index + 1, label)

    try:
        card.click()
        page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
    except PWTimeoutError:
        log.warning("[%d] Timed out opening recording '%s', skipping", index + 1, label)
        return False

    # ---- Navigate to the Transcript tab --------------------------------
    try:
        transcript_tab = page.locator(
            "button:has-text('Transcript'), [role='tab']:has-text('Transcript'), "
            "a:has-text('Transcript'), [class*='transcript' i]"
        ).first
        transcript_tab.click(timeout=10_000)
        page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
    except PWTimeoutError:
        log.warning("[%d] No Transcript tab found for '%s'", index + 1, label)
        page.go_back()
        return False

    # ---- Generate transcript if it hasn't been generated yet ----------
    generate_btn = page.locator(
        "button:has-text('Generate'), button:has-text('Transcribe'), "
        "button:has-text('Create Transcript'), button:has-text('Start')"
    ).first
    if generate_btn.is_visible(timeout=3_000):
        log.info("[%d] Generating transcript for '%s'...", index + 1, label)
        generate_btn.click()
        try:
            page.wait_for_selector(
                "[class*='transcriptContent'], [class*='transcript-content'], "
                "[class*='TranscriptItem'], p[class*='segment']",
                timeout=TRANSCRIPT_GENERATION_TIMEOUT_MS,
            )
            log.info("[%d] Transcript ready for '%s'", index + 1, label)
        except PWTimeoutError:
            log.error("[%d] Transcript generation timed out for '%s'", index + 1, label)
            page.go_back()
            return False
    else:
        log.info("[%d] Transcript already exists for '%s'", index + 1, label)

    exported = _export_transcript(page, label, index)

    page.go_back()
    page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
    return exported


def _export_transcript(page, label: str, index: int) -> bool:
    """
    Try to export via the Export/Download button in the Plaud UI.
    Falls back to scraping the visible transcript text if no button is found.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    export_btn = page.locator(
        "button:has-text('Export'), button:has-text('Download'), "
        "[aria-label*='export' i], [aria-label*='download' i]"
    ).first

    if export_btn.is_visible(timeout=3_000):
        with page.expect_download(timeout=30_000) as dl_info:
            export_btn.click()
            try:
                fmt_btn = page.locator(
                    f"button:has-text('{TRANSCRIPT_FORMAT.upper()}'), "
                    f"li:has-text('{TRANSCRIPT_FORMAT.upper()}')"
                ).first
                fmt_btn.click(timeout=5_000)
            except PWTimeoutError:
                pass

        download = dl_info.value
        dest = EXPORT_DIR / f"{label}.{download.suggested_filename.rsplit('.', 1)[-1] or TRANSCRIPT_FORMAT}"
        download.save_as(dest)
        log.info("[%d] Saved transcript → %s", index + 1, dest)
        return True

    # Fallback: scrape visible text
    log.info("[%d] No export button found; scraping transcript text for '%s'", index + 1, label)
    transcript_blocks = page.query_selector_all(
        "[class*='transcriptContent'] p, [class*='transcript-content'] p, "
        "[class*='TranscriptItem'], p[class*='segment'], [class*='utterance']"
    )
    if not transcript_blocks:
        panel = page.query_selector("[class*='transcript' i]")
        raw = panel.inner_text() if panel else ""
    else:
        raw = "\n".join(b.inner_text() for b in transcript_blocks)

    if not raw.strip():
        log.warning("[%d] Could not extract transcript text for '%s'", index + 1, label)
        return False

    dest = EXPORT_DIR / f"{label}.txt"
    dest.write_text(raw, encoding="utf-8")
    log.info("[%d] Saved transcript (scraped) → %s", index + 1, dest)
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    setup_mode = "--setup" in sys.argv

    with sync_playwright() as pw:
        if setup_mode:
            run_setup(pw)
            return

        # Decide how to create the browser context
        has_session = SESSION_FILE.exists()
        browser = pw.chromium.launch(headless=HEADLESS)

        if has_session:
            log.info("Loading saved session from '%s'", SESSION_FILE)
            context = browser.new_context(
                storage_state=str(SESSION_FILE),
                accept_downloads=True,
            )
        else:
            context = browser.new_context(accept_downloads=True)

        page = context.new_page()
        page.set_default_timeout(PAGE_LOAD_TIMEOUT_MS)

        try:
            page.goto(PLAUD_URL, timeout=PAGE_LOAD_TIMEOUT_MS)

            if not is_logged_in(page):
                if has_session:
                    log.warning("Saved session has expired. Re-run with --setup to log in again.")
                    sys.exit(1)
                if not EMAIL or not PASSWORD:
                    log.error(
                        "Not logged in. Either:\n"
                        "  • Run once with --setup to log in via Google/SSO, or\n"
                        "  • Set PLAUD_EMAIL and PLAUD_PASSWORD in your .env file."
                    )
                    sys.exit(1)
                login_with_credentials(page)

            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            cards = get_recording_cards(page)
            if not cards:
                log.warning("No recordings found. Check that you are logged in and have recordings.")
                return

            total = len(cards)
            succeeded = 0
            failed = 0

            for i, card in enumerate(cards):
                ok = ensure_transcript_and_export(page, i, card)
                if ok:
                    succeeded += 1
                else:
                    failed += 1
                time.sleep(1)

            log.info("Done. %d/%d transcripts exported to '%s'. %d failed/skipped.",
                     succeeded, total, EXPORT_DIR, failed)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
