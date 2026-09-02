"""Preflight check: confirm every URL in app.scraper.phone_urls.PHONE_URLS
still resolves to the expected phone before running a full scrape.

Usage:
    python -m scripts.verify_gsmarena_urls
"""

from app.scraper.gsmarena_scraper import USER_AGENT
from app.scraper.phone_urls import PHONE_URLS

import requests
from bs4 import BeautifulSoup


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    mismatches = []
    for expected_name, url in PHONE_URLS.items():
        response = session.get(url, timeout=15)
        if response.status_code != 200:
            print(f"[HTTP {response.status_code}] {expected_name}: {url}")
            mismatches.append(expected_name)
            continue

        soup = BeautifulSoup(response.text, "lxml")
        title_tag = soup.find("h1", class_="specs-phone-name-title")
        actual_name = title_tag.get_text(strip=True) if title_tag else None

        status = "OK" if actual_name and expected_name.split(" 5G")[0] in actual_name else "MISMATCH"
        print(f"[{status}] expected='{expected_name}' actual='{actual_name}' url={url}")
        if status == "MISMATCH":
            mismatches.append(expected_name)

    if mismatches:
        print(f"\n{len(mismatches)} URL(s) need fixing: {', '.join(mismatches)}")
    else:
        print(f"\nAll {len(PHONE_URLS)} URLs verified OK.")


if __name__ == "__main__":
    main()
