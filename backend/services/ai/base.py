"""
AI 服务基类

定义 AI 服务的统一接口，所有 AI 客户端都需要实现这个接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from pydantic import BaseModel


class AIMessage(BaseModel):
    """AI 消息"""
    role: str  # system, user, assistant
    content: str


class AIResponse(BaseModel):
    """AI 响应"""
    content: str
    model: str
    usage: Optional[dict] = None  # token 使用情况
    finish_reason: Optional[str] = None


class AIServiceError(Exception):
    """AI 服务错误"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")


class BaseAIService(ABC):
    """
    AI 服务基类
    
    所有 AI 客户端（豆包、Ollama 等）都需要继承此类并实现抽象方法。
    """
    
    def __init__(self, model: str):
        self.model = model
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """服务提供商名称"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        检查服务是否可用
        
        用于健康检查和自动切换逻辑。
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数
            
        Returns:
            AI 响应
        """
        pass
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        简化的补全接口
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            
        Returns:
            生成的文本内容
        """
        messages = []
        
        if system_prompt:
            messages.append(AIMessage(role="system", content=system_prompt))
        
        messages.append(AIMessage(role="user", content=prompt))
        
        response = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.content
