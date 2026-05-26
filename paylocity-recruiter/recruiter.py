"""
recruiter.py — Navigate Paylocity Recruiting, iterate applicants, download PDFs.

NOTE: CSS selectors below are best-guess placeholders.
      Run the script, open DevTools (F12) on each page, and inspect the actual
      HTML so the selectors can be tuned to match Paylocity's real structure.
"""
import re
import time
from pathlib import Path
from playwright.sync_api import Page
from config import OUTPUT_DIR

RECRUITING_URL = "https://access.paylocity.com/recruiting"


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe_name(text: str) -> str:
    """Strip characters that are invalid in folder/file names."""
    return re.sub(r'[\\/*?:"<>|]', "_", text).strip()


def _make_applicant_dir(job_title: str, applicant_name: str) -> Path:
    folder = OUTPUT_DIR / _safe_name(job_title) / _safe_name(applicant_name)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ── job listing ───────────────────────────────────────────────────────────────

def get_job_postings(page: Page) -> list[dict]:
    """
    Navigate to the Recruiting module and return a list of open job postings.
    Each item: {"title": str, "element": Locator}

    ⚠ Selector to tune: the rows/cards that represent each job posting.
    """
    print("→ Loading Recruiting module…")
    page.goto(RECRUITING_URL, wait_until="networkidle")
    time.sleep(2)  # let any lazy-loaded content settle

    # TODO: replace with the real selector after inspecting DevTools
    job_rows = page.locator("tr.job-row, div.job-card, [data-testid='job-posting']")
    count = job_rows.count()

    jobs = []
    for i in range(count):
        row = job_rows.nth(i)
        title = row.inner_text().strip().splitlines()[0]  # first line as title
        jobs.append({"title": title, "index": i, "locator": row})

    return jobs


def choose_job(jobs: list[dict]) -> dict:
    """Print a numbered menu and return the chosen job dict."""
    print("\nOpen job postings:")
    for i, job in enumerate(jobs, 1):
        print(f"  {i}. {job['title']}")
    print()

    while True:
        raw = input("Enter the number of the job to process: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(jobs):
            return jobs[int(raw) - 1]
        print(f"  Please enter a number between 1 and {len(jobs)}.")


# ── applicant iteration ───────────────────────────────────────────────────────

def get_applicants(page: Page, job: dict) -> list[dict]:
    """
    Click into a job posting and return a list of applicants.
    Each item: {"name": str, "locator": Locator}

    ⚠ Selectors to tune after DevTools inspection.
    """
    print(f"\n→ Opening job posting: {job['title']}")
    job["locator"].click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # TODO: replace with real selector for applicant rows
    applicant_rows = page.locator(
        "tr.applicant-row, div.applicant-card, [data-testid='applicant-row']"
    )
    count = applicant_rows.count()
    print(f"  Found {count} applicant(s).")

    applicants = []
    for i in range(count):
        row = applicant_rows.nth(i)
        name = row.inner_text().strip().splitlines()[0]
        applicants.append({"name": name, "index": i})

    return applicants


# ── PDF download ──────────────────────────────────────────────────────────────

def download_applicant_pdfs(page: Page, job_title: str, applicants: list[dict]) -> None:
    """
    For each applicant: open their submission, download Application PDF + Resume.

    ⚠ Selectors and download triggers to tune after DevTools inspection.
    """
    for applicant in applicants:
        name = applicant["name"]
        print(f"\n  ── {name}")
        dest = _make_applicant_dir(job_title, name)

        # Re-query applicant rows each time (DOM may refresh after navigation)
        applicant_rows = page.locator(
            "tr.applicant-row, div.applicant-card, [data-testid='applicant-row']"
        )
        row = applicant_rows.nth(applicant["index"])
        row.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # ── Application PDF ──────────────────────────────────────────────────
        try:
            with page.expect_download(timeout=30_000) as dl_info:
                # TODO: replace with the real selector for "Export Application" button
                page.locator(
                    "button:has-text('Export Application'), "
                    "a:has-text('Application PDF'), "
                    "[data-testid='export-application']"
                ).first.click()
            download = dl_info.value
            save_path = dest / f"{_safe_name(name)}_Application.pdf"
            download.save_as(save_path)
            print(f"    ✔ Application PDF → {save_path}")
        except Exception as exc:
            print(f"    ✘ Application PDF failed: {exc}")

        # ── Resume PDF ───────────────────────────────────────────────────────
        try:
            with page.expect_download(timeout=30_000) as dl_info:
                # TODO: replace with the real selector for "Download Resume" button
                page.locator(
                    "button:has-text('Download Resume'), "
                    "a:has-text('Resume'), "
                    "[data-testid='download-resume']"
                ).first.click()
            download = dl_info.value
            save_path = dest / f"{_safe_name(name)}_Resume.pdf"
            download.save_as(save_path)
            print(f"    ✔ Resume        → {save_path}")
        except Exception as exc:
            print(f"    ✘ Resume failed: {exc}")

        # Navigate back to the applicant list
        page.go_back()
        page.wait_for_load_state("networkidle")
        time.sleep(1)
