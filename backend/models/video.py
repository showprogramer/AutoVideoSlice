"""
视频相关数据模型

定义视频信息、切割请求等数据结构。
"""

from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path


class VideoInfo(BaseModel):
    """视频信息"""
    
    path: str = Field(..., description="文件路径")
    filename: str = Field(..., description="文件名")
    duration: float = Field(..., description="时长（秒）")
    width: int = Field(default=0, description="宽度")
    height: int = Field(default=0, description="高度")
    codec: str = Field(default="", description="视频编码")
    audio_codec: str = Field(default="", description="音频编码")
    bitrate: int = Field(default=0, description="比特率 (bps)")
    fps: float = Field(default=0.0, description="帧率")
    size_bytes: int = Field(default=0, description="文件大小（字节）")
    
    @property
    def size_mb(self) -> float:
        """文件大小 MB"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def resolution(self) -> str:
        """分辨率字符串"""
        return f"{self.width}x{self.height}"
    
    def format_duration(self) -> str:
        """格式化时长"""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class VideoInfoRequest(BaseModel):
    """视频信息请求"""
    
    path: str = Field(..., description="视频文件路径")


class CutRequest(BaseModel):
    """视频切割请求"""
    
    input_path: str = Field(..., description="输入视频路径")
    start_time: float = Field(..., ge=0, description="开始时间（秒）")
    end_time: float = Field(..., ge=0, description="结束时间（秒）")
    output_name: Optional[str] = Field(None, description="输出文件名（不含扩展名）")
    lossless: bool = Field(default=True, description="是否无损切割")
    
    @property
    def duration(self) -> float:
        """切割时长"""
        return self.end_time - self.start_time


class CutResponse(BaseModel):
    """视频切割响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    output_path: Optional[str] = Field(None, description="输出文件路径")
    duration: Optional[float] = Field(None, description="切割时长")


class ThumbnailRequest(BaseModel):
    """缩略图请求"""
    
    video_path: str = Field(..., description="视频路径")
    time: float = Field(..., ge=0, description="截取时间点（秒）")
    width: Optional[int] = Field(None, description="缩略图宽度")
    height: Optional[int] = Field(None, description="缩略图高度")


class ThumbnailResponse(BaseModel):
    """缩略图响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    thumbnail_path: Optional[str] = Field(None, description="缩略图路径")


class FFmpegStatus(BaseModel):
    """FFmpeg 状态"""
    
    available: bool = Field(..., description="是否可用")
    path: Optional[str] = Field(None, description="FFmpeg 路径")
    version: Optional[str] = Field(None, description="版本信息")
    message: str = Field(..., description="状态消息")
