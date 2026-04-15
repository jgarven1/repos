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
ALL_FILES_URL = f"{PLAUD_URL}/file-list?categoryId=allFiles"
TRANSCRIPT_GENERATION_TIMEOUT_MS = 5 * 60 * 1000   # 5 minutes per recording
PAGE_LOAD_TIMEOUT_MS = 30_000
SCROLL_PAUSE_MS = 400

POPUP_DISMISS_SELECTORS = [
    "button:has-text('Maybe later')",
    "button:has-text('Close')",
    "button:has-text('Got it')",
    "button:has-text('OK')",
    "[aria-label='Close']",
    "[data-testid='dialog-close-btn']",
    ".modal-close",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def dismiss_popups(page):
    """Close any modal/dialog overlays that could block tab clicks."""
    for sel in POPUP_DISMISS_SELECTORS:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=800):
                el.click()
                page.wait_for_timeout(300)
        except PWTimeoutError:
            pass


def is_logged_in(page):
    try:
        page.wait_for_selector(
            "li.file-list-item, [data-testid='nav-sidebar-all-files-item']",
            timeout=8_000,
        )
        return True
    except PWTimeoutError:
        return False


# ---------------------------------------------------------------------------
# Setup mode — one-time manual login to save a session
# ---------------------------------------------------------------------------

def run_setup(pw):
    log.info("=== SETUP MODE ===")
    log.info("A browser window will open. Log in to Plaud however you normally do.")
    log.info("When fully logged in and your recordings are visible, come back here and press Enter.")

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
        "li.file-list-item, [data-testid='nav-sidebar-all-files-item']",
        timeout=PAGE_LOAD_TIMEOUT_MS,
    )
    log.info("Login successful")


# ---------------------------------------------------------------------------
# Collect all file IDs via virtual-scroller
# ---------------------------------------------------------------------------

def collect_all_file_ids(page):
    """
    Navigate to the All Files page and scroll through the virtual list
    to collect every file ID, title, and whether transcript is already generated.
    Returns a list of dicts: [{id, title, has_transcript}]
    """
    log.info("Loading All Files list...")
    page.goto(ALL_FILES_URL, timeout=PAGE_LOAD_TIMEOUT_MS)
    page.wait_for_selector("li.file-list-item", timeout=PAGE_LOAD_TIMEOUT_MS)
    page.wait_for_timeout(500)

    files = {}  # file_id -> {title, has_transcript}

    while True:
        prev_count = len(files)

        for item in page.query_selector_all("li.file-list-item[data-file-id]"):
            file_id = item.get_attribute("data-file-id")
            if not file_id or file_id in files:
                continue
            title_el = item.query_selector(".file-list-item__filename")
            title = title_el.inner_text().strip() if title_el else file_id
            status_el = item.query_selector(".status-text")
            has_transcript = bool(
                status_el and "generated" in status_el.inner_text().lower()
            )
            files[file_id] = {"title": title, "has_transcript": has_transcript}

        if len(files) == prev_count:
            # No new items — try scrolling further; if already at bottom, stop
            scrolled = page.evaluate("""
                (() => {
                    const s = document.querySelector('.vue-recycle-scroller');
                    if (!s) return false;
                    const before = s.scrollTop;
                    s.scrollBy(0, 800);
                    return s.scrollTop !== before;
                })()
            """)
            if not scrolled:
                break
        else:
            page.evaluate(
                "document.querySelector('.vue-recycle-scroller').scrollBy(0, 800)"
            )

        page.wait_for_timeout(SCROLL_PAUSE_MS)

    log.info("Collected %d recording(s)", len(files))
    return [{"id": fid, **data} for fid, data in files.items()]


# ---------------------------------------------------------------------------
# URL pattern discovery
# ---------------------------------------------------------------------------

def discover_url_pattern(page, file_id):
    """
    Click the first file item and check whether the resulting URL contains
    the file ID. If so, return a format-string pattern for direct navigation.
    """
    page.goto(ALL_FILES_URL, timeout=PAGE_LOAD_TIMEOUT_MS)
    page.wait_for_selector("li.file-list-item", timeout=PAGE_LOAD_TIMEOUT_MS)

    item = page.query_selector(f"li.file-list-item[data-file-id='{file_id}']")
    if not item:
        return None

    item.click()
    page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)

    current_url = page.url
    if file_id in current_url:
        pattern = current_url.replace(file_id, "{file_id}")
        log.info("File URL pattern: %s", pattern)
        return pattern

    log.info("File ID not in URL — will scroll + click for each file")
    return None


# ---------------------------------------------------------------------------
# Navigate to a single file
# ---------------------------------------------------------------------------

def navigate_to_file(page, file_id, url_pattern):
    """Open a file's detail page. Returns True on success."""
    if url_pattern:
        page.goto(url_pattern.format(file_id=file_id), timeout=PAGE_LOAD_TIMEOUT_MS)
        page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
        return True

    # No URL pattern — scroll through the list and click the item
    page.goto(ALL_FILES_URL, timeout=PAGE_LOAD_TIMEOUT_MS)
    page.wait_for_selector("li.file-list-item", timeout=PAGE_LOAD_TIMEOUT_MS)

    for _ in range(80):
        item = page.query_selector(f"li.file-list-item[data-file-id='{file_id}']")
        if item:
            item.click()
            page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
            return True
        page.evaluate(
            "document.querySelector('.vue-recycle-scroller').scrollBy(0, 500)"
        )
        page.wait_for_timeout(300)

    return False


# ---------------------------------------------------------------------------
# Transcript generation
# ---------------------------------------------------------------------------

def ensure_transcript_generated(page, title, index, total):
    """On the file detail page, generate transcript if not already done."""
    dismiss_popups(page)

    # Click the Transcript tab (data-testid="tab-transcript-item")
    try:
        page.click("[data-testid='tab-transcript-item']", timeout=8_000)
        page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
        page.wait_for_timeout(1_000)
    except PWTimeoutError:
        log.warning("[%d/%d] Could not click Transcript tab for '%s'", index + 1, total, title)

    # Look for a Generate/Transcribe button
    generate_btn = page.locator(
        "button:has-text('Generate'), button:has-text('Transcribe'), "
        "button:has-text('Create Transcript')"
    ).first

    try:
        btn_visible = generate_btn.is_visible(timeout=3_000)
    except PWTimeoutError:
        btn_visible = False

    if btn_visible:
        log.info("[%d/%d] Generating transcript for '%s'...", index + 1, total, title)
        generate_btn.click()
        try:
            page.wait_for_selector(
                "[class*='transcript-content'], [class*='transcriptContent'], "
                "[class*='transcript-item'], [class*='transcriptItem'], "
                "[class*='utterance'], [class*='segment']",
                timeout=TRANSCRIPT_GENERATION_TIMEOUT_MS,
            )
            log.info("[%d/%d] Transcript ready", index + 1, total)
        except PWTimeoutError:
            log.error(
                "[%d/%d] Transcript generation timed out for '%s'", index + 1, total, title
            )
            return False
    else:
        log.info("[%d/%d] Transcript already exists for '%s'", index + 1, total, title)

    return True


# ---------------------------------------------------------------------------
# Transcript export
# ---------------------------------------------------------------------------

def export_transcript(page, label, index, total):
    """Export transcript via download button, or scrape visible text."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Try the share/export toolbar button (data-testid="share-button") ---
    share_btn = page.locator("[data-testid='share-button']").first
    try:
        btn_visible = share_btn.is_visible(timeout=3_000)
    except PWTimeoutError:
        btn_visible = False

    if btn_visible:
        try:
            with page.expect_download(timeout=30_000) as dl_info:
                share_btn.click()
                page.wait_for_timeout(500)
                # Look for a Download / Export option in the dropdown
                for opt_sel in [
                    f"li:has-text('{TRANSCRIPT_FORMAT.upper()}')",
                    "li:has-text('Download')",
                    "li:has-text('Export')",
                    f"[data-testid*='export']:has-text('{TRANSCRIPT_FORMAT.upper()}')",
                    "[data-testid*='download']",
                ]:
                    try:
                        opt = page.locator(opt_sel).first
                        if opt.is_visible(timeout=2_000):
                            opt.click()
                            break
                    except PWTimeoutError:
                        pass

            dl = dl_info.value
            ext = (
                dl.suggested_filename.rsplit(".", 1)[-1]
                if "." in dl.suggested_filename
                else TRANSCRIPT_FORMAT
            )
            dest = EXPORT_DIR / f"{label}.{ext}"
            dl.save_as(dest)
            log.info("[%d/%d] Saved (download) → %s", index + 1, total, dest)
            return True
        except PWTimeoutError:
            log.warning("[%d/%d] Download timed out; falling back to text scrape", index + 1, total)
            # Close any open dropdown before scraping
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass

    # --- Fallback: scrape visible transcript text ---
    log.info("[%d/%d] Scraping transcript text for '%s'", index + 1, total, label)

    # Try progressively broader selectors for the transcript content
    TRANSCRIPT_CONTENT_SELECTORS = [
        # Plaud-specific data-testid patterns
        "[data-testid*='transcript-item']",
        "[data-testid*='utterance']",
        "[data-testid*='sentence']",
        # class-name patterns
        "[class*='transcript-item']",
        "[class*='transcriptItem']",
        "[class*='utterance-item']",
        "[class*='utteranceItem']",
        "[class*='sentence-item']",
        "[class*='transcript-content'] > *",
        "[class*='transcriptContent'] > *",
        "[class*='transcript-row']",
    ]

    blocks = []
    for sel in TRANSCRIPT_CONTENT_SELECTORS:
        blocks = page.query_selector_all(sel)
        if blocks:
            break

    if blocks:
        text = "\n".join(b.inner_text().strip() for b in blocks if b.inner_text().strip())
    else:
        # Last resort: grab the whole transcript panel
        panel = page.query_selector(
            "[class*='transcript']:not([class*='tab'])"
        )
        text = panel.inner_text() if panel else ""

    if not text.strip():
        log.warning("[%d/%d] Could not extract text for '%s'", index + 1, total, label)
        return False

    dest = EXPORT_DIR / f"{label}.txt"
    dest.write_text(text, encoding="utf-8")
    log.info("[%d/%d] Saved (scraped) → %s", index + 1, total, dest)
    return True


# ---------------------------------------------------------------------------
# Process one file
# ---------------------------------------------------------------------------

def process_file(page, file_info, index, total, url_pattern):
    title = safe_filename(file_info["title"]) or f"recording_{index + 1}"
    file_id = file_info["id"]

    log.info("[%d/%d] '%s'", index + 1, total, title)

    try:
        if not navigate_to_file(page, file_id, url_pattern):
            log.warning("[%d/%d] Could not navigate to '%s', skipping", index + 1, total, title)
            return False

        if not ensure_transcript_generated(page, title, index, total):
            return False

        return export_transcript(page, title, index, total)

    except PWTimeoutError as exc:
        log.error("[%d/%d] Timeout on '%s': %s", index + 1, total, title, exc)
        return False
    except Exception as exc:
        log.error("[%d/%d] Error on '%s': %s", index + 1, total, title, exc)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    setup_mode = "--setup" in sys.argv
    debug_mode = "--debug" in sys.argv

    with sync_playwright() as pw:
        if setup_mode:
            run_setup(pw)
            return

        has_session = SESSION_FILE.exists()
        browser = pw.chromium.launch(headless=False if debug_mode else HEADLESS)

        if has_session:
            log.info("Loading saved session from '%s'", SESSION_FILE)
            context = browser.new_context(
                storage_state=str(SESSION_FILE), accept_downloads=True
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

            if debug_mode:
                debug_dir = pathlib.Path("debug")
                debug_dir.mkdir(exist_ok=True)

                # Navigate directly to a known file and snapshot the Transcript tab
                file_url = "https://web.plaud.ai/file/8b0e55e6c07fa8e803362e4563124ff2"
                log.info("Navigating to file detail page...")
                page.goto(file_url, timeout=PAGE_LOAD_TIMEOUT_MS)
                page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
                page.wait_for_timeout(2000)

                # Dismiss any popups
                for dismiss_sel in [
                    "button:has-text('Maybe later')",
                    "button:has-text('Close')",
                    "[aria-label='Close']",
                    "button:has-text('Accept')",
                ]:
                    try:
                        page.click(dismiss_sel, timeout=2000)
                    except PWTimeoutError:
                        pass

                # Click the Transcript tab
                try:
                    page.click("[data-testid='tab-transcript-item']", timeout=5_000)
                    page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
                    page.wait_for_timeout(1_500)
                    log.info("Transcript tab clicked successfully")
                except PWTimeoutError:
                    log.warning("Could not click Transcript tab with data-testid selector")

                page.screenshot(path=str(debug_dir / "file.png"), full_page=True)
                (debug_dir / "file.html").write_text(page.content(), encoding="utf-8")
                log.info("File detail snapshot saved to debug/file.png and debug/file.html")
                return

            EXPORT_DIR.mkdir(parents=True, exist_ok=True)

            files = collect_all_file_ids(page)
            if not files:
                log.warning("No files found.")
                return

            url_pattern = discover_url_pattern(page, files[0]["id"])

            total = len(files)
            succeeded = 0
            failed = 0

            for i, file_info in enumerate(files):
                ok = process_file(page, file_info, i, total, url_pattern)
                if ok:
                    succeeded += 1
                else:
                    failed += 1
                time.sleep(0.5)

            log.info(
                "Done. %d/%d exported to '%s'. %d failed/skipped.",
                succeeded, total, EXPORT_DIR, failed,
            )

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
