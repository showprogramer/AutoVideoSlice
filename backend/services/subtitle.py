"""
字幕解析服务

支持 SRT 和 VTT 格式的字幕解析。
"""

import re
from typing import Optional
from pathlib import Path

from models.subtitle import (
    SubtitleData,
    SubtitleEntry,
    SubtitleFormat,
)


class SubtitleParser:
    """字幕解析器基类"""
    
    def parse(self, content: str, filename: str) -> SubtitleData:
        """解析字幕内容"""
        raise NotImplementedError


class SRTParser(SubtitleParser):
    """SRT 格式解析器"""
    
    # SRT 时间戳格式: 00:00:00,000 --> 00:00:00,000
    TIME_PATTERN = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
    )
    
    def parse(self, content: str, filename: str) -> SubtitleData:
        """解析 SRT 格式字幕"""
        entries = []
        
        # 按空行分割字幕块
        blocks = re.split(r"\n\s*\n", content.strip())
        
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 2:
                continue
            
            # 解析序号
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue
            
            # 解析时间戳
            time_match = self.TIME_PATTERN.search(lines[1])
            if not time_match:
                continue
            
            start_time = self._parse_time(*time_match.groups()[:4])
            end_time = self._parse_time(*time_match.groups()[4:])
            
            # 解析文本（可能是多行）
            text = "\n".join(lines[2:]).strip()
            
            entries.append(SubtitleEntry(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text,
            ))
        
        # 计算总时长
        total_duration = entries[-1].end_time if entries else 0
        
        return SubtitleData(
            filename=filename,
            format=SubtitleFormat.SRT,
            entries=entries,
            total_duration=total_duration,
        )
    
    def _parse_time(self, h: str, m: str, s: str, ms: str) -> float:
        """将时间字符串转换为秒数"""
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


class VTTParser(SubtitleParser):
    """VTT 格式解析器"""
    
    # VTT 时间戳格式: 00:00:00.000 --> 00:00:00.000
    TIME_PATTERN = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    )
    
    # 简化格式: 00:00.000 --> 00:00.000
    SHORT_TIME_PATTERN = re.compile(
        r"(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2})\.(\d{3})"
    )
    
    def parse(self, content: str, filename: str) -> SubtitleData:
        """解析 VTT 格式字幕"""
        entries = []
        
        # 移除 WEBVTT 头部
        content = re.sub(r"^WEBVTT.*?\n", "", content, flags=re.MULTILINE)
        
        # 移除注释和样式
        content = re.sub(r"NOTE.*?\n\n", "", content, flags=re.DOTALL)
        content = re.sub(r"STYLE.*?\n\n", "", content, flags=re.DOTALL)
        
        # 按空行分割字幕块
        blocks = re.split(r"\n\s*\n", content.strip())
        
        index = 0
        for block in blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue
            
            # 查找时间戳行
            time_line_idx = 0
            for i, line in enumerate(lines):
                if "-->" in line:
                    time_line_idx = i
                    break
            else:
                continue
            
            # 解析时间戳
            time_line = lines[time_line_idx]
            time_match = self.TIME_PATTERN.search(time_line)
            
            if time_match:
                start_time = self._parse_time(*time_match.groups()[:4])
                end_time = self._parse_time(*time_match.groups()[4:])
            else:
                # 尝试简化格式
                short_match = self.SHORT_TIME_PATTERN.search(time_line)
                if short_match:
                    start_time = self._parse_short_time(*short_match.groups()[:3])
                    end_time = self._parse_short_time(*short_match.groups()[3:])
                else:
                    continue
            
            # 解析文本
            text_lines = lines[time_line_idx + 1:]
            text = "\n".join(text_lines).strip()
            
            # 移除 VTT 标签
            text = re.sub(r"<[^>]+>", "", text)
            
            if text:
                index += 1
                entries.append(SubtitleEntry(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                ))
        
        total_duration = entries[-1].end_time if entries else 0
        
        return SubtitleData(
            filename=filename,
            format=SubtitleFormat.VTT,
            entries=entries,
            total_duration=total_duration,
        )
    
    def _parse_time(self, h: str, m: str, s: str, ms: str) -> float:
        """将时间字符串转换为秒数"""
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    
    def _parse_short_time(self, m: str, s: str, ms: str) -> float:
        """解析简化格式时间"""
        return int(m) * 60 + int(s) + int(ms) / 1000


def detect_format(filename: str, content: Optional[str] = None) -> SubtitleFormat:
    """检测字幕格式"""
    ext = Path(filename).suffix.lower()
    
    if ext == ".srt":
        return SubtitleFormat.SRT
    elif ext in (".vtt", ".webvtt"):
        return SubtitleFormat.VTT
    elif content and content.strip().startswith("WEBVTT"):
        return SubtitleFormat.VTT
    
    return SubtitleFormat.UNKNOWN


def parse_subtitle(content: str, filename: str) -> SubtitleData:
    """解析字幕文件（自动检测格式）"""
    format_type = detect_format(filename, content)
    
    if format_type == SubtitleFormat.SRT:
        parser = SRTParser()
    elif format_type == SubtitleFormat.VTT:
        parser = VTTParser()
    else:
        raise ValueError(f"不支持的字幕格式: {filename}")
    
    return parser.parse(content, filename)
