"""
Scrape relocation-friendly jobs from Relocate.me category pages
without any JS rendering.

Works with URLs like:
  https://relocate.me/international-jobs/product-manager
  https://relocate.me/international-jobs/senior-product-manager
"""

import re, time
from datetime import date
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
# ------------------------------------------------------------------
#  Fuzzy allow-list and block-list
# ------------------------------------------------------------------
import difflib

ALLOW_TITLES = [
    "product manager",
    "sr. product manager",
    "senior product manager",
    "staff product manager",
    "product manager ai",
    "ai product manager",
    "principal product manager",
    "product design lecturer",
    "product design professor",
    "industrial design lecturer",
    "industrial design professor",
    "product management lecturer",
    "product management professor",
]

BLOCK_KEYWORDS = [
    "engineer",
    "designer",
    "developer",
    "architect",
    "security",
    "machine learning",
    "data scientist",
]

def title_is_allowed(title: str, threshold: float = 0.7) -> bool:
    """
    True  ⇢ allowed title (fuzzy-matched) and no blocked keywords  
    False ⇢ everything else
    """
    t = title.lower()

    # Hard block first
    if any(b in t for b in BLOCK_KEYWORDS):
        return False

    # Fuzzy allow
    best = max(
        difflib.SequenceMatcher(None, t, allow).ratio()
        for allow in ALLOW_TITLES
    )
    return best >= threshold

HEADERS = {
    "User-Agent": "Mozilla/5.0 (reloc8-agent test)"
}

KEYWORDS = [
    "product-manager",
    "senior-product-manager",
    "staff-product-manager",
    "principal-product-manager",
    "innovation-manager",
    "design-lecturer",
    "design-school-lecturer",
]

ROOT = "https://relocate.me"
BASE = ROOT + "/international-jobs/{}"


def scrape_page(slug: str):
    url = BASE.format(slug)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Relocate.me's static HTML shows job links as <a> whose href ends with "-<digits>"
    link_re = re.compile(r"^/[a-z0-9\-]+/[a-z0-9\-]+/[a-z0-9\-]+/[a-z0-9\-]+-\d+$")

    rows = []
    for a in soup.find_all("a", href=link_re):
        link = ROOT + a["href"]
        title = a.get_text(strip=True)

        # Company line is two previous siblings that are NavigableStrings
        comp_node = a.find_previous(string=True)
        loc_node = comp_node.find_previous(string=True) if comp_node else ""
        company = comp_node.strip() if comp_node else ""
        location = loc_node.strip() if loc_node else ""

        rows.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "date": date.today().isoformat(),
            }
        )
    return rows


def search_jobs():
    """Collect and de-duplicate jobs across all keywords."""
    seen = set()
    jobs = []
    for kw in KEYWORDS:
    for job in scrape_page(quote_plus(kw)):
        if job["link"] in seen:
            continue
        if not title_is_allowed(job["title"]):
            continue  # skip unwanted titles
        seen.add(job["link"])
        jobs.append(job)


        time.sleep(1)  # polite delay
    return jobs


if __name__ == "__main__":
    from pprint import pprint

    pprint(search_jobs()[:10])
