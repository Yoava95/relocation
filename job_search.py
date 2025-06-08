# Local job search for product manager roles in Israel

import re, time, html
from datetime import date
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
import difflib
from bot_notify import send_message

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def notify_blocked(site: str):
    """Send a Telegram notification when a site blocks access."""
    try:
        send_message(f"the request was blocked {site.lower()}")
    except Exception as exc:  # pragma: no cover - notification failures are non-critical
        print("WARN: failed to notify Telegram →", exc)


ALLOW_TITLES = [
    "product manager",
    "staff product manager",
    "principal product manager",
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

KEYWORDS = [
    "product manager",
    "staff product manager",
    "principal product manager",
]


def title_is_allowed(title: str, threshold: float = 0.7) -> bool:
    """Check fuzzy title allow list and block keywords"""
    t = title.lower()
    if any(b in t for b in BLOCK_KEYWORDS):
        return False
    best = max(difflib.SequenceMatcher(None, t, allow).ratio() for allow in ALLOW_TITLES)
    return best >= threshold


def scrape_indeed(keyword: str):
    url = f"https://www.indeed.com/jobs?q={quote_plus(keyword)}&l=Israel"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for card in soup.select("a.tapItem"):
        title = card.select_one("h2").get_text(" ", strip=True)
        company = card.select_one(".companyName").get_text(strip=True)
        loc = card.select_one(".companyLocation").get_text(strip=True)
        if "israel" not in loc.lower():
            continue
        link = "https://www.indeed.com" + card["href"]
        rows.append({
            "title": html.unescape(title),
            "company": company,
            "location": loc,
            "link": link,
            "date": date.today().isoformat(),
        })
    return rows


def scrape_linkedin(keyword: str):
    url = (
        "https://www.linkedin.com/jobs/search/?keywords="
        f"{quote_plus(keyword)}&location=Israel"
    )
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for li in soup.select("li.jobs-search-results__list-item"):
        a = li.select_one("a.base-card__full-link")
        if not a:
            continue
        title = a.select_one("h3").get_text(" ", strip=True)
        company = a.select_one("h4").get_text(" ", strip=True)
        loc = a.select_one("span.job-search-card__location").get_text(" ", strip=True)
        if "israel" not in loc.lower():
            continue
        link = a["href"].split("?")[0]
        rows.append({
            "title": title,
            "company": company,
            "location": loc,
            "link": link,
            "date": date.today().isoformat(),
        })
    return rows


def scrape_glassdoor(keyword: str):
    url = (
        "https://www.glassdoor.com/Job/jobs.htm?sc.keyword="
        f"{quote_plus(keyword)}&locT=N&locId=114&locName=Israel"
    )
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for card in soup.select("article.react-job-listing"):
        title_tag = card.select_one("a.jobLink span")
        if not title_tag:
            continue
        title = title_tag.get_text(" ", strip=True)
        company = card.select_one("div.jobHeader a").get_text(" ", strip=True)
        loc = card.select_one("span.pr-xxsm").get_text(" ", strip=True)
        link = "https://www.glassdoor.com" + card.get("data-job-url", "")
        rows.append({
            "title": title,
            "company": company,
            "location": loc,
            "link": link,
            "date": date.today().isoformat(),
        })
    return rows


def _keep(job, seen_set):
    canonical = job["link"].split("?", 1)[0]
    if canonical in seen_set:
        return False
    if not title_is_allowed(job["title"]):
        return False
    if "israel" not in job["location"].lower():
        return False
    seen_set.add(canonical)
    return True


def search_jobs():
    seen = set()
    jobs = []
    for kw in KEYWORDS:
        for site, func in [
            ("Indeed", scrape_indeed),
            ("LinkedIn", scrape_linkedin),
            ("Glassdoor", scrape_glassdoor),
        ]:
            try:
                for job in func(kw):
                    if _keep(job, seen):
                        jobs.append(job)
            except Exception as e:
                print(f"WARN: {func.__name__} failed for {kw} → {e}")
                notify_blocked(site)
            time.sleep(1)
    return jobs


if __name__ == "__main__":
    from pprint import pprint
    pprint(search_jobs()[:10])
