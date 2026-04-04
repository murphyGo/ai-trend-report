"""Claude API를 사용한 기사 요약 및 카테고리 분류"""

import json
import logging
from typing import Optional

import anthropic

from .models import Article, Category
from .config import Config
from .utils.retry import retry_with_backoff


logger = logging.getLogger(__name__)

# 재시도할 API 예외 타입들
RETRYABLE_API_EXCEPTIONS = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)


CATEGORIES_STR = "\n".join([f"- {cat.value}" for cat in Category])

SUMMARIZE_PROMPT = """당신은 AI/ML 분야 전문 기술 에디터입니다.
다음 기사를 읽고 한국어로 요약해주세요.

## 요구사항
1. 3-5문장으로 핵심 내용을 요약
2. 기술적 의의와 실용적 영향을 포함
3. 전문 용어는 그대로 사용하되 필요시 간단히 설명

## 카테고리
아래 카테고리 중 가장 적합한 것을 하나 선택해주세요:
{categories}

## 기사 제목
{title}

## 기사 내용
{content}

## 응답 형식 (JSON)
{{
  "summary": "한국어 요약 내용",
  "category": "선택한 카테고리 (위 목록에서 정확히 복사)"
}}
"""


class Summarizer:
    """Claude API를 사용한 기사 요약기"""

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic.api_key)
        self.model = config.anthropic.model

    def summarize(self, article: Article) -> Article:
        """기사 요약 및 카테고리 분류"""
        if not article.content:
            logger.warning(f"No content to summarize for: {article.title}")
            return article

        prompt = SUMMARIZE_PROMPT.format(
            categories=CATEGORIES_STR,
            title=article.title,
            content=article.content[:8000],  # 토큰 제한
        )

        try:
            response_text = self._call_api(prompt)

            if response_text:
                result = self._parse_response(response_text)

                if result:
                    article.summary = result.get("summary", "")
                    category_str = result.get("category", "")
                    article.category = Category.from_string(category_str)

                logger.info(f"Summarized: {article.title[:50]}... -> {article.category.value}")

        except anthropic.APIError as e:
            logger.error(f"Claude API error for {article.title}: {e}")
        except Exception as e:
            logger.error(f"Summarization failed for {article.title}: {e}")

        return article

    @retry_with_backoff(max_retries=3, base_delay=2.0, exceptions=RETRYABLE_API_EXCEPTIONS)
    def _call_api(self, prompt: str) -> Optional[str]:
        """Claude API 호출 (재시도 포함)"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.content[0].text

    def summarize_batch(self, articles: list[Article]) -> list[Article]:
        """여러 기사 일괄 요약"""
        summarized = []
        for i, article in enumerate(articles):
            logger.info(f"Summarizing [{i+1}/{len(articles)}]: {article.title[:50]}...")
            summarized.append(self.summarize(article))
        return summarized

    def _parse_response(self, response_text: str) -> Optional[dict]:
        """Claude 응답에서 JSON 추출"""
        # JSON 블록 추출 시도
        try:
            # ```json ... ``` 블록 처리
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                # 중괄호로 직접 찾기
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]

            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")

            # 폴백: 텍스트에서 직접 추출
            summary = response_text.strip()
            if len(summary) > 500:
                summary = summary[:500] + "..."

            return {
                "summary": summary,
                "category": "기타",
            }
