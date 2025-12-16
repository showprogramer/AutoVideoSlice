"""
字幕数据模型

定义字幕相关的数据结构。
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SubtitleFormat(str, Enum):
    """字幕格式枚举"""
    SRT = "srt"
    VTT = "vtt"
    UNKNOWN = "unknown"


class SubtitleEntry(BaseModel):
    """单条字幕条目"""
    
    index: int = Field(..., description="字幕序号")
    start_time: float = Field(..., description="开始时间（秒）")
    end_time: float = Field(..., description="结束时间（秒）")
    text: str = Field(..., description="字幕文本内容")
    
    @property
    def duration(self) -> float:
        """字幕持续时间（秒）"""
        return self.end_time - self.start_time
    
    def format_time(self, seconds: float) -> str:
        """格式化时间为 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def to_srt_format(self) -> str:
        """转换为 SRT 格式字符串"""
        return (
            f"{self.index}\n"
            f"{self.format_time(self.start_time)} --> {self.format_time(self.end_time)}\n"
            f"{self.text}\n"
        )


class SubtitleData(BaseModel):
    """完整字幕数据"""
    
    filename: str = Field(..., description="原始文件名")
    format: SubtitleFormat = Field(..., description="字幕格式")
    entries: list[SubtitleEntry] = Field(default_factory=list, description="字幕条目列表")
    total_duration: Optional[float] = Field(None, description="总时长（秒）")
    
    @property
    def entry_count(self) -> int:
        """字幕条目数量"""
        return len(self.entries)
    
    @property
    def full_text(self) -> str:
        """获取完整字幕文本（用于 AI 分析）"""
        return "\n".join(entry.text for entry in self.entries)
    
    def get_text_with_timestamps(self) -> str:
        """获取带时间戳的文本（用于 AI 分析高光片段）"""
        lines = []
        for entry in self.entries:
            time_str = f"[{entry.format_time(entry.start_time)} - {entry.format_time(entry.end_time)}]"
            lines.append(f"{time_str} {entry.text}")
        return "\n".join(lines)
    
    def get_entries_in_range(
        self, start: float, end: float
    ) -> list[SubtitleEntry]:
        """获取指定时间范围内的字幕条目"""
        return [
            entry for entry in self.entries
            if entry.start_time >= start and entry.end_time <= end
        ]


class SubtitleParseRequest(BaseModel):
    """字幕解析请求"""
    
    content: str = Field(..., description="字幕文件内容")
    filename: str = Field(..., description="文件名（用于判断格式）")


class SubtitleParseResponse(BaseModel):
    """字幕解析响应"""
    
    success: bool = Field(..., description="解析是否成功")
    message: str = Field(..., description="处理消息")
    data: Optional[SubtitleData] = Field(None, description="解析后的字幕数据")
