"""
AI API 路由

提供 AI 服务状态检查和测试接口。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.ai import get_ai_manager, AIServiceError


router = APIRouter(prefix="/api/ai", tags=["AI"])


class AITestRequest(BaseModel):
    """AI 测试请求"""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7


class AITestResponse(BaseModel):
    """AI 测试响应"""
    success: bool
    content: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None


@router.get("/status")
async def get_ai_status():
    """
    获取 AI 服务状态
    
    返回所有 AI 服务的可用性状态。
    """
    manager = get_ai_manager()
    status = await manager.get_status()
    
    # 获取当前可用的服务
    service = await manager.get_available_service()
    status["active_service"] = service.provider_name if service else None
    
    return status


@router.post("/test", response_model=AITestResponse)
async def test_ai(request: AITestRequest):
    """
    测试 AI 服务
    
    发送测试请求到当前可用的 AI 服务。
    """
    manager = get_ai_manager()
    
    try:
        service = await manager.get_available_service()
        if not service:
            return AITestResponse(
                success=False,
                error="没有可用的 AI 服务",
            )
        
        content = await service.complete(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
        )
        
        return AITestResponse(
            success=True,
            content=content,
            provider=service.provider_name,
        )
        
    except AIServiceError as e:
        return AITestResponse(
            success=False,
            error=str(e),
            provider=e.provider,
        )
    except Exception as e:
        return AITestResponse(
            success=False,
            error=f"未知错误: {str(e)}",
        )
