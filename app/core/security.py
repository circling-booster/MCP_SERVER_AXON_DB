import logging
import time
from typing import Dict, Any, Callable
from functools import wraps
from datetime import datetime
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pythonjsonlogger import jsonlogger
from app.core.telemetry import TOOL_CALL_COUNT, TOOL_LATENCY, AUTH_FAILURES
from config import settings

# 로거 설정
logger = logging.getLogger("audit")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(settings.LOG_LEVEL)

security = HTTPBearer()

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """민감 정보 마스킹 처리"""
    SENSITIVE_KEYS = {'email', 'password', 'token', 'authorization', 'ip_address'}
    masked = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            masked[k] = "***"
        else:
            masked[k] = v
    return masked

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰 검증 (추후 JWT 디코딩 및 스코프 확인 로직 확장 가능)"""
    if credentials.credentials != settings.API_TOKEN:
        AUTH_FAILURES.inc()
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return credentials.credentials

def audit_log(tool_name: str):
    """감사 로깅 및 메트릭 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                TOOL_LATENCY.labels(tool_name=tool_name).observe(duration)
                TOOL_CALL_COUNT.labels(tool_name=tool_name, status="success").inc()
                
                logger.info("tool_execution_success", extra={
                    "tool": tool_name,
                    "duration_ms": round(duration * 1000, 2),
                    "params": mask_sensitive_data(kwargs)
                })
                return result
            except Exception as e:
                TOOL_CALL_COUNT.labels(tool_name=tool_name, status="error").inc()
                logger.error("tool_execution_failed", extra={
                    "tool": tool_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "params": mask_sensitive_data(kwargs)
                })
                raise e
        return wrapper
    return decorator