"""
内容分析服务

实现高光片段提取和标题生成逻辑。
"""

import json
import re
from typing import Optional

from models.analysis import (
    AnalysisResult,
    HighlightSegment,
    TitleSuggestion,
    HighlightType,
)
from services.ai import get_ai_manager, AIServiceError
from services.prompts import (
    HIGHLIGHT_EXTRACTION_SYSTEM_PROMPT,
    HIGHLIGHT_EXTRACTION_USER_PROMPT,
    TITLE_GENERATION_SYSTEM_PROMPT,
    TITLE_GENERATION_USER_PROMPT,
)


class AnalysisService:
    """内容分析服务"""
    
    def __init__(self):
        self.ai_manager = get_ai_manager()
    
    async def extract_highlights(
        self,
        subtitle_text: str,
        max_highlights: int = 10,
        min_duration: float = 15.0,
        max_duration: float = 120.0,
    ) -> tuple[list[HighlightSegment], str, str]:
        """
        提取高光片段
        
        Args:
            subtitle_text: 带时间戳的字幕文本
            max_highlights: 最多返回多少个高光
            min_duration: 最小片段时长
            max_duration: 最大片段时长
            
        Returns:
            (高光片段列表, 内容摘要, 使用的AI服务名称)
        """
        # 获取可用的 AI 服务
        service = await self.ai_manager.get_available_service()
        if not service:
            raise AIServiceError(
                message="没有可用的 AI 服务",
                provider="AnalysisService",
            )
        
        # 构建 Prompt
        user_prompt = HIGHLIGHT_EXTRACTION_USER_PROMPT.format(
            max_highlights=max_highlights,
            min_duration=int(min_duration),
            max_duration=int(max_duration),
            subtitle_text=subtitle_text[:15000],  # 限制长度
        )
        
        # 调用 AI
        response = await service.complete(
            prompt=user_prompt,
            system_prompt=HIGHLIGHT_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.7,
        )
        
        # 解析结果
        highlights, summary = self._parse_highlight_response(response)
        
        return highlights, summary, service.provider_name
    
    async def generate_titles(
        self,
        summary: str,
        highlights: list[HighlightSegment],
    ) -> tuple[list[TitleSuggestion], str]:
        """
        生成标题建议
        
        Args:
            summary: 内容摘要
            highlights: 高光片段列表
            
        Returns:
            (标题建议列表, 使用的AI服务名称)
        """
        service = await self.ai_manager.get_available_service()
        if not service:
            raise AIServiceError(
                message="没有可用的 AI 服务",
                provider="AnalysisService",
            )
        
        # 构建高光描述
        highlights_text = "\n".join([
            f"- {h.title}: {h.reason}"
            for h in highlights[:5]
        ])
        
        user_prompt = TITLE_GENERATION_USER_PROMPT.format(
            summary=summary or "视频内容",
            highlights=highlights_text or "无",
        )
        
        response = await service.complete(
            prompt=user_prompt,
            system_prompt=TITLE_GENERATION_SYSTEM_PROMPT,
            temperature=0.8,
        )
        
        titles = self._parse_title_response(response)
        
        return titles, service.provider_name
    
    async def analyze(
        self,
        subtitle_text: str,
        video_duration: Optional[float] = None,
        max_highlights: int = 10,
        min_duration: float = 15.0,
        max_duration: float = 120.0,
        generate_titles: bool = True,
    ) -> tuple[AnalysisResult, str]:
        """
        完整分析流程
        
        Args:
            subtitle_text: 带时间戳的字幕文本
            video_duration: 视频总时长
            max_highlights: 最多返回多少个高光
            min_duration: 最小片段时长
            max_duration: 最大片段时长
            generate_titles: 是否生成标题
            
        Returns:
            (分析结果, 使用的AI服务名称)
        """
        # 提取高光
        highlights, summary, provider = await self.extract_highlights(
            subtitle_text=subtitle_text,
            max_highlights=max_highlights,
            min_duration=min_duration,
            max_duration=max_duration,
        )
        
        # 生成标题
        titles = []
        if generate_titles and (summary or highlights):
            titles, _ = await self.generate_titles(summary, highlights)
        
        # 计算统计
        total_highlight_duration = sum(h.duration for h in highlights)
        highlight_ratio = (
            total_highlight_duration / video_duration
            if video_duration and video_duration > 0
            else 0.0
        )
        
        result = AnalysisResult(
            highlights=highlights,
            titles=titles,
            summary=summary,
            total_duration=video_duration or 0.0,
            highlight_ratio=highlight_ratio,
        )
        
        return result, provider
    
    def _parse_highlight_response(
        self, response: str
    ) -> tuple[list[HighlightSegment], str]:
        """解析 AI 返回的高光提取结果"""
        highlights = []
        summary = ""
        
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                summary = data.get("summary", "")
                
                for item in data.get("highlights", []):
                    try:
                        highlight = HighlightSegment(
                            start_time=float(item.get("start_time", 0)),
                            end_time=float(item.get("end_time", 0)),
                            title=str(item.get("title", "无标题")),
                            reason=str(item.get("reason", "")),
                            score=float(item.get("score", 5.0)),
                            type=self._parse_highlight_type(item.get("type")),
                            keywords=item.get("keywords", []),
                        )
                        if highlight.duration > 0:
                            highlights.append(highlight)
                    except (ValueError, TypeError):
                        continue
                        
        except json.JSONDecodeError:
            pass
        
        return highlights, summary
    
    def _parse_title_response(self, response: str) -> list[TitleSuggestion]:
        """解析 AI 返回的标题生成结果"""
        titles = []
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                for item in data.get("titles", []):
                    try:
                        title = TitleSuggestion(
                            title=str(item.get("title", "")),
                            style=str(item.get("style", "neutral")),
                            score=float(item.get("score", 5.0)),
                        )
                        if title.title:
                            titles.append(title)
                    except (ValueError, TypeError):
                        continue
                        
        except json.JSONDecodeError:
            pass
        
        return titles
    
    def _parse_highlight_type(self, type_str: Optional[str]) -> HighlightType:
        """解析高光类型"""
        if not type_str:
            return HighlightType.EMOTIONAL
        
        try:
            return HighlightType(type_str.lower())
        except ValueError:
            return HighlightType.EMOTIONAL


# 单例
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """获取分析服务单例"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
