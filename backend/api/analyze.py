"""
分析 API 路由

处理视频内容分析请求。
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from models.analysis import AnalyzeRequest, AnalyzeResponse, AnalysisResult
from services.analyzer import get_analysis_service
from services.ai import AIServiceError


router = APIRouter(prefix="/api/analyze", tags=["分析"])


@router.post("", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest):
    """
    分析字幕内容
    
    从字幕中提取高光片段并生成标题建议。
    """
    service = get_analysis_service()
    
    try:
        result, provider = await service.analyze(
            subtitle_text=request.subtitle_text,
            video_duration=request.video_duration,
            max_highlights=request.max_highlights,
            min_duration=request.min_segment_duration,
            max_duration=request.max_segment_duration,
            generate_titles=request.generate_titles,
        )
        
        return AnalyzeResponse(
            success=True,
            message=f"成功提取 {result.highlight_count} 个高光片段",
            result=result,
            provider=provider,
        )
        
    except AIServiceError as e:
        return AnalyzeResponse(
            success=False,
            message=str(e),
            result=None,
            provider=e.provider,
        )
    except Exception as e:
        return AnalyzeResponse(
            success=False,
            message=f"分析失败: {str(e)}",
            result=None,
        )


@router.post("/highlights")
async def extract_highlights_only(
    subtitle_text: str,
    max_highlights: int = 10,
    min_duration: float = 15.0,
    max_duration: float = 120.0,
):
    """
    仅提取高光片段（不生成标题）
    """
    service = get_analysis_service()
    
    try:
        highlights, summary, provider = await service.extract_highlights(
            subtitle_text=subtitle_text,
            max_highlights=max_highlights,
            min_duration=min_duration,
            max_duration=max_duration,
        )
        
        return {
            "success": True,
            "highlights": [h.model_dump() for h in highlights],
            "summary": summary,
            "provider": provider,
        }
        
    except AIServiceError as e:
        return {
            "success": False,
            "error": str(e),
            "provider": e.provider,
        }


@router.post("/titles")
async def generate_titles_only(
    summary: str,
    highlight_descriptions: Optional[list[str]] = None,
):
    """
    仅生成标题建议
    """
    from models.analysis import HighlightSegment
    
    service = get_analysis_service()
    
    # 构造简单的高光对象用于标题生成
    highlights = []
    if highlight_descriptions:
        for i, desc in enumerate(highlight_descriptions[:5]):
            highlights.append(HighlightSegment(
                start_time=0,
                end_time=60,
                title=desc,
                reason="",
            ))
    
    try:
        titles, provider = await service.generate_titles(summary, highlights)
        
        return {
            "success": True,
            "titles": [t.model_dump() for t in titles],
            "provider": provider,
        }
        
    except AIServiceError as e:
        return {
            "success": False,
            "error": str(e),
            "provider": e.provider,
        }
