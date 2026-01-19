import duckdb
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.core.exceptions import DataLoadError
from config import settings

logger = logging.getLogger("audit")

class DuckDBService:
    def __init__(self):
        self._file_path = Path(settings.CSV_FILE_PATH)
        self._last_mtime = 0.0
        self._conn = None
        self._lock = asyncio.Lock() # DuckDB Connection은 Thread-safe하지 않을 수 있으므로 Lock 사용
        
        # 초기 로드 시도
        try:
            self._ensure_connection()
        except Exception as e:
            logger.error(f"Initial DB connection failed: {e}")

    def _ensure_connection(self):
        """파일 변경 확인 및 재연결"""
        if not self._file_path.exists():
            raise DataLoadError(f"CSV file not found at {self._file_path}")

        current_mtime = self._file_path.stat().st_mtime
        if self._conn is None or current_mtime != self._last_mtime:
            logger.info("Reloading data source from CSV (DuckDB)")
            try:
                # 인메모리 DB 생성 후 CSV를 테이블로 등록
                self._conn = duckdb.connect(":memory:")
                self._conn.execute(
                    f"CREATE OR REPLACE TABLE users AS SELECT * FROM read_csv_auto('{self._file_path}')"
                )
                self._last_mtime = current_mtime
            except Exception as e:
                raise DataLoadError(f"Failed to load CSV into DuckDB: {e}")

    async def get_users(self, page: int, page_size: int) -> Dict[str, Any]:
        async with self._lock:
            self._ensure_connection()
            offset = (page - 1) * page_size
            
            # 전체 카운트와 데이터 조회를 단일 트랜잭션처럼 처리
            total = self._conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            rows = self._conn.execute(
                "SELECT * FROM users LIMIT ? OFFSET ?", 
                [page_size, offset]
            ).fetch_df().to_dict(orient="records")
            
            return {
                "data": rows,
                "total": total,
                "page": page,
                "page_size": page_size
            }

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        async with self._lock:
            self._ensure_connection()
            df = self._conn.execute(
                "SELECT * FROM users WHERE id = ?", [user_id]
            ).fetch_df()
            
            if df.empty:
                return None
            return df.iloc[0].to_dict()

    async def search_users(self, query: str, limit: int) -> List[Dict]:
        async with self._lock:
            self._ensure_connection()
            search_pattern = f"%{query}%"
            # SQL Injection 방지를 위해 파라미터 바인딩 사용
            rows = self._conn.execute(
                """
                SELECT * FROM users 
                WHERE first_name ILIKE ? OR last_name ILIKE ? OR email ILIKE ? 
                LIMIT ?
                """,
                [search_pattern, search_pattern, search_pattern, limit]
            ).fetch_df().to_dict(orient="records")
            return rows

data_service = DuckDBService()