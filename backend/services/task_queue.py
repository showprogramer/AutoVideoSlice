"""
切割任务队列

管理视频切割任务的创建、执行和状态跟踪。
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from services.ffmpeg import get_ffmpeg_service


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    DONE = "done"            # 执行完成
    FAILED = "failed"        # 执行失败


class CutTask(BaseModel):
    """切割任务"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    input_path: str = Field(..., description="输入视频路径")
    start_time: float = Field(..., description="开始时间（秒）")
    end_time: float = Field(..., description="结束时间（秒）")
    output_name: Optional[str] = Field(None, description="输出文件名")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress: float = Field(default=0.0, description="进度 0-100")
    output_path: Optional[str] = Field(None, description="输出文件路径")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)
    
    @property
    def duration(self) -> float:
        """切割时长"""
        return self.end_time - self.start_time
    
    def format_time_range(self) -> str:
        """格式化时间范围"""
        def fmt(sec):
            m, s = divmod(int(sec), 60)
            return f"{m:02d}:{s:02d}"
        return f"{fmt(self.start_time)} - {fmt(self.end_time)}"


class BatchCutRequest(BaseModel):
    """批量切割请求"""
    
    input_path: str = Field(..., description="输入视频路径")
    segments: list[dict] = Field(..., description="切割片段列表")
    # 每个 segment: {"start_time": float, "end_time": float, "output_name": optional str}


class BatchCutResponse(BaseModel):
    """批量切割响应"""
    
    success: bool
    message: str
    task_ids: list[str] = Field(default_factory=list)
    total_tasks: int = 0


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self, max_concurrent: int = 2):
        self.tasks: dict[str, CutTask] = {}
        self.max_concurrent = max_concurrent
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    def add_task(self, task: CutTask) -> str:
        """添加任务到队列"""
        self.tasks[task.id] = task
        return task.id
    
    def add_batch(
        self,
        input_path: str,
        segments: list[dict],
    ) -> list[str]:
        """批量添加任务"""
        task_ids = []
        for i, seg in enumerate(segments):
            task = CutTask(
                input_path=input_path,
                start_time=seg.get("start_time", 0),
                end_time=seg.get("end_time", 0),
                output_name=seg.get("output_name"),
            )
            self.add_task(task)
            task_ids.append(task.id)
        return task_ids
    
    def get_task(self, task_id: str) -> Optional[CutTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> list[CutTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_pending_tasks(self) -> list[CutTask]:
        """获取待执行任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def get_running_tasks(self) -> list[CutTask]:
        """获取正在执行的任务"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]
    
    def clear_completed(self) -> int:
        """清除已完成的任务"""
        completed = [
            tid for tid, t in self.tasks.items()
            if t.status in [TaskStatus.DONE, TaskStatus.FAILED]
        ]
        for tid in completed:
            del self.tasks[tid]
        return len(completed)
    
    async def start_worker(self):
        """启动后台工作线程"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._run_worker())
    
    async def stop_worker(self):
        """停止后台工作线程"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
    
    async def _run_worker(self):
        """后台工作线程：执行队列中的任务"""
        ffmpeg = get_ffmpeg_service()
        
        while self._running:
            # 检查是否有空闲槽位
            running_count = len(self.get_running_tasks())
            if running_count >= self.max_concurrent:
                await asyncio.sleep(0.5)
                continue
            
            # 获取待执行任务
            pending = self.get_pending_tasks()
            if not pending:
                await asyncio.sleep(0.5)
                continue
            
            # 执行任务
            task = pending[0]
            await self._execute_task(task, ffmpeg)
    
    async def _execute_task(self, task: CutTask, ffmpeg):
        """执行单个切割任务"""
        from pathlib import Path
        from config import get_settings
        
        settings = get_settings()
        
        # 更新状态
        task.status = TaskStatus.RUNNING
        task.progress = 10
        
        try:
            # 生成输出路径
            input_path = Path(task.input_path)
            if task.output_name:
                output_name = f"{task.output_name}{input_path.suffix}"
            else:
                start_str = f"{int(task.start_time):04d}"
                end_str = f"{int(task.end_time):04d}"
                output_name = f"{input_path.stem}_{start_str}-{end_str}{input_path.suffix}"
            
            output_dir = Path(settings.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / output_name
            
            task.progress = 30
            
            # 执行切割
            success = await ffmpeg.cut_video(
                input_path=task.input_path,
                output_path=str(output_path),
                start_time=task.start_time,
                end_time=task.end_time,
                lossless=True,
            )
            
            if success:
                task.status = TaskStatus.DONE
                task.progress = 100
                task.output_path = str(output_path)
            else:
                task.status = TaskStatus.FAILED
                task.error = "FFmpeg 切割失败"
            
            task.completed_at = datetime.now()
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()


# 全局任务队列单例
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """获取任务队列单例"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
