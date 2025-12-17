"""
评分系统数据模型

定义评分维度、片段评分等数据结构。
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ScoreDimensionType(str, Enum):
    """评分维度类型"""
    VIRALITY = "virality"           # 传播力
    EMOTION = "emotion"             # 情感强度
    DENSITY = "density"             # 信息密度
    COMPLETENESS = "completeness"   # 完整性


class RecommendationLevel(str, Enum):
    """推荐等级"""
    EXCELLENT = "excellent"  # 优秀 (8-10分)
    GOOD = "good"            # 良好 (6-8分)
    FAIR = "fair"            # 一般 (4-6分)
    POOR = "poor"            # 较差 (0-4分)


class ScoreDimension(BaseModel):
    """评分维度"""
    
    name: ScoreDimensionType = Field(..., description="维度类型")
    score: float = Field(..., ge=0.0, le=10.0, description="得分 0-10")
    weight: float = Field(..., ge=0.0, le=1.0, description="权重 0-1")
    description: str = Field(default="", description="评分理由")
    
    @property
    def weighted_score(self) -> float:
        """加权得分"""
        return self.score * self.weight


class SegmentScore(BaseModel):
    """片段综合评分"""
    
    total_score: float = Field(..., ge=0.0, le=10.0, description="总分 0-10")
    dimensions: list[ScoreDimension] = Field(default_factory=list, description="各维度得分")
    recommendation: RecommendationLevel = Field(..., description="推荐等级")
    summary: str = Field(default="", description="评分总结")
    
    @classmethod
    def get_recommendation(cls, score: float) -> RecommendationLevel:
        """根据分数获取推荐等级"""
        if score >= 8.0:
            return RecommendationLevel.EXCELLENT
        elif score >= 6.0:
            return RecommendationLevel.GOOD
        elif score >= 4.0:
            return RecommendationLevel.FAIR
        else:
            return RecommendationLevel.POOR


# 默认权重配置
DEFAULT_WEIGHTS = {
    ScoreDimensionType.VIRALITY: 0.30,      # 传播力 30%
    ScoreDimensionType.EMOTION: 0.25,       # 情感强度 25%
    ScoreDimensionType.DENSITY: 0.25,       # 信息密度 25%
    ScoreDimensionType.COMPLETENESS: 0.20,  # 完整性 20%
}


class ScoreRequest(BaseModel):
    """评分请求"""
    
    start_time: float = Field(..., description="开始时间（秒）")
    end_time: float = Field(..., description="结束时间（秒）")
    title: str = Field(..., description="片段标题")
    reason: str = Field(default="", description="高光理由")
    type: Optional[str] = Field(default="emotional", description="高光类型")
    keywords: list[str] = Field(default_factory=list, description="关键词")
    
    @property
    def duration(self) -> float:
        """片段时长（秒）"""
        return self.end_time - self.start_time


class ScoreResponse(BaseModel):
    """评分响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    score: Optional[SegmentScore] = Field(None, description="评分结果")


class BatchScoreRequest(BaseModel):
    """批量评分请求"""
    
    segments: list[ScoreRequest] = Field(..., description="片段列表")


class BatchScoreResponse(BaseModel):
    """批量评分响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="处理消息")
    scores: list[SegmentScore] = Field(default_factory=list, description="评分结果列表")
