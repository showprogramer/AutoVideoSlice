/**
 * 导出面板组件
 * 
 * 展示已完成的切割任务和下载选项
 */

import { useState, useEffect } from 'react';
import './ExportPanel.css';

export function ExportPanel() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [packaging, setPackaging] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);

  // 获取已完成视频列表
  const fetchVideos = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/export/collection');
      const data = await response.json();
      if (data.success) {
        setVideos(data.videos);
      }
    } catch (error) {
      console.error('获取视频列表失败:', error);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  // 切换选择
  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  };

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedIds.length === videos.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(videos.map(v => v.id));
    }
  };

  // 下载单个视频
  const handleDownload = (video) => {
    window.open(`http://localhost:8000${video.download_url}`, '_blank');
  };

  // 打包下载
  const handlePackage = async () => {
    if (selectedIds.length === 0) return;
    
    setPackaging(true);
    try {
      const response = await fetch('http://localhost:8000/api/export/package', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_ids: selectedIds }),
      });
      const data = await response.json();
      
      if (data.success && data.download_url) {
        window.open(`http://localhost:8000${data.download_url}`, '_blank');
      }
    } catch (error) {
      console.error('打包失败:', error);
    } finally {
      setPackaging(false);
    }
  };

  if (videos.length === 0) {
    return null;
  }

  return (
    <div className="export-panel">
      <div className="export-panel__header">
        <h3>📦 导出中心</h3>
        <div className="export-panel__actions">
          <button 
            className="btn btn-secondary"
            onClick={toggleSelectAll}
          >
            {selectedIds.length === videos.length ? '取消全选' : '全选'}
          </button>
          <button 
            className="btn btn-primary"
            disabled={selectedIds.length === 0 || packaging}
            onClick={handlePackage}
          >
            {packaging ? '打包中...' : `打包下载 (${selectedIds.length})`}
          </button>
        </div>
      </div>

      <div className="export-panel__list">
        {videos.map((video) => (
          <div 
            key={video.id} 
            className={`export-item ${selectedIds.includes(video.id) ? 'export-item--selected' : ''}`}
          >
            <label className="export-item__checkbox">
              <input 
                type="checkbox"
                checked={selectedIds.includes(video.id)}
                onChange={() => toggleSelect(video.id)}
              />
            </label>
            
            <div className="export-item__info">
              <span className="export-item__name">{video.filename}</span>
              <span className="export-item__meta">
                {video.time_range} · {video.duration.toFixed(1)}s
              </span>
            </div>
            
            <button 
              className="btn btn-secondary export-item__download"
              onClick={() => handleDownload(video)}
            >
              下载
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ExportPanel;
