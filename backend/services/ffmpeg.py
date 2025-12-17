"""
FFmpeg 工具服务

封装 FFmpeg 操作，包含检测、下载、视频处理等功能。
"""

import os
import subprocess
import shutil
import json
import asyncio
import zipfile
import httpx
from pathlib import Path
from typing import Optional, Tuple

from config import get_settings
from models.video import VideoInfo, FFmpegStatus


class FFmpegService:
    """FFmpeg 工具服务"""
    
    # FFmpeg 下载 URL (Windows)
    FFMPEG_DOWNLOAD_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    def __init__(self):
        self.settings = get_settings()
        self._ffmpeg_path: Optional[str] = None
        self._ffprobe_path: Optional[str] = None
    
    async def check_availability(self) -> FFmpegStatus:
        """
        检查 FFmpeg 是否可用
        """
        path = await self._find_ffmpeg()
        
        if path:
            version = await self._get_version(path)
            return FFmpegStatus(
                available=True,
                path=path,
                version=version,
                message="FFmpeg 已就绪",
            )
        else:
            return FFmpegStatus(
                available=False,
                path=None,
                version=None,
                message="FFmpeg 未安装，需要下载",
            )
    
    async def ensure_installed(self) -> str:
        """
        确保 FFmpeg 已安装，未安装则下载
        
        Returns:
            FFmpeg 可执行文件路径
        """
        # 先检查是否已有
        path = await self._find_ffmpeg()
        if path:
            return path
        
        # 下载并安装
        download_dir = Path(self.settings.ffmpeg_download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = download_dir / "ffmpeg.zip"
        
        # 下载
        await self._download_ffmpeg(str(zip_path))
        
        # 解压
        await self._extract_ffmpeg(str(zip_path), str(download_dir))
        
        # 查找可执行文件
        path = await self._find_in_dir(str(download_dir))
        if path:
            self._ffmpeg_path = path
            return path
        
        raise RuntimeError("FFmpeg 下载后未找到可执行文件")
    
    async def get_video_info(self, video_path: str) -> VideoInfo:
        """
        获取视频信息
        
        使用 ffprobe 读取视频元数据。
        """
        # 先检查 FFmpeg 是否可用
        status = await self.check_availability()
        if not status.available:
            raise RuntimeError("FFmpeg 未安装，请先调用 /api/video/ffmpeg-install 安装")
        
        ffprobe = await self._get_ffprobe()
        
        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]
        
        # 使用 encoding='utf-8' 来正确处理中文路径
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace',
            )
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe 执行失败: {result.stderr or '未知错误'}")
        
        # 检查输出是否为空
        if not result.stdout or not result.stdout.strip():
            raise RuntimeError("ffprobe 返回空结果，请检查视频文件是否有效")
        
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"ffprobe 输出解析失败: {str(e)}")
        
        # 解析视频流
        video_stream = None
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream
        
        format_info = data.get("format", {})
        
        # 构建 VideoInfo
        path = Path(video_path)
        return VideoInfo(
            path=video_path,
            filename=path.name,
            duration=float(format_info.get("duration", 0)),
            width=int(video_stream.get("width", 0)) if video_stream else 0,
            height=int(video_stream.get("height", 0)) if video_stream else 0,
            codec=video_stream.get("codec_name", "") if video_stream else "",
            audio_codec=audio_stream.get("codec_name", "") if audio_stream else "",
            bitrate=int(format_info.get("bit_rate", 0)),
            fps=self._parse_fps(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0,
            size_bytes=int(format_info.get("size", 0)),
        )
    
    async def cut_video(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        lossless: bool = True,
    ) -> bool:
        """
        切割视频
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            lossless: 是否无损切割
            
        Returns:
            是否成功
        """
        ffmpeg = await self._get_ffmpeg()
        duration = end_time - start_time
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if lossless:
            # 无损切割 - 使用 -c copy
            cmd = [
                ffmpeg,
                "-y",  # 覆盖输出文件
                "-ss", str(start_time),
                "-i", input_path,
                "-t", str(duration),
                "-c", "copy",  # 无损复制
                "-avoid_negative_ts", "1",
                output_path,
            ]
        else:
            # 重新编码
            cmd = [
                ffmpeg,
                "-y",
                "-ss", str(start_time),
                "-i", input_path,
                "-t", str(duration),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                output_path,
            ]
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True)
        )
        
        return result.returncode == 0
    
    async def generate_thumbnail(
        self,
        video_path: str,
        output_path: str,
        time: float,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> bool:
        """
        生成缩略图
        
        Args:
            video_path: 视频路径
            output_path: 输出图片路径
            time: 截取时间点（秒）
            width: 缩略图宽度
            height: 缩略图高度
        """
        ffmpeg = await self._get_ffmpeg()
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            ffmpeg,
            "-y",
            "-ss", str(time),
            "-i", video_path,
            "-vframes", "1",
        ]
        
        # 添加缩放参数
        if width or height:
            scale = f"scale={width or -1}:{height or -1}"
            cmd.extend(["-vf", scale])
        
        cmd.append(output_path)
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True)
        )
        
        return result.returncode == 0
    
    async def _find_ffmpeg(self) -> Optional[str]:
        """查找 FFmpeg 可执行文件"""
        # 1. 检查配置的路径
        if self.settings.ffmpeg_path:
            if os.path.isfile(self.settings.ffmpeg_path):
                return self.settings.ffmpeg_path
        
        # 2. 检查缓存
        if self._ffmpeg_path and os.path.isfile(self._ffmpeg_path):
            return self._ffmpeg_path
        
        # 3. 检查系统 PATH
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            self._ffmpeg_path = ffmpeg
            return ffmpeg
        
        # 4. 检查下载目录
        download_dir = self.settings.ffmpeg_download_dir
        if os.path.isdir(download_dir):
            path = await self._find_in_dir(download_dir)
            if path:
                self._ffmpeg_path = path
                return path
        
        return None
    
    async def _get_ffmpeg(self) -> str:
        """获取 FFmpeg 路径，不存在则抛出异常"""
        path = await self._find_ffmpeg()
        if not path:
            raise RuntimeError("FFmpeg 未安装，请先调用 ensure_installed()")
        return path
    
    async def _get_ffprobe(self) -> str:
        """获取 ffprobe 路径"""
        if self._ffprobe_path:
            return self._ffprobe_path
        
        ffmpeg = await self._get_ffmpeg()
        ffmpeg_dir = os.path.dirname(ffmpeg)
        
        # ffprobe 通常和 ffmpeg 在同一目录
        if os.name == "nt":
            ffprobe = os.path.join(ffmpeg_dir, "ffprobe.exe")
        else:
            ffprobe = os.path.join(ffmpeg_dir, "ffprobe")
        
        if os.path.isfile(ffprobe):
            self._ffprobe_path = ffprobe
            return ffprobe
        
        # 尝试系统 PATH
        ffprobe = shutil.which("ffprobe")
        if ffprobe:
            self._ffprobe_path = ffprobe
            return ffprobe
        
        raise RuntimeError("ffprobe 未找到")
    
    async def _find_in_dir(self, directory: str) -> Optional[str]:
        """在目录中查找 FFmpeg"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file in ["ffmpeg", "ffmpeg.exe"]:
                    return os.path.join(root, file)
        return None
    
    async def _get_version(self, ffmpeg_path: str) -> Optional[str]:
        """获取 FFmpeg 版本"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [ffmpeg_path, "-version"],
                    capture_output=True,
                    text=True,
                )
            )
            if result.returncode == 0:
                first_line = result.stdout.split("\n")[0]
                return first_line
        except Exception:
            pass
        return None
    
    async def _download_ffmpeg(self, zip_path: str) -> None:
        """下载 FFmpeg"""
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.get(self.FFMPEG_DOWNLOAD_URL, follow_redirects=True)
            response.raise_for_status()
            
            with open(zip_path, "wb") as f:
                f.write(response.content)
    
    async def _extract_ffmpeg(self, zip_path: str, extract_dir: str) -> None:
        """解压 FFmpeg"""
        def extract():
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            # 删除 zip 文件
            os.remove(zip_path)
        
        await asyncio.get_event_loop().run_in_executor(None, extract)
    
    def _parse_fps(self, fps_str: str) -> float:
        """解析帧率字符串 (如 '30/1')"""
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/")
                return float(num) / float(den)
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 0.0


# 单例
_ffmpeg_service: Optional[FFmpegService] = None


def get_ffmpeg_service() -> FFmpegService:
    """获取 FFmpeg 服务单例"""
    global _ffmpeg_service
    if _ffmpeg_service is None:
        _ffmpeg_service = FFmpegService()
    return _ffmpeg_service
