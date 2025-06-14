# Local job search for product manager roles in Israel

import html
import re
import time
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


def canonical_url(url: str) -> str:
    """Return a canonical form of the URL for deduping."""
    return url.split("?", 1)[0]


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


def scrape_jobdata_api(keyword: str):
    """Fetch jobs from JobdataAPI REST endpoint."""
    base = "https://jobdataapi.com/api/jobs/?country_code=IL"
    url = base
    jobs = []
    while url:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        for item in data.get("results", data.get("jobs", [])):
            jobs.append(
                {
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("location", "Israel"),
                    "link": item.get("apply_url") or item.get("url"),
                    "date": item.get("date_posted", "")[:10],
                }
            )
        next_url = data.get("next")
        if next_url and not next_url.startswith("http"):
            next_url = "https://jobdataapi.com" + next_url
        url = next_url
    return jobs


def scrape_remotive(keyword: str):
    """Remote jobs from Remotive API."""
    url = "https://remotive.io/api/remote-jobs?search=israel"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    jobs = []
    for item in data.get("jobs", []):
        jobs.append(
            {
                "title": item.get("title", ""),
                "company": item.get("company_name", ""),
                "location": item.get("candidate_required_location", "Remote, Israel"),
                "link": item.get("url"),
                "date": item.get("publication_date", "")[:10],
            }
        )
    return jobs


def scrape_jobicy(keyword: str):
    """Remote jobs from Jobicy API."""
    url = "https://jobicy.com/api/v2/remote-jobs?geo=israel"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    jobs = []
    for item in data.get("jobs", []):
        jobs.append(
            {
                "title": item.get("title", ""),
                "company": item.get("company"),
                "location": item.get("location", "Remote, Israel"),
                "link": item.get("job_url") or item.get("url"),
                "date": item.get("date" , "")[:10],
            }
        )
    return jobs


def scrape_iitjobs(keyword: str):
    """Parse RSS feed from IITJobs."""
    url = "https://www.iitjobs.com/jobs-in-israel/rss-jobs"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    rows = []
    for item in soup.select("item"):
        rows.append(
            {
                "title": item.title.get_text(strip=True),
                "company": "",
                "location": "Israel",
                "link": item.link.get_text(strip=True),
                "date": item.pubDate.get_text(strip=True)[:16],
            }
        )
    return rows


def scrape_craigslist(keyword: str):
    """Craigslist RSS feed for Israeli jobs via JobMob."""
    url = "https://telaviv.craigslist.org/search/jjj?format=rss"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    rows = []
    for item in soup.select("item"):
        rows.append(
            {
                "title": item.title.get_text(strip=True),
                "company": "",
                "location": "Israel",
                "link": item.link.get_text(strip=True),
                "date": item.pubDate.get_text(strip=True)[:16],
            }
        )
    return rows


SCRAPERS = [
    ("Indeed", "scrape_indeed"),
    ("LinkedIn", "scrape_linkedin"),
    ("Glassdoor", "scrape_glassdoor"),
    ("JobdataAPI", "scrape_jobdata_api"),
    ("Remotive", "scrape_remotive"),
    ("Jobicy", "scrape_jobicy"),
    ("IITJobs", "scrape_iitjobs"),
    ("Craigslist", "scrape_craigslist"),
]


def _keep(job, seen_set):
    canonical = canonical_url(job["link"])
    if canonical in seen_set:
        return False
    if not title_is_allowed(job["title"]):
        return False
    if "israel" not in job["location"].lower():
        return False
    seen_set.add(canonical)
    return True


def search_jobs(keywords=None, scrapers=None):
    keywords = keywords or KEYWORDS
    scrapers = scrapers or SCRAPERS
    seen = set()
    jobs = []
    blocked = set()
    for kw in keywords:
        for site, func_name in scrapers:
            func = globals()[func_name]
            try:
                for job in func(kw):
                    if _keep(job, seen):
                        jobs.append(job)
            except Exception as exc:
                print(f"WARN: {func.__name__} failed for {kw} → {exc}")
                if site not in blocked:
                    notify_blocked(site)
                    blocked.add(site)
            time.sleep(1)
    return jobs


if __name__ == "__main__":
    from pprint import pprint
    pprint(search_jobs()[:10])
