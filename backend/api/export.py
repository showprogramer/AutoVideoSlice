"""
导出 API 路由

处理视频导出、下载和打包功能。
"""

import os
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from config import get_settings
from services.task_queue import get_task_queue, TaskStatus


router = APIRouter(prefix="/api/export", tags=["导出"])


class PackageRequest(BaseModel):
    """打包请求"""
    task_ids: list[str] = Field(..., description="任务 ID 列表")
    filename: Optional[str] = Field(None, description="输出文件名（不含扩展名）")


class PackageResponse(BaseModel):
    """打包响应"""
    success: bool
    message: str
    download_url: Optional[str] = None
    file_count: int = 0


@router.get("/download/{task_id}")
async def download_video(task_id: str):
    """
    下载单个视频
    
    根据任务 ID 下载切割后的视频文件。
    """
    queue = get_task_queue()
    task = queue.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    if task.status != TaskStatus.DONE:
        raise HTTPException(status_code=400, detail=f"任务未完成，当前状态: {task.status.value}")
    
    if not task.output_path or not os.path.isfile(task.output_path):
        raise HTTPException(status_code=404, detail="输出文件不存在")
    
    return FileResponse(
        path=task.output_path,
        filename=Path(task.output_path).name,
        media_type="video/mp4",
    )


@router.post("/package", response_model=PackageResponse)
async def package_videos(request: PackageRequest):
    """
    打包多个视频
    
    将多个已完成的切割视频打包为 ZIP 文件。
    """
    queue = get_task_queue()
    settings = get_settings()
    
    # 获取所有已完成任务
    valid_paths = []
    for task_id in request.task_ids:
        task = queue.get_task(task_id)
        if task and task.status == TaskStatus.DONE and task.output_path:
            if os.path.isfile(task.output_path):
                valid_paths.append(task.output_path)
    
    if not valid_paths:
        return PackageResponse(
            success=False,
            message="没有可打包的文件",
        )
    
    # 生成 ZIP 文件
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if request.filename:
        zip_name = f"{request.filename}.zip"
    else:
        zip_name = f"video_package_{timestamp}.zip"
    
    zip_path = output_dir / zip_name
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in valid_paths:
                zf.write(path, Path(path).name)
        
        return PackageResponse(
            success=True,
            message=f"打包成功: {len(valid_paths)} 个文件",
            download_url=f"/api/export/zip/{zip_name}",
            file_count=len(valid_paths),
        )
    except Exception as e:
        return PackageResponse(
            success=False,
            message=f"打包失败: {str(e)}",
        )


@router.get("/zip/{filename}")
async def download_zip(filename: str):
    """
    下载 ZIP 包
    """
    settings = get_settings()
    zip_path = Path(settings.output_dir) / filename
    
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(zip_path),
        filename=filename,
        media_type="application/zip",
    )


@router.get("/collection")
async def export_collection():
    """
    导出所有已完成视频
    
    返回所有已完成任务的列表和下载链接。
    """
    queue = get_task_queue()
    
    completed_tasks = [
        {
            "id": t.id,
            "time_range": t.format_time_range(),
            "duration": t.duration,
            "output_path": t.output_path,
            "download_url": f"/api/export/download/{t.id}",
            "filename": Path(t.output_path).name if t.output_path else None,
        }
        for t in queue.get_all_tasks()
        if t.status == TaskStatus.DONE and t.output_path
    ]
    
    return {
        "success": True,
        "count": len(completed_tasks),
        "videos": completed_tasks,
    }
