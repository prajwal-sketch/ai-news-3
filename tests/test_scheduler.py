from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.models.crawl_job import CrawlJob
from app.registry.source_registry import SourceRegistry
from app.scheduler import Scheduler


def write_registry(path: Path) -> SourceRegistry:
    payload = [
        {
            "id": 1,
            "name": "Alpha",
            "url": "https://alpha.example",
            "crawler": "simple_crawler",
            "parser": "html_parser",
            "crawl_frequency": "6h",
            "enabled": True,
            "priority": 10,
            "category": "AI",
            "allowed_paths": ["/"],
            "last_crawled": "2024-01-01T05:00:00",
        },
        {
            "id": 2,
            "name": "Beta",
            "url": "https://beta.example",
            "crawler": "rss_crawler",
            "parser": "rss_parser",
            "crawl_frequency": "1h",
            "enabled": True,
            "priority": 2,
            "category": "AI",
            "allowed_paths": ["/"],
            "last_crawled": "2024-01-01T10:00:00",
        },
        {
            "id": 3,
            "name": "Gamma",
            "url": "https://gamma.example",
            "crawler": "api",
            "parser": "html_parser",
            "crawl_frequency": "12h",
            "enabled": True,
            "priority": 3,
            "category": "AI",
            "allowed_paths": ["/"],
            "last_crawled": "2023-12-31T00:00:00",
        },
        {
            "id": 4,
            "name": "Delta",
            "url": "https://delta.example",
            "crawler": "playwright",
            "parser": "html_parser",
            "crawl_frequency": "24h",
            "enabled": True,
            "priority": 1,
            "category": "AI",
            "allowed_paths": ["/"],
            "last_crawled": "2024-01-01T11:00:00",
        },
        {
            "id": 5,
            "name": "Epsilon",
            "url": "https://epsilon.example",
            "crawler": "simple_crawler",
            "parser": "html_parser",
            "crawl_frequency": "4h",
            "enabled": False,
            "priority": 1,
            "category": "AI",
            "allowed_paths": ["/"],
            "last_crawled": None,
        },
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")
    return SourceRegistry(path=path)


def test_get_due_jobs_returns_due_sources_sorted_by_priority(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "sources.json")
    scheduler = Scheduler(registry)
    fixed_now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

    with patch.object(scheduler, "_get_now", return_value=fixed_now):
        jobs = scheduler.get_due_jobs(max_jobs=2)

    assert len(jobs) == 2
    assert [job.source.name for job in jobs] == ["Beta", "Gamma"]
    assert all(isinstance(job, CrawlJob) for job in jobs)
    assert jobs[0].scheduled_time == fixed_now
    assert jobs[0].priority == 2


def test_get_due_jobs_marks_sources_without_previous_crawl_as_due(tmp_path: Path) -> None:
    payload = [
        {
            "id": 1,
            "name": "First",
            "url": "https://first.example",
            "crawler": "simple_crawler",
            "parser": "html_parser",
            "crawl_frequency": "24h",
            "enabled": True,
            "priority": 7,
            "category": "AI",
            "allowed_paths": ["/"],
            "last_crawled": None,
        }
    ]
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    registry = SourceRegistry(path=path)
    scheduler = Scheduler(registry)

    jobs = scheduler.get_due_jobs()

    assert len(jobs) == 1
    assert jobs[0].source.name == "First"
    assert "No previous crawl" in jobs[0].reason
