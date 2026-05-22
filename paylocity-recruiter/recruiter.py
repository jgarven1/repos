"""
Navigate Paylocity Recruiting: list job postings, iterate applicants,
download Application PDF and Resume for each.

NOTE: CSS selectors are best-guess placeholders. Run the script, inspect
the Paylocity UI with DevTools, and update the selectors to match exactly.
"""

import pathlib
import re
import time

from playwright.sync_api import Page, TimeoutError as PWTimeoutError
import config


def safe_name(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", text).strip()


# ---------------------------------------------------------------------------
# Navigate to Recruiting
# ---------------------------------------------------------------------------

def go_to_recruiting(page: Page) -> None:
    """Navigate directly to the Paylocity Jobs Dashboard."""
    page.goto(config.JOBS_URL, timeout=config.PAGE_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=config.PAGE_TIMEOUT_MS)


# ---------------------------------------------------------------------------
# List job postings
# ---------------------------------------------------------------------------

def list_job_postings(page: Page) -> list[dict]:
    """
    Return a list of open job postings as:
      [{"title": str, "element": Locator}, ...]

    UPDATE the selector below to match the actual job row in Paylocity.
    """
    go_to_recruiting(page)

    # Placeholder selector — inspect the job list page and replace this
    job_rows = page.locator(
        ".job-posting-row, [data-testid='job-row'], tr.job-row"
    )
    try:
        job_rows.first.wait_for(timeout=config.PAGE_TIMEOUT_MS)
    except PWTimeoutError:
        raise RuntimeError(
            "No job postings found. Check the selector in recruiter.py:list_job_postings()."
        )

    jobs = []
    for i in range(job_rows.count()):
        row = job_rows.nth(i)
        title = row.inner_text().strip().splitlines()[0]
        jobs.append({"title": title, "index": i, "locator": row})

    return jobs


def select_job(page: Page) -> dict:
    """Print numbered job list, prompt user to pick one, return the chosen job."""
    jobs = list_job_postings(page)
    if not jobs:
        raise RuntimeError("No job postings found.")

    print("\nJob Postings:")
    for i, job in enumerate(jobs):
        print(f"  [{i + 1}] {job['title']}")

    while True:
        try:
            choice = int(input("\nEnter the number of the job to process: "))
            if 1 <= choice <= len(jobs):
                return jobs[choice - 1]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(jobs)}.")


# ---------------------------------------------------------------------------
# List applicants for a job
# ---------------------------------------------------------------------------

def list_applicants(page: Page, job: dict) -> list[dict]:
    """
    Click into the job posting and return a list of applicants as:
      [{"name": str, "locator": Locator}, ...]

    UPDATE the selectors below after inspecting the applicant table.
    """
    job["locator"].click()
    page.wait_for_load_state("networkidle", timeout=config.PAGE_TIMEOUT_MS)
    time.sleep(1)

    # Placeholder selector — inspect the applicant list and replace this
    rows = page.locator(
        ".applicant-row, [data-testid='applicant-row'], tr.applicant"
    )
    try:
        rows.first.wait_for(timeout=config.PAGE_TIMEOUT_MS)
    except PWTimeoutError:
        raise RuntimeError(
            "No applicants found. Check the selector in recruiter.py:list_applicants()."
        )

    applicants = []
    for i in range(rows.count()):
        row = rows.nth(i)
        name = row.inner_text().strip().splitlines()[0]
        applicants.append({"name": name, "index": i, "locator": row})

    return applicants


# ---------------------------------------------------------------------------
# Download Application PDF and Resume for one applicant
# ---------------------------------------------------------------------------

def download_applicant_files(page: Page, applicant: dict, job_title: str) -> None:
    """
    Open an applicant's submission and download:
      - Application PDF
      - Resume

    Files are saved to: output/<job_title>/<applicant_name>/

    UPDATE selectors after inspecting the applicant detail page.
    """
    out_dir = config.OUTPUT_DIR / safe_name(job_title) / safe_name(applicant["name"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Open applicant detail
    applicant["locator"].click()
    page.wait_for_load_state("networkidle", timeout=config.PAGE_TIMEOUT_MS)
    time.sleep(1)

    _download_application_pdf(page, out_dir)
    _download_resume(page, out_dir)

    # Go back to the applicant list
    page.go_back()
    page.wait_for_load_state("networkidle", timeout=config.PAGE_TIMEOUT_MS)


def _download_application_pdf(page: Page, out_dir: pathlib.Path) -> None:
    """
    Download the Application PDF from the applicant detail page.
    UPDATE the selector to match the actual button/link in Paylocity.
    """
    try:
        btn = page.locator(
            "button:has-text('Application'), a:has-text('Application PDF'), "
            "[data-testid='download-application']"
        ).first
        btn.wait_for(timeout=8_000)

        with page.expect_download(timeout=30_000) as dl_info:
            btn.click()

        dl = dl_info.value
        dest = out_dir / (dl.suggested_filename or "application.pdf")
        dl.save_as(dest)
        print(f"    ✓ Application → {dest.name}")

    except PWTimeoutError:
        print(f"    ✗ Application PDF not found — update selector in _download_application_pdf()")


def _download_resume(page: Page, out_dir: pathlib.Path) -> None:
    """
    Download the Resume from the applicant detail page.
    UPDATE the selector to match the actual button/link in Paylocity.
    """
    try:
        btn = page.locator(
            "button:has-text('Resume'), a:has-text('Resume'), "
            "[data-testid='download-resume']"
        ).first
        btn.wait_for(timeout=8_000)

        with page.expect_download(timeout=30_000) as dl_info:
            btn.click()

        dl = dl_info.value
        dest = out_dir / (dl.suggested_filename or "resume.pdf")
        dl.save_as(dest)
        print(f"    ✓ Resume     → {dest.name}")

    except PWTimeoutError:
        print(f"    ✗ Resume not found — update selector in _download_resume()")
