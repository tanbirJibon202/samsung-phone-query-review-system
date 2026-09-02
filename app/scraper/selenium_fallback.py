"""Fallback fetcher for if GSMArena ever starts blocking plain `requests`.

Not needed as of this writing (plain requests.get with a browser User-Agent
successfully returns spec pages), but kept as a documented escalation path per
the task's Selenium option. `run_scrape.py` only calls this after
`fetch_page`'s retries are exhausted.
"""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from app.scraper.gsmarena_scraper import USER_AGENT


def fetch_with_selenium(url: str, wait_seconds: float = 3.0) -> str:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(wait_seconds)
        return driver.page_source
    finally:
        driver.quit()
