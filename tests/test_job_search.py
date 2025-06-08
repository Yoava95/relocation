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
