"""GSMArena spec-page fetcher and parser.

GSMArena spec pages render a `<div id="specs-list">` containing one `<table>`
per section (Network, Launch, Body, Display, Platform, Memory, Main Camera,
Selfie camera, ...). Each row is `<td class="ttl">label</td><td class="nfo"
data-spec="key">value</td>`. Most (not all) value cells carry a stable
machine-readable `data-spec` attribute, which is far more robust to key off
than the human-readable label text.
"""

from __future__ import annotations

import random
import re
import time

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


class ScraperError(Exception):
    pass


def fetch_page(url: str, max_retries: int = 3, delay: float = 2.0) -> str:
    """Fetch a page politely: real User-Agent, small randomized delay after
    success, exponential-ish backoff and retry on non-200 (403 in particular)."""
    last_status = None
    for attempt in range(1, max_retries + 1):
        response = _session.get(url, timeout=15)
        last_status = response.status_code
        if response.status_code == 200:
            time.sleep(delay + random.uniform(0, 1.0))
            return response.text
        time.sleep(delay * attempt * 3)
    raise ScraperError(f"Failed to fetch {url} after {max_retries} attempts (last status: {last_status})")


def parse_spec_page(html: str) -> dict[str, str]:
    """Flat dict keyed by the `data-spec` attribute, e.g.
    {"displaysize": "6.1 inches, ...", "chipset": "...", "batdescription1": "Li-Ion 3900 mAh"}."""
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("div", id="specs-list")
    if root is None:
        raise ScraperError("Could not find #specs-list on page - GSMArena markup may have changed")
    return {
        td["data-spec"]: td.get_text(separator=" ", strip=True)
        for td in root.find_all("td", class_="nfo")
        if td.get("data-spec")
    }


def parse_full_sections(html: str) -> dict[str, dict[str, str]]:
    """Section -> {label: value} walk of the same markup, used for fields with
    no `data-spec` (e.g. "Charging") and to build the full raw spec text.

    Continuation rows (e.g. a second set of network bands) have an empty or
    '&nbsp;' label cell; their value is appended to the previous label instead
    of overwriting it, so no scraped data is silently dropped.
    """
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("div", id="specs-list")
    if root is None:
        raise ScraperError("Could not find #specs-list on page - GSMArena markup may have changed")

    sections: dict[str, dict[str, str]] = {}
    for table in root.find_all("table"):
        header = table.find("th")
        section = header.get_text(strip=True) if header else "General"
        sections.setdefault(section, {})
        last_label = None
        for row in table.find_all("tr"):
            ttl = row.find("td", class_="ttl")
            nfo = row.find("td", class_="nfo")
            if ttl is None or nfo is None:
                continue
            label = ttl.get_text(strip=True)
            value = nfo.get_text(separator=" ", strip=True)
            if label:
                sections[section][label] = value
                last_label = label
            elif last_label:
                sections[section][last_label] += " | " + value
    return sections


def flatten_to_text(sections: dict[str, dict[str, str]]) -> str:
    lines = []
    for section, kv in sections.items():
        for label, value in kv.items():
            lines.append(f"{section} - {label}: {value}")
    return "\n".join(lines)


def _first_number(pattern: str, text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


def extract_battery_and_price_fields(sections: dict[str, dict[str, str]]) -> dict:
    """Extract test-based battery life and the unmodified multi-currency price.

    Capacity and real-world endurance are intentionally separate: a larger
    battery does not automatically mean longer battery life.
    """
    tests = sections.get("Our Tests", {})
    active_use_text = tests.get("Battery", "")
    old_endurance_text = tests.get("Battery (old)", "")
    active_match = re.search(r"(\d+):(\d+)h", active_use_text)
    endurance_match = re.search(r"(\d+)h", old_endurance_text)

    active_use_hours = None
    if active_match:
        active_use_hours = int(active_match.group(1)) + int(active_match.group(2)) / 60

    return {
        "battery_active_use_hours": active_use_hours,
        "battery_endurance_hours": int(endurance_match.group(1)) if endurance_match else None,
        "price_summary": sections.get("Misc", {}).get("Price") or None,
    }


def map_to_structured_columns(flat: dict[str, str], sections: dict[str, dict[str, str]]) -> dict:
    """Extract the queryable Specification columns from the parsed spec data."""
    memory_match = re.search(r"(\d+)\s*GB\s+(\d+)\s*GB\s*RAM", flat.get("internalmemory", ""))
    storage_gb = int(memory_match.group(1)) if memory_match else None
    ram_gb = int(memory_match.group(2)) if memory_match else None

    charging_text = sections.get("Battery", {}).get("Charging", "")
    charging_match = re.search(r"(\d+)\s*W", charging_text)

    year_match = re.search(r"(\d{4})", flat.get("year", ""))

    price_match = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", flat.get("price", ""))

    structured = {
        "display_size_in": _first_number(r"([\d.]+)\s*inches", flat.get("displaysize")),
        "display_type": flat.get("displaytype"),
        "display_resolution": flat.get("displayresolution"),
        "chipset": flat.get("chipset"),
        "cpu": flat.get("cpu"),
        "gpu": flat.get("gpu"),
        "os": flat.get("os"),
        "ram_gb": ram_gb,
        "storage_gb": storage_gb,
        "rear_camera_mp": _first_number(r"(\d+(?:\.\d+)?)\s*MP", flat.get("cam1modules")),
        "rear_camera_summary": flat.get("cam1modules"),
        "front_camera_mp": _first_number(r"(\d+(?:\.\d+)?)\s*MP", flat.get("cam2modules")),
        "battery_capacity_mah": (
            int(_first_number(r"(\d+)\s*mAh", flat.get("batdescription1")))
            if _first_number(r"(\d+)\s*mAh", flat.get("batdescription1")) is not None
            else None
        ),
        "charging_speed_w": int(charging_match.group(1)) if charging_match else None,
        "body_weight_g": _first_number(r"([\d.]+)\s*g\b", flat.get("weight")),
        "price_usd": float(price_match.group(1).replace(",", "")) if price_match else None,
    }
    structured.update(extract_battery_and_price_fields(sections))
    return structured, (int(year_match.group(1)) if year_match else None)


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = slug.replace("+", "_plus")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return re.sub(r"_+", "_", slug).strip("_")
