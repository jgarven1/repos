import os
import re
import time
from pathlib import Path
from playwright.sync_api import Page, Download

import config


def sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def get_job_postings(page: Page) -> list[dict]:
    """Navigate to the Recruiting module and return a list of active job postings."""
    page.goto(config.TALENT_URL)
    page.wait_for_load_state("networkidle")

    postings = []
    # Collect job posting rows — selectors will need tuning after inspecting the live page
    rows = page.query_selector_all("table tbody tr, [data-testid*='job'], .job-posting-row")
    for row in rows:
        title_el = row.query_selector("td:first-child, .job-title, [data-testid*='title']")
        if title_el:
            postings.append({
                "title": title_el.inner_text().strip(),
                "element": row,
            })
    return postings


def select_job_interactively(postings: list[dict]) -> dict:
    """Print available postings and let the user pick one."""
    if not postings:
        raise RuntimeError("No job postings found. Check the selector in get_job_postings().")

    print("\nAvailable job postings:")
    for i, job in enumerate(postings):
        print(f"  [{i + 1}] {job['title']}")

    while True:
        choice = input("\nEnter the number of the posting to process: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(postings):
            return postings[int(choice) - 1]
        print("Invalid choice, try again.")


def get_applicants(page: Page) -> list[dict]:
    """Return applicant entries visible on the current job posting page."""
    page.wait_for_load_state("networkidle")
    applicants = []
    rows = page.query_selector_all("table tbody tr, .applicant-row, [data-testid*='applicant']")
    for row in rows:
        name_el = row.query_selector("td:first-child, .applicant-name, [data-testid*='name']")
        if name_el:
            applicants.append({
                "name": name_el.inner_text().strip(),
                "element": row,
            })
    return applicants


def download_applicant_files(page: Page, applicant: dict, job_title: str) -> None:
    """Open an applicant's submission and download their Application PDF and Resume."""
    name = sanitize(applicant["name"])
    job = sanitize(job_title)
    dest = Path(config.OUTPUT_DIR) / job / name
    dest.mkdir(parents=True, exist_ok=True)

    # Click into the applicant's detail view
    applicant["element"].click()
    page.wait_for_load_state("networkidle")

    _download_file(page, dest, "application.pdf", label="Application PDF",
                   trigger_selector='a:has-text("Application"), button:has-text("Application PDF"), [data-testid*="application"]')

    _download_file(page, dest, "resume.pdf", label="Resume",
                   trigger_selector='a:has-text("Resume"), button:has-text("Resume"), [data-testid*="resume"]')

    # Go back to the applicant list
    page.go_back()
    page.wait_for_load_state("networkidle")


def _download_file(page: Page, dest: Path, filename: str, label: str, trigger_selector: str) -> None:
    trigger = page.query_selector(trigger_selector)
    if not trigger:
        print(f"  [WARN] {label} link not found for {dest.name} — skipping.")
        return

    with page.expect_download() as dl_info:
        trigger.click()
    download: Download = dl_info.value
    out_path = dest / filename
    download.save_as(out_path)
    print(f"  [OK] {label} → {out_path}")
