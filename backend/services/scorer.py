"""
评分服务

实现基于规则的片段评分逻辑。
"""

from typing import Optional

from models.scoring import (
    ScoreDimension,
    ScoreDimensionType,
    SegmentScore,
    RecommendationLevel,
    ScoreRequest,
    DEFAULT_WEIGHTS,
)
from models.analysis import HighlightSegment, HighlightType


class ScoringService:
    """评分服务"""
    
    # 高光类型对应的情感基础分
    TYPE_EMOTION_SCORES = {
        HighlightType.EMOTIONAL: 8.5,
        HighlightType.CLIMAX: 8.0,
        HighlightType.HUMOROUS: 7.5,
        HighlightType.CONTROVERSIAL: 7.0,
        HighlightType.QUOTE: 7.0,
        HighlightType.INFORMATIVE: 6.0,
    }
    
    # 传播力关键词
    VIRAL_KEYWORDS = [
        "震惊", "没想到", "真相", "揭秘", "秘密",
        "绝了", "太强了", "神了", "牛", "厉害",
        "感动", "泪目", "破防", "扎心", "哭了",
        "笑死", "搞笑", "有趣", "好玩", "逗",
    ]
    
    def score_segment(
        self,
        segment: ScoreRequest,
    ) -> SegmentScore:
        """
        为单个片段评分
        
        使用基于规则的评分算法。
        """
        dimensions = []
        
        # 1. 传播力评分 (30%)
        virality = self._score_virality(segment)
        dimensions.append(virality)
        
        # 2. 情感强度评分 (25%)
        emotion = self._score_emotion(segment)
        dimensions.append(emotion)
        
        # 3. 信息密度评分 (25%)
        density = self._score_density(segment)
        dimensions.append(density)
        
        # 4. 完整性评分 (20%)
        completeness = self._score_completeness(segment)
        dimensions.append(completeness)
        
        # 计算总分
        total_score = sum(d.weighted_score for d in dimensions)
        total_score = round(min(10.0, max(0.0, total_score)), 2)
        
        # 获取推荐等级
        recommendation = SegmentScore.get_recommendation(total_score)
        
        # 生成总结
        summary = self._generate_summary(total_score, dimensions)
        
        return SegmentScore(
            total_score=total_score,
            dimensions=dimensions,
            recommendation=recommendation,
            summary=summary,
        )
    
    def score_all(
        self,
        segments: list[ScoreRequest],
    ) -> list[SegmentScore]:
        """批量评分"""
        return [self.score_segment(seg) for seg in segments]
    
    def score_highlight(
        self,
        highlight: HighlightSegment,
    ) -> SegmentScore:
        """从 HighlightSegment 评分"""
        request = ScoreRequest(
            start_time=highlight.start_time,
            end_time=highlight.end_time,
            title=highlight.title,
            reason=highlight.reason,
            type=highlight.type.value,
            keywords=highlight.keywords,
        )
        return self.score_segment(request)
    
    def _score_virality(self, segment: ScoreRequest) -> ScoreDimension:
        """评估传播力"""
        score = 5.0  # 基础分
        reasons = []
        
        # 检查标题和理由中的爆款关键词
        text = f"{segment.title} {segment.reason}".lower()
        keyword_count = sum(1 for kw in self.VIRAL_KEYWORDS if kw in text)
        
        if keyword_count >= 3:
            score += 3.0
            reasons.append("包含多个爆款关键词")
        elif keyword_count >= 1:
            score += 1.5
            reasons.append("包含爆款关键词")
        
        # 检查用户定义的关键词
        if len(segment.keywords) >= 3:
            score += 1.0
            reasons.append("关键词丰富")
        
        # 争议性内容传播力更强
        if segment.type == "controversial":
            score += 1.5
            reasons.append("话题有争议性")
        
        score = min(10.0, max(0.0, score))
        
        return ScoreDimension(
            name=ScoreDimensionType.VIRALITY,
            score=round(score, 2),
            weight=DEFAULT_WEIGHTS[ScoreDimensionType.VIRALITY],
            description="、".join(reasons) if reasons else "传播力一般",
        )
    
    def _score_emotion(self, segment: ScoreRequest) -> ScoreDimension:
        """评估情感强度"""
        # 根据高光类型设置基础分
        try:
            highlight_type = HighlightType(segment.type)
            score = self.TYPE_EMOTION_SCORES.get(highlight_type, 5.0)
        except ValueError:
            score = 5.0
        
        reasons = []
        
        # 情感类型得分说明
        type_names = {
            "emotional": "情感类内容，感染力强",
            "climax": "剧情高潮，吸引力强",
            "humorous": "幽默内容，易传播",
            "controversial": "争议话题，引发讨论",
            "quote": "金句名言，值得收藏",
            "informative": "知识干货，实用价值",
        }
        
        if segment.type in type_names:
            reasons.append(type_names[segment.type])
        
        return ScoreDimension(
            name=ScoreDimensionType.EMOTION,
            score=round(score, 2),
            weight=DEFAULT_WEIGHTS[ScoreDimensionType.EMOTION],
            description="、".join(reasons) if reasons else "情感表达适中",
        )
    
    def _score_density(self, segment: ScoreRequest) -> ScoreDimension:
        """评估信息密度"""
        score = 5.0
        reasons = []
        
        duration = segment.duration
        
        # 时长与信息密度关系
        # 30-90秒是最佳时长
        if 30 <= duration <= 90:
            score += 2.0
            reasons.append("时长最优(30-90秒)")
        elif 15 <= duration < 30:
            score += 1.0
            reasons.append("时长稍短")
        elif 90 < duration <= 120:
            score += 1.0
            reasons.append("时长稍长")
        elif duration > 120:
            score -= 1.0
            reasons.append("时长过长，可能拖沓")
        elif duration < 15:
            score -= 1.0
            reasons.append("时长过短，信息不足")
        
        # 关键词数量反映信息丰富度
        if len(segment.keywords) >= 3:
            score += 1.5
            reasons.append("信息点丰富")
        elif len(segment.keywords) >= 1:
            score += 0.5
            reasons.append("有明确信息点")
        
        # 标题长度
        if 10 <= len(segment.title) <= 30:
            score += 0.5
            reasons.append("标题概括精准")
        
        score = min(10.0, max(0.0, score))
        
        return ScoreDimension(
            name=ScoreDimensionType.DENSITY,
            score=round(score, 2),
            weight=DEFAULT_WEIGHTS[ScoreDimensionType.DENSITY],
            description="、".join(reasons) if reasons else "信息密度一般",
        )
    
    def _score_completeness(self, segment: ScoreRequest) -> ScoreDimension:
        """评估完整性"""
        score = 6.0  # 基础分 - 假设 AI 提取的片段基本完整
        reasons = []
        
        duration = segment.duration
        
        # 时长合理性（完整内容通常不会太短）
        if duration >= 30:
            score += 2.0
            reasons.append("时长充足")
        elif duration >= 20:
            score += 1.0
            reasons.append("时长基本够用")
        else:
            reasons.append("时长偏短")
        
        # 有明确的高光理由说明内容完整
        if len(segment.reason) >= 20:
            score += 1.5
            reasons.append("内容描述完整")
        elif len(segment.reason) >= 10:
            score += 0.5
            reasons.append("有基本描述")
        
        score = min(10.0, max(0.0, score))
        
        return ScoreDimension(
            name=ScoreDimensionType.COMPLETENESS,
            score=round(score, 2),
            weight=DEFAULT_WEIGHTS[ScoreDimensionType.COMPLETENESS],
            description="、".join(reasons) if reasons else "完整性待验证",
        )
    
    def _generate_summary(
        self,
        total_score: float,
        dimensions: list[ScoreDimension],
    ) -> str:
        """生成评分总结"""
        if total_score >= 8.0:
            return "优质片段，强烈推荐发布"
        elif total_score >= 6.0:
            return "质量良好，可以考虑发布"
        elif total_score >= 4.0:
            return "质量一般，建议优化后发布"
        else:
            return "质量较差，不建议发布"


# 单例
_scoring_service: Optional[ScoringService] = None


def get_scoring_service() -> ScoringService:
    """获取评分服务单例"""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
