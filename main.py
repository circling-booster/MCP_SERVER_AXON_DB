from fastapi import FastAPI, Depends, Request
from prometheus_client import make_asgi_app
from contextlib import asynccontextmanager
import logging

from app.mcp.tools import mcp
from app.core.security import verify_token
from app.services.data_service import data_service
from config import settings

# 로거 설정
logger = logging.getLogger("audit")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 데이터 로드 확인
    try:
        logger.info("Server starting... Checking data source.")
        data_service._ensure_connection()
    except Exception as e:
        logger.critical(f"Failed to initialize data source: {e}")
    yield
    # 종료 시 정리 로직 (필요 시)

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    lifespan=lifespan
)

# 1. Prometheus 메트릭
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 2. 헬스 체크 & Readiness Probe (운영성 개선)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    try:
        # DB 연결 테스트 (간단한 쿼리)
        await data_service.get_user_by_id(1)
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503

# 3. SSE Endpoint 마운트 (보안 적용)
# FastMCP의 mount_sse를 사용하여 /mcp/sse, /mcp/messages 엔드포인트 자동 생성
# verify_token 의존성을 주입하여 모든 요청에 대해 인증 강제
mcp.mount_sse(app, "/mcp", dependencies=[Depends(verify_token)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)