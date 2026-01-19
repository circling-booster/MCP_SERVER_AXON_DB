from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.mcp.tools import mcp
from app.services.data_service import data_service
from config import settings
from prometheus_client import make_asgi_app

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

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    lifespan=lifespan
)

# 1. Prometheus 메트릭
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 2. 헬스 체크 & Readiness Probe
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    try:
        await data_service.get_user_by_id(1)
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503

# 3. 인증 미들웨어 (Mount된 앱 보호용)
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # /mcp 경로로 시작하는 요청에 대해서만 토큰 검사
    if request.url.path.startswith("/mcp"):
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {settings.API_TOKEN}":
            return JSONResponse(
                status_code=401, 
                content={"detail": "Invalid or missing authentication credentials"}
            )
    
    response = await call_next(request)
    return response

# 4. MCP SSE 앱 마운트
# mcp.sse_app()은 Starlette 앱을 반환하며, 이를 /mcp 경로에 마운트합니다.
# 결과적으로 /mcp/sse, /mcp/messages 엔드포인트가 생성됩니다.
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)