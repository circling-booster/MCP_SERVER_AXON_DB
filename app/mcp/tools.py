from mcp.server.fastmcp import FastMCP
from pydantic import Field
from app.services.data_service import data_service
from app.core.security import audit_log
from app.models import PaginatedResponse, User, ErrorResponse
from app.core.exceptions import ToolError
from config import settings
import json

# FastMCP 인스턴스 (의존성 주입은 main.py에서 처리)
mcp = FastMCP("ProductionUserDataServer")

@mcp.tool()
@audit_log("list_users")
async def list_users(
    page: int = Field(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Field(10, ge=1, le=100, description="페이지 당 항목 수")
) -> str: # MCP Protocol상 최종 리턴은 문자열(JSON)이 안전함. 내부 로직은 객체 사용.
    """
    사용자 목록을 페이징하여 조회합니다.
    """
    try:
        actual_size = min(page_size, settings.PAGE_SIZE_MAX)
        result = await data_service.get_users(page, actual_size)
        # Pydantic 모델로 변환하여 유효성 검증 후 JSON 직렬화
        response = PaginatedResponse(**result)
        return response.model_dump_json()
    except Exception as e:
        return ErrorResponse(error="Internal Error", details=str(e)).model_dump_json()

@mcp.tool()
@audit_log("get_user_by_id")
async def get_user_by_id(
    user_id: int = Field(..., description="사용자 고유 ID")
) -> str:
    """ID로 특정 사용자를 조회합니다."""
    try:
        user_data = await data_service.get_user_by_id(user_id)
        if not user_data:
            return ErrorResponse(error="User not found").model_dump_json()
        return User(**user_data).model_dump_json()
    except Exception as e:
        return ErrorResponse(error="Search Error", details=str(e)).model_dump_json()

@mcp.tool()
@audit_log("search_users")
async def search_users(
    query: str = Field(..., min_length=2, description="검색어 (이름 또는 이메일)"),
    limit: int = Field(5, ge=1, le=20, description="최대 결과 수")
) -> str:
    """이름이나 이메일로 사용자를 검색합니다 (대소문자 구분 없음)."""
    try:
        results = await data_service.search_users(query, limit)
        users = [User(**row) for row in results]
        return json.dumps([u.model_dump() for u in users]) # List serialization
    except Exception as e:
         return ErrorResponse(error="Search Failed", details=str(e)).model_dump_json()