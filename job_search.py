"""
Scrape Relocate.me for relocation-friendly roles that match our keywords.
Returns a list of dicts:
    {title, company, location, link, date}
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; reloc8-agent/1.0)"
}

# Keywords we care about
KEYWORDS = [
    "Product Manager",
    "Senior Product Manager",
    "Staff Product Manager",
    "Principal Product Manager",
    "Innovation Manager",
    "Design Lecturer",
    "Design School Lecturer",
]

DAYS_BACK = 7  # only grab jobs posted in the last N days


def fetch_one_keyword(term: str):
    """
    Pull one search page from Relocate.me and parse out job cards.
    """
    url = f"https://relocate.me/search?term={requests.utils.quote(term)}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("article.job-card")  # CSS class used on Relocate.me

    jobs = []
    for card in cards:
        title = card.select_one(".job-title").get_text(strip=True)
        company = card.select_one(".company-title").get_text(strip=True)
        location = card.select_one(".location").get_text(strip=True)

        link_el = card.select_one("a[itemprop='url']")
        link = "https://relocate.me" + link_el["href"] if link_el else url

        # Date is like "Posted 5 days ago" or "Posted 21 May"
        date_txt = card.select_one(".date") or card.select_one(".posted")
        posted = parse_date(date_txt.get_text() if date_txt else "")

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "date": posted.isoformat() if posted else "",
            }
        )
    return jobs


def parse_date(text: str):
    text = text.lower()
    today = datetime.utcnow().date()

    # "5 days ago"
    m = re.search(r"(\d+)\s+day", text)
    if m:
        return today - timedelta(days=int(m.group(1)))

    # "21 may"
    m = re.search(r"(\d{1,2})\s+([a-z]{3,})", text)
    if m:
        day, month = int(m.group(1)), m.group(2)
        try:
            dt = datetime.strptime(f"{day} {month} {today.year}", "%d %B %Y")
        except ValueError:
            dt = datetime.strptime(f"{day} {month} {today.year}", "%d %b %Y")
        return dt.date()

    return None


def search_jobs():
    """Main entry used by main.py"""
    seen_links = set()
    fresh = []
    for kw in KEYWORDS:
        for job in fetch_one_keyword(kw):
            if job["link"] in seen_links:
                continue
            seen_links.add(job["link"])

            # Filter by recency (optional)
            if job["date"]:
                days_old = (datetime.utcnow().date() - datetime.fromisoformat(job["date"]).date()).days
                if days_old > DAYS_BACK:
                    continue
            fresh.append(job)
    return fresh


if __name__ == "__main__":
    for j in search_jobs()[:5]:
        print(j)
