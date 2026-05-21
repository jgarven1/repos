"""
Paylocity Recruitment Automation
---------------------------------
1. Opens Paylocity in a browser window
2. Logs in (pauses for MFA if needed)
3. Lets you pick a job posting from a numbered list
4. Iterates every applicant and downloads their Application PDF + Resume
   into output/<Job Title>/<Applicant Name>/
"""

from playwright.sync_api import sync_playwright
import auth
import recruiter
import config


def main():
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        # Use system Chrome if available so network/DNS settings match the OS
        try:
            browser = pw.chromium.launch(channel="chrome", headless=False)
        except Exception:
            browser = pw.chromium.launch(headless=False)

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(config.PAGE_TIMEOUT_MS)

        try:
            # Step 1: log in
            auth.login(page)

            # Step 2: pick a job posting
            job = recruiter.select_job(page)
            print(f"\nProcessing: {job['title']}\n")

            # Step 3: list applicants
            applicants = recruiter.list_applicants(page, job)
            total = len(applicants)
            print(f"Found {total} applicant(s).\n")

            # Step 4: download files for each applicant
            for i, applicant in enumerate(applicants):
                print(f"[{i + 1}/{total}] {applicant['name']}")
                try:
                    recruiter.download_applicant_files(page, applicant, job["title"])
                except Exception as exc:
                    print(f"    ✗ Error: {exc}")

            print(f"\nDone. Files saved to: {config.OUTPUT_DIR.resolve()}")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
