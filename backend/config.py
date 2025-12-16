"""
配置管理模块

管理应用程序的所有配置项，支持环境变量覆盖。
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "AutoVideoSlice"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 8000
    
    # CORS 配置
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    
    # AI 模型配置
    # 本地模型 (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    
    # 云端模型 (豆包)
    doubao_api_key: Optional[str] = None
    doubao_model: str = "doubao-1-5-pro-32k-250115"
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    
    # AI 策略：local_first | cloud_first | local_only | cloud_only
    ai_strategy: str = "local_first"
    
    # 文件路径配置
    output_dir: str = "output"
    temp_dir: str = "temp"
    
    # FFmpeg 配置
    ffmpeg_path: Optional[str] = None  # 为 None 时使用系统 PATH
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
