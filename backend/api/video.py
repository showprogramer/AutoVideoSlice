"""
视频 API 路由

处理视频信息读取、切割、缩略图等请求。
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional

from config import get_settings
from models.video import (
    VideoInfo,
    VideoInfoRequest,
    CutRequest,
    CutResponse,
    ThumbnailRequest,
    ThumbnailResponse,
    FFmpegStatus,
)
from services.ffmpeg import get_ffmpeg_service


router = APIRouter(prefix="/api/video", tags=["视频"])


@router.get("/ffmpeg-status", response_model=FFmpegStatus)
async def get_ffmpeg_status():
    """
    获取 FFmpeg 状态
    
    检查 FFmpeg 是否可用，返回版本信息。
    """
    service = get_ffmpeg_service()
    return await service.check_availability()


@router.post("/ffmpeg-install", response_model=FFmpegStatus)
async def install_ffmpeg():
    """
    安装 FFmpeg
    
    如果 FFmpeg 未安装，自动下载到 D:/Tools/ffmpeg。
    """
    service = get_ffmpeg_service()
    
    try:
        path = await service.ensure_installed()
        version = await service._get_version(path)
        
        return FFmpegStatus(
            available=True,
            path=path,
            version=version,
            message="FFmpeg 安装成功",
        )
    except Exception as e:
        return FFmpegStatus(
            available=False,
            path=None,
            version=None,
            message=f"FFmpeg 安装失败: {str(e)}",
        )


@router.post("/info", response_model=VideoInfo)
async def get_video_info(request: VideoInfoRequest):
    """
    获取视频信息
    
    读取视频的时长、分辨率、编码等元数据。
    """
    service = get_ffmpeg_service()
    
    # 检查文件存在
    if not os.path.isfile(request.path):
        raise HTTPException(status_code=404, detail=f"视频文件不存在: {request.path}")
    
    try:
        return await service.get_video_info(request.path)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cut", response_model=CutResponse)
async def cut_video(request: CutRequest):
    """
    切割视频
    
    从视频中提取指定时间段的片段。
    """
    service = get_ffmpeg_service()
    settings = get_settings()
    
    # 检查输入文件
    if not os.path.isfile(request.input_path):
        return CutResponse(
            success=False,
            message=f"输入视频不存在: {request.input_path}",
        )
    
    # 验证时间范围
    if request.start_time >= request.end_time:
        return CutResponse(
            success=False,
            message="开始时间必须小于结束时间",
        )
    
    # 生成输出文件名
    input_path = Path(request.input_path)
    if request.output_name:
        output_name = f"{request.output_name}{input_path.suffix}"
    else:
        # 自动生成: 原文件名_开始时间-结束时间
        start_str = f"{int(request.start_time):04d}"
        end_str = f"{int(request.end_time):04d}"
        output_name = f"{input_path.stem}_{start_str}-{end_str}{input_path.suffix}"
    
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    
    try:
        success = await service.cut_video(
            input_path=request.input_path,
            output_path=str(output_path),
            start_time=request.start_time,
            end_time=request.end_time,
            lossless=request.lossless,
        )
        
        if success:
            return CutResponse(
                success=True,
                message="视频切割成功",
                output_path=str(output_path),
                duration=request.duration,
            )
        else:
            return CutResponse(
                success=False,
                message="视频切割失败",
            )
    except Exception as e:
        return CutResponse(
            success=False,
            message=f"切割出错: {str(e)}",
        )


@router.post("/thumbnail", response_model=ThumbnailResponse)
async def generate_thumbnail(request: ThumbnailRequest):
    """
    生成视频缩略图
    
    从视频指定时间点截取一帧作为缩略图。
    """
    service = get_ffmpeg_service()
    settings = get_settings()
    
    # 检查输入文件
    if not os.path.isfile(request.video_path):
        return ThumbnailResponse(
            success=False,
            message=f"视频文件不存在: {request.video_path}",
        )
    
    # 生成输出路径
    video_path = Path(request.video_path)
    thumbnail_dir = Path(settings.output_dir) / "thumbnails"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    time_str = f"{int(request.time):04d}"
    thumbnail_name = f"{video_path.stem}_{time_str}.jpg"
    thumbnail_path = thumbnail_dir / thumbnail_name
    
    try:
        success = await service.generate_thumbnail(
            video_path=request.video_path,
            output_path=str(thumbnail_path),
            time=request.time,
            width=request.width,
            height=request.height,
        )
        
        if success:
            return ThumbnailResponse(
                success=True,
                message="缩略图生成成功",
                thumbnail_path=str(thumbnail_path),
            )
        else:
            return ThumbnailResponse(
                success=False,
                message="缩略图生成失败",
            )
    except Exception as e:
        return ThumbnailResponse(
            success=False,
            message=f"生成出错: {str(e)}",
        )
