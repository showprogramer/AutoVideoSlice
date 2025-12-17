"""
评分 API 路由

处理片段评分请求。
"""

from fastapi import APIRouter

from models.scoring import (
    ScoreRequest,
    ScoreResponse,
    BatchScoreRequest,
    BatchScoreResponse,
)
from services.scorer import get_scoring_service


router = APIRouter(prefix="/api/score", tags=["评分"])


@router.post("", response_model=ScoreResponse)
async def score_segment(request: ScoreRequest):
    """
    为单个片段评分
    
    基于传播力、情感强度、信息密度、完整性四个维度进行评分。
    """
    service = get_scoring_service()
    
    try:
        score = service.score_segment(request)
        
        return ScoreResponse(
            success=True,
            message=f"评分完成，总分：{score.total_score}，等级：{score.recommendation.value}",
            score=score,
        )
        
    except Exception as e:
        return ScoreResponse(
            success=False,
            message=f"评分失败: {str(e)}",
            score=None,
        )


@router.post("/batch", response_model=BatchScoreResponse)
async def score_batch(request: BatchScoreRequest):
    """
    批量评分
    
    为多个片段同时评分。
    """
    service = get_scoring_service()
    
    try:
        scores = service.score_all(request.segments)
        
        # 统计各等级数量
        excellent = sum(1 for s in scores if s.recommendation.value == "excellent")
        good = sum(1 for s in scores if s.recommendation.value == "good")
        
        return BatchScoreResponse(
            success=True,
            message=f"完成 {len(scores)} 个片段评分，优秀: {excellent}，良好: {good}",
            scores=scores,
        )
        
    except Exception as e:
        return BatchScoreResponse(
            success=False,
            message=f"批量评分失败: {str(e)}",
            scores=[],
        )
