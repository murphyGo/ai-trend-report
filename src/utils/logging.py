"""로깅 설정 모듈

구조화된 로깅(JSON 형식)과 로그 파일 출력을 지원합니다.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포매터

    로그 파일에 구조화된 JSON 형식으로 로그를 출력합니다.
    분석 및 모니터링 도구에서 쉽게 파싱할 수 있습니다.
    """

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 문자열로 변환"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 예외 정보 포함
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False,
) -> None:
    """로깅 설정을 초기화합니다.

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR). 기본값 INFO.
        log_file: 로그 파일 경로. None이면 파일 출력 안 함.
        verbose: True면 DEBUG 레벨로 강제 설정 (--verbose 플래그용).

    Notes:
        - 콘솔 출력: 사람이 읽기 쉬운 형식 (기존 포맷 유지)
        - 파일 출력: JSON 형식 (구조화된 로깅)
        - verbose=True는 level 설정보다 우선함
    """
    # 로그 레벨 결정 (verbose가 config보다 우선)
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()

    # 콘솔 핸들러 (사람이 읽기 쉬운 형식)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (JSON 형식)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
