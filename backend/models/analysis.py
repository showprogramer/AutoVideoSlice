"""
分析结果数据模型

定义高光片段、标题建议等分析结果的数据结构。
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class HighlightType(str, Enum):
    """高光类型"""
    EMOTIONAL = "emotional"      # 情感高潮
    INFORMATIVE = "informative"  # 知识干货
    CONTROVERSIAL = "controversial"  # 争议话题
    HUMOROUS = "humorous"        # 幽默搞笑
    CLIMAX = "climax"            # 剧情高潮
    QUOTE = "quote"              # 金句名言


class HighlightSegment(BaseModel):
    """高光片段"""
    
    start_time: float = Field(..., description="开始时间（秒）")
    end_time: float = Field(..., description="结束时间（秒）")
    title: str = Field(..., description="片段标题/描述")
    reason: str = Field(..., description="为什么这是高光（AI 解释）")
    score: float = Field(default=0.0, ge=0.0, le=10.0, description="片段评分 0-10")
    type: HighlightType = Field(default=HighlightType.EMOTIONAL, description="高光类型")
    keywords: list[str] = Field(default_factory=list, description="关键词")
    
    @property
    def duration(self) -> float:
        """片段时长（秒）"""
        return self.end_time - self.start_time
    
    def format_time_range(self) -> str:
        """格式化时间范围"""
        def fmt(s):
            m, sec = divmod(int(s), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
        return f"{fmt(self.start_time)} - {fmt(self.end_time)}"


class TitleSuggestion(BaseModel):
    """标题建议"""
    
    title: str = Field(..., description="标题文本")
    style: str = Field(default="neutral", description="标题风格：hook/emotional/question/neutral")
    score: float = Field(default=0.0, ge=0.0, le=10.0, description="标题评分 0-10")


class AnalysisResult(BaseModel):
    """完整分析结果"""
    
    highlights: list[HighlightSegment] = Field(default_factory=list, description="高光片段列表")
    titles: list[TitleSuggestion] = Field(default_factory=list, description="标题建议列表")
    summary: Optional[str] = Field(None, description="内容摘要")
    total_duration: float = Field(default=0.0, description="原视频总时长")
    highlight_ratio: float = Field(default=0.0, description="高光占比")
    
    @property
    def highlight_count(self) -> int:
        return len(self.highlights)
    
    @property
    def total_highlight_duration(self) -> float:
        return sum(h.duration for h in self.highlights)


class AnalyzeRequest(BaseModel):
    """分析请求"""
    
    subtitle_text: str = Field(..., description="带时间戳的字幕文本")
    video_duration: Optional[float] = Field(None, description="视频总时长（秒）")
    min_segment_duration: float = Field(default=15.0, description="最小片段时长（秒）")
    max_segment_duration: float = Field(default=120.0, description="最大片段时长（秒）")
    max_highlights: int = Field(default=10, description="最多返回多少个高光")
    generate_titles: bool = Field(default=True, description="是否生成标题建议")


class AnalyzeResponse(BaseModel):
    """分析响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    result: Optional[AnalysisResult] = Field(None, description="分析结果")
    provider: Optional[str] = Field(None, description="使用的 AI 服务")
