"""FastAPI 웹 대시보드 애플리케이션"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from . import service
from ..data_io import DEFAULT_DATA_DIR


logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="AI Report Dashboard",
    description="AI 뉴스/논문 리포트 대시보드",
    version="1.0.0",
)

# 템플릿 디렉토리 설정
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================================
# HTML Pages
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    q: Optional[str] = Query(None, description="검색어"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
):
    """메인 페이지 - 리포트 목록 또는 검색 결과"""
    categories = service.get_categories()

    # 검색 모드
    if q:
        search_results = service.search_articles(q, category=category)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "query": q,
                "category": category,
                "categories": categories,
                "search_results": search_results,
            },
        )

    # 리포트 목록 모드
    reports = service.list_reports()
    total_articles = sum(r["article_count"] for r in reports)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "reports": reports,
            "total_articles": total_articles,
            "categories": categories,
            "query": None,
            "category": None,
        },
    )


@app.get("/reports/{report_id}", response_class=HTMLResponse)
async def report_detail(request: Request, report_id: str):
    """리포트 상세 페이지"""
    report = service.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    stats = service.get_report_stats(report)
    articles_by_category = report.articles_by_category()
    report_date = report.created_at.strftime("%Y-%m-%d")

    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "report": report,
            "report_date": report_date,
            "stats": stats,
            "articles_by_category": articles_by_category,
        },
    )


# ============================================================================
# REST API
# ============================================================================

@app.get("/api/reports")
async def api_list_reports():
    """REST API - 리포트 목록"""
    reports = service.list_reports()
    return {
        "count": len(reports),
        "reports": reports,
    }


@app.get("/api/reports/{report_id}")
async def api_report_detail(report_id: str):
    """REST API - 리포트 상세"""
    report = service.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    stats = service.get_report_stats(report)

    return {
        "id": report.id,
        "created_at": report.created_at.isoformat(),
        "stats": stats,
        "articles": [a.to_dict() for a in report.articles],
    }


@app.get("/api/search")
async def api_search(
    q: str = Query(..., description="검색어"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
):
    """REST API - 기사 검색"""
    results = service.search_articles(q, category=category)
    return {
        "query": q,
        "category": category,
        "count": len(results),
        "results": results,
    }


@app.get("/api/categories")
async def api_categories():
    """REST API - 카테고리 목록"""
    return {
        "categories": service.get_categories(),
    }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok"}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """서버 실행

    Args:
        host: 바인딩 호스트
        port: 포트 번호
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)
