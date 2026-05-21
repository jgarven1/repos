"""
Paylocity Recruiting Exporter
Downloads Application PDF + Resume for every applicant on a selected job posting.

Usage:
    python main.py

Prerequisites:
    1. cp .env.example .env  and fill in your credentials
    2. pip install -r requirements.txt
    3. playwright install chromium
"""

from playwright.sync_api import sync_playwright

import auth
import recruiter


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        auth.login(page)

        postings = recruiter.get_job_postings(page)
        job = recruiter.select_job_interactively(postings)

        print(f"\nProcessing: {job['title']}")
        job["element"].click()

        applicants = recruiter.get_applicants(page)
        print(f"Found {len(applicants)} applicant(s).\n")

        for i, applicant in enumerate(applicants, 1):
            print(f"[{i}/{len(applicants)}] {applicant['name']}")
            recruiter.download_applicant_files(page, applicant, job["title"])

        browser.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
