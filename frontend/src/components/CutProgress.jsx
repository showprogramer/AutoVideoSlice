/**
 * 切割进度组件
 * 
 * 展示切割任务的进度和状态
 */

import { useState, useEffect } from 'react';
import './CutProgress.css';

// 状态配置
const STATUS_CONFIG = {
  pending: { label: '排队中', color: '#86868b', icon: '⏳' },
  running: { label: '进行中', color: '#0071e3', icon: '⚙️' },
  done: { label: '完成', color: '#34c759', icon: '✅' },
  failed: { label: '失败', color: '#ff3b30', icon: '❌' },
};

export function CutProgress({ onRefresh }) {
  const [tasks, setTasks] = useState([]);
  const [summary, setSummary] = useState({ total: 0, pending: 0, running: 0, done: 0, failed: 0 });
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 获取任务列表
  const fetchTasks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/video/tasks');
      const data = await response.json();
      if (data.success) {
        setTasks(data.tasks);
        setSummary(data.summary);
      }
    } catch (error) {
      console.error('获取任务失败:', error);
    }
  };

  // 自动刷新
  useEffect(() => {
    fetchTasks();
    
    if (autoRefresh) {
      const interval = setInterval(fetchTasks, 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // 清除已完成任务
  const handleClear = async () => {
    try {
      await fetch('http://localhost:8000/api/video/tasks/clear', { method: 'DELETE' });
      fetchTasks();
    } catch (error) {
      console.error('清除失败:', error);
    }
  };

  if (tasks.length === 0) {
    return null;
  }

  return (
    <div className="cut-progress">
      <div className="cut-progress__header">
        <h3>🎬 切割任务</h3>
        <div className="cut-progress__actions">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            自动刷新
          </label>
          <button className="btn btn-secondary" onClick={handleClear}>
            清除完成
          </button>
        </div>
      </div>

      {/* 统计摘要 */}
      <div className="cut-progress__summary">
        <span className="summary-item">
          总计: <strong>{summary.total}</strong>
        </span>
        <span className="summary-item pending">
          排队: <strong>{summary.pending}</strong>
        </span>
        <span className="summary-item running">
          执行: <strong>{summary.running}</strong>
        </span>
        <span className="summary-item done">
          完成: <strong>{summary.done}</strong>
        </span>
        {summary.failed > 0 && (
          <span className="summary-item failed">
            失败: <strong>{summary.failed}</strong>
          </span>
        )}
      </div>

      {/* 任务列表 */}
      <div className="cut-progress__list">
        {tasks.map((task) => {
          const config = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;
          
          return (
            <div key={task.id} className={`task-item task-item--${task.status}`}>
              <div className="task-item__info">
                <span className="task-item__icon">{config.icon}</span>
                <span className="task-item__time">{task.time_range}</span>
                <span className="task-item__duration">({task.duration.toFixed(1)}s)</span>
              </div>
              
              <div className="task-item__status">
                {task.status === 'running' ? (
                  <div className="task-item__progress">
                    <div 
                      className="task-item__progress-bar"
                      style={{ width: `${task.progress}%` }}
                    />
                    <span>{task.progress.toFixed(0)}%</span>
                  </div>
                ) : (
                  <span 
                    className="task-item__badge"
                    style={{ backgroundColor: config.color }}
                  >
                    {config.label}
                  </span>
                )}
              </div>
              
              {task.error && (
                <div className="task-item__error">{task.error}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default CutProgress;
