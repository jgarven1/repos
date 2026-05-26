"""
main.py — Entry point for Paylocity recruitment automation.

Usage:
    python main.py

Workflow:
    1. Opens Chromium (headed) and logs into Paylocity
    2. Pauses for you to complete MFA
    3. Lists open job postings — you pick one
    4. Iterates every applicant and saves Application PDF + Resume to:
       output/<Job Title>/<Applicant Name>/
"""
from playwright.sync_api import sync_playwright
from auth import login
from recruiter import get_job_postings, choose_job, get_applicants, download_applicant_pdfs
import config  # ensures .env is loaded and credentials are validated


def main():
    print("=" * 60)
    print("  Paylocity Recruitment Automation")
    print("=" * 60)
    print()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            # Step 1 — authenticate
            login(page)

            # Step 2 — pick a job posting
            jobs = get_job_postings(page)
            if not jobs:
                print("✘ No job postings found. Check the selector in recruiter.py.")
                return

            job = choose_job(jobs)

            # Step 3 — gather applicants
            applicants = get_applicants(page, job)
            if not applicants:
                print("✘ No applicants found for that posting. Check the selector in recruiter.py.")
                return

            # Step 4 — download PDFs
            download_applicant_pdfs(page, job["title"], applicants)

            print("\n" + "=" * 60)
            print(f"  Done! Files saved to: {config.OUTPUT_DIR / job['title']}")
            print("=" * 60)

        finally:
            input("\nPress Enter to close the browser… ")
            browser.close()


if __name__ == "__main__":
    main()
