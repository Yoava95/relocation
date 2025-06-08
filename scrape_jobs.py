import json
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def main():
    query = quote_plus("product manager relocation")
    url = f"https://www.indeed.com/jobs?q={query}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        print(json.dumps({"error": f"Failed to fetch results: {exc}"}))
        return

    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for card in soup.select("a.tapItem"):
        title = card.select_one("h2").get_text(" ", strip=True)
        if "relocation" not in title.lower():
            continue
        company = card.select_one(".companyName").get_text(strip=True)
        loc = card.select_one(".companyLocation").get_text(strip=True)
        link = "https://www.indeed.com" + card["href"]
        rows.append({"title": title, "company": company, "location": loc, "link": link})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
