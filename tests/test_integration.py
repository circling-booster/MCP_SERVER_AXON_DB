import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
import os

# 테스트용 환경변수 설정 (실제 .env보다 우선순위 높게 설정 필요)
os.environ["MCP_API_TOKEN"] = "test-token"
os.environ["CSV_FILE_PATH"] = "MOCK_DATA.csv" 

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "mcp_tool_calls_total" in response.text

def test_auth_failure():
    # 토큰 없이 SSE 연결 시도
    response = client.get("/mcp/sse")
    assert response.status_code == 401

def test_auth_success():
    # 올바른 토큰으로 SSE 연결 시도 (SSE 핸드셰이크는 GET 요청)
    response = client.get(
        "/mcp/sse", 
        headers={"Authorization": f"Bearer {settings.API_TOKEN}"}
    )
    # FastMCP SSE 엔드포인트는 정상 연결 시 스트림 응답을 시작함
    assert response.status_code == 200

# 참고: 실제 도구 실행 테스트는 MCP Client Mocking이 필요하거나, 
# app/services/data_service.py의 유닛 테스트로 대체하는 것이 효율적입니다.
@pytest.mark.asyncio
async def test_duckdb_search_sqlinjection():
    from app.services.data_service import DuckDBService
    service = DuckDBService()
    
    # SQL Injection 시도
    results = await service.search_users("' OR '1'='1", 10)
    # 인젝션이 성공했다면 모든 유저가 나왔겠지만, 바인딩을 썼으므로 결과가 없어야 함
    assert len(results) == 0