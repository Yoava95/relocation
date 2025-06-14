import sys
import types
from pathlib import Path

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub external packages so job_search can be imported without dependencies
sys.modules.setdefault("requests", types.ModuleType("requests"))
bs4_stub = types.ModuleType("bs4")
bs4_stub.BeautifulSoup = object
sys.modules.setdefault("bs4", bs4_stub)

import job_search


def test_skip_seen_job():
    job = {
        "link": "http://example.com/job1",
        "title": "Product Manager",
        "location": "Tel Aviv, Israel",
    }
    seen = {job["link"]}
    assert not job_search._keep(job, seen)
    assert job["link"] in seen


def test_allowed_title_passes():
    job = {
        "link": "http://example.com/job2",
        "title": "Product Manager",
        "location": "Haifa, Israel",
    }
    seen = set()
    assert job_search._keep(job, seen)
    assert job["link"] in seen


def test_fail_without_title():
    job = {
        "link": "http://example.com/job3",
        "title": "QA Engineer",
        "location": "Tel Aviv, Israel",
    }
    seen = set()
    assert not job_search._keep(job, seen)
    assert job["link"] not in seen


def test_allowed_title_wrong_location():
    job = {
        "link": "http://example.com/job4",
        "title": "Product Manager",
        "location": "Berlin, Germany",
    }
    seen = set()
    assert not job_search._keep(job, seen)
    assert job["link"] not in seen


def test_query_is_deduped():
    job1 = {
        "link": "http://example.com/job5?utm=123",
        "title": "Product Manager",
        "location": "Tel Aviv, Israel",
    }
    seen = {"http://example.com/job5"}
    assert not job_search._keep(job1, seen)


def test_blockage_triggers_notification(monkeypatch):
    messages = []
    monkeypatch.setattr(job_search, "KEYWORDS", ["kw"])

    def boom(keyword):
        raise Exception("blocked")

    monkeypatch.setattr(job_search, "scrape_indeed", boom)
    monkeypatch.setattr(job_search, "scrape_linkedin", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_glassdoor", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_jobdata_api", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_remotive", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_jobicy", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_iitjobs", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_craigslist", lambda kw: [])
    monkeypatch.setattr(job_search, "time", types.ModuleType("time"))
    job_search.time.sleep = lambda s: None
    monkeypatch.setattr(job_search, "notify_blocked", lambda site: messages.append(site))

    job_search.search_jobs()
    assert messages == ["Indeed"]


def test_notify_blocked_once_per_provider(monkeypatch):
    messages = []
    monkeypatch.setattr(job_search, "KEYWORDS", ["kw1", "kw2"])

    def boom(keyword):
        raise Exception("blocked")

    monkeypatch.setattr(job_search, "scrape_indeed", boom)
    monkeypatch.setattr(job_search, "scrape_linkedin", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_glassdoor", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_jobdata_api", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_remotive", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_jobicy", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_iitjobs", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_craigslist", lambda kw: [])
    monkeypatch.setattr(job_search, "time", types.ModuleType("time"))
    job_search.time.sleep = lambda s: None
    monkeypatch.setattr(job_search, "notify_blocked", lambda site: messages.append(site))

    job_search.search_jobs()
    assert messages == ["Indeed"]
