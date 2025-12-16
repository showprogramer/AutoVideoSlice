"""
字幕 API 路由

处理字幕文件的上传和解析。
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional

from models.subtitle import SubtitleParseRequest, SubtitleParseResponse, SubtitleData
from services.subtitle import parse_subtitle, detect_format, SubtitleFormat


router = APIRouter(prefix="/api/subtitle", tags=["字幕"])


@router.post("/parse", response_model=SubtitleParseResponse)
async def parse_subtitle_content(request: SubtitleParseRequest):
    """
    解析字幕内容
    
    接收字幕文件内容和文件名，返回解析后的结构化数据。
    """
    try:
        # 检测格式
        format_type = detect_format(request.filename, request.content)
        if format_type == SubtitleFormat.UNKNOWN:
            return SubtitleParseResponse(
                success=False,
                message=f"不支持的字幕格式: {request.filename}",
                data=None,
            )
        
        # 解析字幕
        subtitle_data = parse_subtitle(request.content, request.filename)
        
        return SubtitleParseResponse(
            success=True,
            message=f"成功解析 {subtitle_data.entry_count} 条字幕",
            data=subtitle_data,
        )
    
    except Exception as e:
        return SubtitleParseResponse(
            success=False,
            message=f"解析失败: {str(e)}",
            data=None,
        )


@router.post("/upload", response_model=SubtitleParseResponse)
async def upload_subtitle(file: UploadFile = File(...)):
    """
    上传并解析字幕文件
    
    接收上传的字幕文件，自动检测格式并解析。
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 尝试多种编码解码
        text_content = None
        for encoding in ["utf-8", "gbk", "gb2312", "utf-16", "latin-1"]:
            try:
                text_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            return SubtitleParseResponse(
                success=False,
                message="无法解码字幕文件，请确保文件编码正确",
                data=None,
            )
        
        # 解析字幕
        subtitle_data = parse_subtitle(text_content, file.filename)
        
        return SubtitleParseResponse(
            success=True,
            message=f"成功解析 {subtitle_data.entry_count} 条字幕",
            data=subtitle_data,
        )
    
    except ValueError as e:
        return SubtitleParseResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        return SubtitleParseResponse(
            success=False,
            message=f"处理失败: {str(e)}",
            data=None,
        )


@router.get("/formats")
async def get_supported_formats():
    """获取支持的字幕格式"""
    return {
        "formats": [
            {"extension": ".srt", "name": "SubRip", "description": "最常用的字幕格式"},
            {"extension": ".vtt", "name": "WebVTT", "description": "Web 视频文本轨道格式"},
        ]
    }
