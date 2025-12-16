"""
豆包 API 客户端

火山引擎豆包大模型 API，使用 doubao-1.5-pro-32k。
"""

import httpx
from typing import Optional

from .base import BaseAIService, AIMessage, AIResponse, AIServiceError


class DoubaoService(BaseAIService):
    """
    豆包 API 服务
    
    使用火山引擎的豆包大模型 API。
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "doubao-1.5-pro-32k",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        timeout: float = 60.0,
    ):
        super().__init__(model)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    @property
    def provider_name(self) -> str:
        return "Doubao"
    
    async def is_available(self) -> bool:
        """检查豆包 API 是否可用"""
        if not self.api_key:
            return False
        
        try:
            # 发送一个简单的请求测试连接
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5,
                    },
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def chat(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """发送聊天请求到豆包 API"""
        
        # 转换消息格式（OpenAI 兼容格式）
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )
                
                if response.status_code == 401:
                    raise AIServiceError(
                        message="API 密钥无效",
                        provider=self.provider_name,
                    )
                
                if response.status_code == 429:
                    raise AIServiceError(
                        message="请求过于频繁，请稍后重试",
                        provider=self.provider_name,
                    )
                
                if response.status_code != 200:
                    raise AIServiceError(
                        message=f"请求失败: {response.status_code} - {response.text}",
                        provider=self.provider_name,
                    )
                
                data = response.json()
                choice = data.get("choices", [{}])[0]
                
                return AIResponse(
                    content=choice.get("message", {}).get("content", ""),
                    model=data.get("model", self.model),
                    usage=data.get("usage"),
                    finish_reason=choice.get("finish_reason"),
                )
                
        except httpx.TimeoutException:
            raise AIServiceError(
                message="请求超时",
                provider=self.provider_name,
            )
        except httpx.RequestError as e:
            raise AIServiceError(
                message=f"网络错误: {str(e)}",
                provider=self.provider_name,
                original_error=e,
            )
