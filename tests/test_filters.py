"""filters.py 단위 테스트 (Phase 8.2 + 8.3) + arxiv published_at 파싱 (Phase 8.1)"""

from datetime import datetime, timedelta, timezone

import pytest

from src.filters import filter_by_recency, filter_already_seen
from src.models import Article, Source


def _make_article(url: str, published_at=None) -> Article:
    return Article(
        title=f"title-{url}",
        url=url,
        source=Source.ARXIV,
        published_at=published_at,
    )


# Fixed reference point for deterministic tests
NOW = datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc)


class TestFilterByRecency:
    """Phase 8.2 — 시간 창 필터"""

    def test_all_recent_passes(self):
        articles = [
            _make_article("a", NOW - timedelta(hours=1)),
            _make_article("b", NOW - timedelta(hours=23)),
        ]
        kept, dropped, unknown = filter_by_recency(articles, days=2, now=NOW)
        assert len(kept) == 2
        assert dropped == 0
        assert unknown == 0

    def test_drops_old_articles(self):
        articles = [
            _make_article("recent", NOW - timedelta(hours=1)),
            _make_article("old", NOW - timedelta(days=5)),
        ]
        kept, dropped, unknown = filter_by_recency(articles, days=2, now=NOW)
        assert [a.url for a in kept] == ["recent"]
        assert dropped == 1

    def test_boundary_exact_cutoff_kept(self):
        """cutoff 시점의 기사는 유지 (>=)"""
        cutoff_time = NOW - timedelta(days=2)
        articles = [_make_article("boundary", cutoff_time)]
        kept, dropped, _ = filter_by_recency(articles, days=2, now=NOW)
        assert len(kept) == 1
        assert dropped == 0

    def test_just_past_cutoff_dropped(self):
        articles = [_make_article("old", NOW - timedelta(days=2, seconds=1))]
        kept, dropped, _ = filter_by_recency(articles, days=2, now=NOW)
        assert kept == []
        assert dropped == 1

    def test_published_at_none_is_kept(self):
        """published_at이 None이면 보수적으로 유지 (fallback)"""
        articles = [
            _make_article("unknown1", None),
            _make_article("unknown2", None),
            _make_article("old", NOW - timedelta(days=10)),
        ]
        kept, dropped, unknown_kept = filter_by_recency(articles, days=2, now=NOW)
        assert len(kept) == 2  # 2 unknown kept, 1 old dropped
        assert dropped == 1
        assert unknown_kept == 2

    def test_days_zero_disables_filter(self):
        """days=0이면 필터 비활성화 (모든 기사 통과)"""
        articles = [
            _make_article("recent", NOW - timedelta(hours=1)),
            _make_article("old", NOW - timedelta(days=30)),
        ]
        kept, dropped, _ = filter_by_recency(articles, days=0, now=NOW)
        assert len(kept) == 2
        assert dropped == 0

    def test_empty_input(self):
        kept, dropped, unknown = filter_by_recency([], days=2, now=NOW)
        assert kept == []
        assert dropped == 0
        assert unknown == 0

    def test_naive_published_at_treated_as_utc(self):
        """naive datetime은 UTC로 간주되어 aware cutoff와 비교됨"""
        naive_recent = datetime(2026, 4, 12, 11, 0, 0)  # 1시간 전 (naive)
        naive_old = datetime(2026, 4, 5, 12, 0, 0)      # 7일 전 (naive)
        articles = [
            _make_article("naive-recent", naive_recent),
            _make_article("naive-old", naive_old),
        ]
        kept, dropped, _ = filter_by_recency(articles, days=2, now=NOW)
        assert [a.url for a in kept] == ["naive-recent"]
        assert dropped == 1

    def test_mixed_tz_aware_and_naive(self):
        """aware와 naive가 섞여도 올바르게 비교"""
        aware = NOW - timedelta(hours=1)
        naive = datetime(2026, 4, 12, 10, 0, 0)  # 2시간 전 naive
        articles = [
            _make_article("aware-recent", aware),
            _make_article("naive-recent", naive),
        ]
        kept, dropped, _ = filter_by_recency(articles, days=1, now=NOW)
        assert len(kept) == 2
        assert dropped == 0


class TestFilterAlreadySeen:
    """Phase 8.3 — URL 기반 중복 제거"""

    def test_removes_seen_urls(self):
        articles = [
            _make_article("https://a.com/1"),
            _make_article("https://a.com/2"),
            _make_article("https://a.com/3"),
        ]
        seen = {"https://a.com/2"}
        kept, removed = filter_already_seen(articles, seen)
        assert [a.url for a in kept] == ["https://a.com/1", "https://a.com/3"]
        assert removed == 1

    def test_all_removed(self):
        articles = [_make_article("x"), _make_article("y")]
        seen = {"x", "y"}
        kept, removed = filter_already_seen(articles, seen)
        assert kept == []
        assert removed == 2

    def test_none_removed(self):
        articles = [_make_article("a"), _make_article("b")]
        seen = {"c", "d"}
        kept, removed = filter_already_seen(articles, seen)
        assert len(kept) == 2
        assert removed == 0

    def test_empty_seen_set(self):
        articles = [_make_article("a"), _make_article("b")]
        kept, removed = filter_already_seen(articles, set())
        assert len(kept) == 2
        assert removed == 0

    def test_empty_articles(self):
        kept, removed = filter_already_seen([], {"a", "b"})
        assert kept == []
        assert removed == 0


class TestDataIOLoadRecentReportUrls:
    """data_io.load_recent_report_urls 통합 테스트"""

    def test_loads_urls_from_multiple_reports(self, tmp_path):
        from src.data_io import save_report, load_recent_report_urls
        from src.models import Report

        # Create 3 fake reports
        for i, date_label in enumerate(["2026-04-10", "2026-04-11", "2026-04-12"]):
            arts = [
                _make_article(f"https://x.com/{date_label}/{j}")
                for j in range(3)
            ]
            report = Report(
                articles=arts,
                created_at=datetime(2026, 4, 10 + i),
            )
            save_report(report, output_dir=tmp_path, filename=f"report_{date_label}.json")

        urls = load_recent_report_urls(tmp_path, n=7)
        assert len(urls) == 9
        assert "https://x.com/2026-04-12/0" in urls
        assert "https://x.com/2026-04-10/2" in urls

    def test_limits_to_n_reports(self, tmp_path):
        from src.data_io import save_report, load_recent_report_urls
        from src.models import Report

        # 5 reports
        for i in range(5):
            arts = [_make_article(f"r{i}-url")]
            report = Report(
                articles=arts,
                created_at=datetime(2026, 4, 1 + i),
            )
            save_report(
                report,
                output_dir=tmp_path,
                filename=f"report_2026-04-0{i+1}.json",
            )

        # Only last 2 (newest) should be loaded
        urls = load_recent_report_urls(tmp_path, n=2)
        # newest: 2026-04-05 and 2026-04-04 → r4-url, r3-url
        assert urls == {"r4-url", "r3-url"}

    def test_empty_data_dir(self, tmp_path):
        from src.data_io import load_recent_report_urls
        urls = load_recent_report_urls(tmp_path, n=7)
        assert urls == set()


class TestArxivDateParser:
    """Phase 8.1 — arxiv RSS pubDate/dc:date 파싱 (DEBT-003 해소)"""

    def test_rfc822_pubdate(self):
        from src.collectors.arxiv import _parse_arxiv_date
        result = _parse_arxiv_date("Thu, 10 Apr 2026 00:00:00 +0000")
        assert result is not None
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 10

    def test_rfc822_with_gmt(self):
        from src.collectors.arxiv import _parse_arxiv_date
        result = _parse_arxiv_date("Mon, 07 Apr 2026 03:14:15 GMT")
        assert result is not None
        assert result.hour == 3

    def test_iso_with_z(self):
        from src.collectors.arxiv import _parse_arxiv_date
        result = _parse_arxiv_date("2026-04-10T00:00:00Z")
        assert result is not None
        assert result.year == 2026

    def test_iso_date_only(self):
        from src.collectors.arxiv import _parse_arxiv_date
        result = _parse_arxiv_date("2026-04-10")
        assert result is not None
        assert result.year == 2026

    @pytest.mark.parametrize("value", [None, "", "garbage", "not-a-date"])
    def test_invalid_returns_none(self, value):
        from src.collectors.arxiv import _parse_arxiv_date
        assert _parse_arxiv_date(value) is None

    def test_arxiv_collector_populates_published_at(self):
        """xml.etree 파싱 경로로 pubDate가 Article.published_at에 들어가는지 확인.

        실제 네트워크 호출 없이 static XML로 검증.
        """
        from src.collectors.arxiv import ArxivCollector
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
<channel>
<item>
  <title>Test Paper (cs.AI)</title>
  <link>http://arxiv.org/abs/2604.12345</link>
  <description>Abstract: test</description>
  <pubDate>Thu, 10 Apr 2026 00:00:00 +0000</pubDate>
</item>
<item>
  <title>Another Paper</title>
  <link>http://arxiv.org/abs/2604.12346</link>
  <description>Abstract</description>
  <dc:date>2026-04-11T00:00:00Z</dc:date>
</item>
</channel>
</rss>"""
        collector = ArxivCollector(categories=["cs.AI"])
        with patch.object(collector, "_fetch_text", return_value=sample_xml):
            articles = collector._fetch_rss("cs.AI")

        assert len(articles) == 2
        assert articles[0].published_at is not None
        assert articles[0].published_at.year == 2026
        assert articles[0].published_at.month == 4
        assert articles[0].published_at.day == 10
        # 두 번째 아이템은 dc:date 사용
        assert articles[1].published_at is not None
        assert articles[1].published_at.day == 11
