"""
AI 服务管理器

实现模型自动切换逻辑：本地优先，云端回退。
"""

from typing import Optional
from functools import lru_cache

from .base import BaseAIService, AIMessage, AIResponse, AIServiceError
from .ollama import OllamaService
from .doubao import DoubaoService
from config import get_settings


class AIManager:
    """
    AI 服务管理器
    
    根据配置和可用性自动选择 AI 服务。
    
    策略：
    - local_first: 优先使用本地模型，不可用时回退到云端
    - cloud_first: 优先使用云端 API，不可用时回退到本地
    - local_only: 只使用本地模型
    - cloud_only: 只使用云端 API
    """
    
    def __init__(self):
        settings = get_settings()
        
        self.strategy = settings.ai_strategy
        
        # 初始化服务
        self.ollama = OllamaService(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )
        
        self.doubao = DoubaoService(
            api_key=settings.doubao_api_key or "",
            model=settings.doubao_model,
            base_url=settings.doubao_base_url,
        ) if settings.doubao_api_key else None
        
        # 缓存可用性状态
        self._availability_cache: dict[str, bool] = {}
    
    async def get_available_service(self) -> Optional[BaseAIService]:
        """
        根据策略获取可用的 AI 服务
        
        Returns:
            可用的 AI 服务，如果都不可用则返回 None
        """
        if self.strategy == "local_only":
            if await self._check_ollama():
                return self.ollama
            return None
        
        if self.strategy == "cloud_only":
            if await self._check_doubao():
                return self.doubao
            return None
        
        if self.strategy == "cloud_first":
            if await self._check_doubao():
                return self.doubao
            if await self._check_ollama():
                return self.ollama
            return None
        
        # 默认 local_first
        if await self._check_ollama():
            return self.ollama
        if await self._check_doubao():
            return self.doubao
        return None
    
    async def _check_ollama(self) -> bool:
        """检查 Ollama 是否可用"""
        try:
            return await self.ollama.is_available()
        except Exception:
            return False
    
    async def _check_doubao(self) -> bool:
        """检查豆包是否可用"""
        if not self.doubao:
            return False
        try:
            return await self.doubao.is_available()
        except Exception:
            return False
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        使用可用的 AI 服务完成请求
        
        自动选择服务并处理回退逻辑。
        """
        service = await self.get_available_service()
        
        if not service:
            raise AIServiceError(
                message="没有可用的 AI 服务，请检查 Ollama 是否运行或配置豆包 API 密钥",
                provider="AIManager",
            )
        
        return await service.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def chat(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """
        使用可用的 AI 服务进行聊天
        
        自动选择服务并处理回退逻辑。
        """
        service = await self.get_available_service()
        
        if not service:
            raise AIServiceError(
                message="没有可用的 AI 服务",
                provider="AIManager",
            )
        
        return await service.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def get_status(self) -> dict:
        """获取所有 AI 服务的状态"""
        ollama_available = await self._check_ollama()
        doubao_available = await self._check_doubao()
        
        return {
            "strategy": self.strategy,
            "services": {
                "ollama": {
                    "available": ollama_available,
                    "model": self.ollama.model if ollama_available else None,
                },
                "doubao": {
                    "available": doubao_available,
                    "model": self.doubao.model if doubao_available and self.doubao else None,
                },
            },
        }


@lru_cache()
def get_ai_manager() -> AIManager:
    """获取 AI 管理器单例"""
    return AIManager()
