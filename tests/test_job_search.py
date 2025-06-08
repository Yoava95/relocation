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


def test_skip_seen_job(monkeypatch):
    job = {"link": "http://example.com/job1", "title": "Product Manager"}
    seen = {job["link"]}
    # patch to verify not called; using stub that raises if called
    def fake_page_mentions(url):
        raise AssertionError("page_mentions_relocation should not be called")
    monkeypatch.setattr(job_search, "page_mentions_relocation", fake_page_mentions)
    assert not job_search._keep(job, seen)
    assert job["link"] in seen  # still in seen_set, unchanged


def test_allowed_title_passes(monkeypatch):
    job = {"link": "http://example.com/job2", "title": "Product Manager"}
    seen = set()
    monkeypatch.setattr(job_search, "page_mentions_relocation", lambda url: True)
    assert job_search._keep(job, seen)
    assert job["link"] in seen


def test_fail_without_title_or_relocation(monkeypatch):
    job = {"link": "http://example.com/job3", "title": "QA Engineer"}
    seen = set()
    monkeypatch.setattr(job_search, "page_mentions_relocation", lambda url: False)
    assert not job_search._keep(job, seen)
    assert job["link"] not in seen


def test_allowed_title_without_relocation(monkeypatch):
    job = {"link": "http://example.com/job4", "title": "Product Manager"}
    seen = set()
    monkeypatch.setattr(job_search, "page_mentions_relocation", lambda url: False)
    assert not job_search._keep(job, seen)
    assert job["link"] not in seen


def test_query_is_deduped(monkeypatch):
    job1 = {"link": "http://example.com/job5?utm=123", "title": "Product Manager"}
    seen = {"http://example.com/job5"}
    monkeypatch.setattr(job_search, "page_mentions_relocation", lambda url: True)
    assert not job_search._keep(job1, seen)


def test_blockage_triggers_notification(monkeypatch):
    messages = []
    monkeypatch.setattr(job_search, "KEYWORDS", ["kw"])

    def boom(keyword):
        raise Exception("blocked")

    monkeypatch.setattr(job_search, "scrape_indeed", boom)
    monkeypatch.setattr(job_search, "scrape_otta", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_linkedin", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_glassdoor", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_remotive", lambda kw: [])
    monkeypatch.setattr(job_search, "scrape_page", lambda kw: [])
    monkeypatch.setattr(job_search, "page_mentions_relocation", lambda url: True)
    monkeypatch.setattr(job_search, "time", types.ModuleType("time"))
    job_search.time.sleep = lambda s: None

    monkeypatch.setattr(job_search, "notify_blocked", lambda site: messages.append(site))

    job_search.search_jobs()
    assert messages == ["Indeed"]


def test_scrape_remotive(monkeypatch):
    sample = {
        "jobs": [
            {
                "title": "Product Manager Relocation",
                "company_name": "Acme",
                "candidate_required_location": "Anywhere",
                "url": "http://example.com/job",
                "publication_date": "2024-01-01T00:00:00",
                "description": "Relocation offered",
            }
        ]
    }

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return sample

    def fake_get(url, params=None, headers=None, timeout=10):
        return FakeResp()

    monkeypatch.setattr(job_search.requests, "get", fake_get, raising=False)
    rows = job_search.scrape_remotive("prod")
    assert rows == [
        {
            "title": "Product Manager Relocation",
            "company": "Acme",
            "location": "Anywhere",
            "link": "http://example.com/job",
            "date": "2024-01-01",
        }
    ]
