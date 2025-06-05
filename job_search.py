
"""Searches relocation-friendly jobs from a few public sites without paid APIs.
Currently returns a mocked list; extend with BeautifulSoup scraping later.
"""
from datetime import date

def search_jobs():
    # TODO: Replace with real scraping logic
    today = date.today().isoformat()
    return [
        {
            "title": "Staff Product Manager",
            "company": "Shopify",
            "location": "Toronto, Canada",
            "link": "https://example.com/job1",
            "date": today,
        },
        {
            "title": "Principal Product Manager",
            "company": "Google",
            "location": "Zurich, Switzerland",
            "link": "https://example.com/job2",
            "date": today,
        },
    ]

if __name__ == "__main__":
    for j in search_jobs():
        print(j)
