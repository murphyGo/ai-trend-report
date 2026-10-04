"""Generation must preserve sources and reject malformed or invented records."""

import json
import subprocess
from unittest.mock import Mock

import pytest

from src.codex_report import ReportGenerationError, build_prompt, generate_report, parse_report
from src.models import Article, Audience, Category, Source


@pytest.fixture
def articles():
    return [Article(id="source-1", title="Original title", url="https://example.org/source",
                    source=Source.OPENAI_BLOG, content="source content")]


def payload():
    return {"articles": [{"id": "source-1", "summary": "새로운 모델이 공개됐습니다. 기술적인 특징을 소개합니다. 개발에 활용할 수 있습니다.",
                          "category": "LLM", "audience": ["GENERAL", "DEVELOPER"]}]}


def test_valid_report_preserves_source_and_does_not_mutate_input(articles):
    report = parse_report(json.dumps(payload()), articles)
    selected = report.articles[0]
    assert selected.url == articles[0].url
    assert selected.title == articles[0].title
    assert selected.content == articles[0].content
    assert selected.category == Category.LLM
    assert selected.audience == [Audience.GENERAL, Audience.DEVELOPER]
    assert articles[0].summary == ""


@pytest.mark.parametrize("field,value", [
    ("id", "invented-id"), ("summary", ""), ("summary", "English only" * 5),
    ("category", "invented-category"), ("category", {}),
    ("audience", []), ("audience", ["ADMIN"]), ("audience", ["GENERAL", "GENERAL"]),
    ("audience", [["GENERAL"]]), ("url", "https://attacker.example"),
])
def test_invalid_selection_is_rejected(articles, field, value):
    data = payload()
    data["articles"][0][field] = value
    with pytest.raises(ReportGenerationError, match="^invalid_codex_report$"):
        parse_report(json.dumps(data), articles)


@pytest.mark.parametrize("raw", ["not json", "[]", '{"articles":[]}', '{"articles":{},"extra":1}'])
def test_invalid_structure_is_rejected(articles, raw):
    with pytest.raises(ReportGenerationError):
        parse_report(raw, articles)


def test_duplicate_selection_is_rejected(articles):
    data = payload()
    data["articles"] *= 2
    with pytest.raises(ReportGenerationError):
        parse_report(json.dumps(data), articles * 2)


def test_quiet_day_does_not_call_model():
    runner = Mock()
    assert generate_report([], runner).articles == []
    runner.assert_not_called()


def test_model_failure_is_not_fallback_or_raw_output(articles):
    runner = Mock(return_value=subprocess.CompletedProcess([], 1, "sensitive output", "details"))
    with pytest.raises(ReportGenerationError, match="^codex_report_failed$"):
        generate_report(articles, runner)
    runner.assert_called_once()


def test_generate_uses_stdin_and_preserves_ranking_criteria(articles):
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(payload())))
    assert len(generate_report(articles, runner).articles) == 1
    kwargs = runner.call_args.kwargs
    assert kwargs["input"] == build_prompt(articles)
    assert kwargs["timeout"] == 600
    assert "source content" in kwargs["input"]
    assert "untrusted source data" in kwargs["input"]
