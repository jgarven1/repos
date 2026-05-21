import re
from pathlib import Path
from playwright.sync_api import Page, Download

import config


def sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def _wait_for_table(page: Page) -> None:
    # talent.paylocity.com never reaches networkidle — wait for load then the table element
    page.wait_for_load_state("load")
    page.wait_for_selector("table tbody tr", state="visible", timeout=20000)


def get_job_postings(page: Page) -> list[dict]:
    page.goto(config.TALENT_URL)
    _wait_for_table(page)

    # Target only the 4th td (Title column) to avoid picking up "New" count links
    postings = page.evaluate("""() => {
        const links = document.querySelectorAll('table tbody tr td:nth-child(4) a');
        return Array.from(links).map(a => ({
            title: a.innerText.trim(),
            href: a.getAttribute('href') || ''
        })).filter(item => item.title && item.href);
    }""")

    return [
        {
            "title": p["title"],
            "url": p["href"] if p["href"].startswith("http") else f"https://talent.paylocity.com{p['href']}",
        }
        for p in postings
    ]


def select_job_interactively(postings: list[dict]) -> dict:
    if not postings:
        raise RuntimeError("No job postings found — check selectors in get_job_postings().")

    print("\nAvailable job postings:")
    for i, job in enumerate(postings):
        print(f"  [{i + 1}] {job['title']}")

    while True:
        choice = input("\nEnter the number of the posting to process: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(postings):
            return postings[int(choice) - 1]
        print("Invalid choice, try again.")


def get_applicants(page: Page) -> list[dict]:
    _wait_for_table(page)

    applicants = page.evaluate("""() => {
        const rows = document.querySelectorAll('table tbody tr');
        return Array.from(rows).map(row => {
            const link = row.querySelector('td a');
            return link ? { name: link.innerText.trim(), href: link.getAttribute('href') || '' } : null;
        }).filter(Boolean).filter(a => a.name && a.href);
    }""")

    return [
        {
            "name": a["name"],
            "url": a["href"] if a["href"].startswith("http") else f"https://talent.paylocity.com{a['href']}",
        }
        for a in applicants
    ]


def download_applicant_files(page: Page, applicant: dict, job_title: str) -> None:
    name = sanitize(applicant["name"])
    job = sanitize(job_title)
    dest = Path(config.OUTPUT_DIR) / job / name
    dest.mkdir(parents=True, exist_ok=True)

    page.goto(applicant["url"])
    page.wait_for_load_state("load")

    _download_file(page, dest, "application.pdf", label="Application PDF",
                   trigger_selector='a:has-text("Application"), button:has-text("Application PDF"), [data-testid*="application"]')

    _download_file(page, dest, "resume.pdf", label="Resume",
                   trigger_selector='a:has-text("Resume"), button:has-text("Resume"), [data-testid*="resume"]')


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
