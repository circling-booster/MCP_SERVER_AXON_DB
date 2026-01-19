class ToolError(Exception):
    """MCP 도구 실행 중 발생하는 기본 에러"""
    pass

class DataLoadError(ToolError):
    pass

class InvalidParameterError(ToolError):
    pass