"""
Ollama 客户端

本地 AI 模型服务，使用 qwen3:4b。
"""

import httpx
from typing import Optional

from .base import BaseAIService, AIMessage, AIResponse, AIServiceError


class OllamaService(BaseAIService):
    """
    Ollama 本地模型服务
    
    默认使用 qwen3:4b 模型。
    """
    
    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        super().__init__(model)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    @property
    def provider_name(self) -> str:
        return "Ollama"
    
    async def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # 检查模型是否存在（支持带标签和不带标签的匹配）
                    model_base = self.model.split(":")[0]
                    return any(
                        m == self.model or m.startswith(f"{model_base}:")
                        for m in models
                    )
                return False
        except Exception:
            return False
    
    async def chat(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """发送聊天请求到 Ollama"""
        
        # 转换消息格式
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                
                if response.status_code != 200:
                    raise AIServiceError(
                        message=f"请求失败: {response.status_code} - {response.text}",
                        provider=self.provider_name,
                    )
                
                data = response.json()
                
                return AIResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=data.get("model", self.model),
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                    finish_reason=data.get("done_reason", "stop"),
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
