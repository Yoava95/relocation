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
# ------------------------------------------------------------------
#  EXTRA SOURCES  (Indeed, Otta, LinkedIn quick scrape)
# ------------------------------------------------------------------
from bs4 import BeautifulSoup
import requests, re, html
from urllib.parse import quote_plus
import time, re

RELOCATION_PATTERNS = re.compile(
    r"(relocation|visa\s+sponsorship|work\s*permit|moving\s+costs|moving\s+assistance|relocation\s+assistance|work-visa)",
    re.I,
)

def page_mentions_relocation(url: str, timeout: int = 12) -> bool:
    """
    Downloads the job detail page and returns True if any relocation-related
    phrase is found. Returns False on HTTP errors/timeouts.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return bool(RELOCATION_PATTERNS.search(r.text))
    except Exception:
        return False

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_indeed(keyword: str):
    """Simple Indeed query with 'relocation' filter in the text."""
    url = f"https://www.indeed.com/jobs?q={quote_plus(keyword)}+relocation&l="
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for card in soup.select("a.tapItem"):
        title = card.select_one("h2").get_text(" ", strip=True)
        if "relocation" not in title.lower():
            continue
        company = card.select_one(".companyName").get_text(strip=True)
        loc = card.select_one(".companyLocation").get_text(strip=True)
        link = "https://www.indeed.com" + card["href"]
        rows.append(
            {"title": html.unescape(title),
             "company": company,
             "location": loc,
             "link": link,
             "date": date.today().isoformat()}
        )
    return rows

def scrape_otta(keyword: str):
    """Otta search (public landing page)."""
    url = f"https://app.otta.com/jobs?query={quote_plus(keyword)}&years=5&relocation=true"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for card in soup.select("a.JobCard"):
        title = card.select_one("h2").get_text(" ", strip=True)
        company = card.select_one("h3").get_text(" ", strip=True)
        loc = "Relocation"
        link = "https://otta.com" + card["href"]
        rows.append(
            {"title": title,
             "company": company,
             "location": loc,
             "link": link,
             "date": date.today().isoformat()}
        )
    return rows

def scrape_linkedin(keyword: str):
    """LinkedIn public search page – keep titles that literally contain 'relocation'."""
    url = ( "https://www.linkedin.com/jobs/search/?keywords="
            f"{quote_plus(keyword)}%20relocation&location=&f_WT=2" )
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for li in soup.select("li.jobs-search-results__list-item"):
        a = li.select_one("a.base-card__full-link")
        if not a:
            continue
        title = a.select_one("h3").get_text(" ", strip=True)
        if "relocation" not in title.lower():
            continue
        company = a.select_one("h4").get_text(" ", strip=True)
        loc = a.select_one("span.job-search-card__location").get_text(" ", strip=True)
        link = a["href"].split("?")[0]
        rows.append(
            {"title": title,
             "company": company,
             "location": loc,
             "link": link,
             "date": date.today().isoformat()}
        )
    return rows

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

# Separate headers for Relocate.me requests so that other scrapers keep
# the more realistic browser headers defined above.
RELOCATE_HEADERS = {
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
    r = requests.get(url, headers=RELOCATE_HEADERS, timeout=30)
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

def _keep(job, seen_set):
    if job["link"] in seen_set:
        return False
        # 1) Title passes your fuzzy allow-list
    # 2) OR the detail page explicitly mentions relocation/visa
    if not (title_is_allowed(job["title"]) or page_mentions_relocation(job["link"])):
        return False
    seen_set.add(job["link"])
    return True

def search_jobs():
    """Collect and de-duplicate jobs across all keywords."""
    seen = set()
    jobs = []
    for kw in KEYWORDS:
                # -------------- Relocate.me --------------
        for job in scrape_page(quote_plus(kw)):
            if _keep(job, seen):
                jobs.append(job)
        time.sleep(1)   # be polite to the host


        # -------------- Indeed -------------------
        try:
            for job in scrape_indeed(kw):
                if _keep(job, seen):
                    jobs.append(job)
        except Exception as e:
            print("WARN: Indeed failed for", kw, "→", e)


        # -------------- Otta ---------------------
        for job in scrape_otta(kw):
            if _keep(job, seen):
                jobs.append(job)
        time.sleep(1)   # be polite to the host


        # -------------- LinkedIn -----------------
        for job in scrape_linkedin(kw):
            if _keep(job, seen):
                jobs.append(job)

    return jobs


if __name__ == "__main__":
    from pprint import pprint

    pprint(search_jobs()[:10])
