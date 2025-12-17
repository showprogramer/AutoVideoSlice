/**
 * AutoVideoSlice 主应用
 */

import { useState } from 'react';
import { Layout } from './components/Layout';
import { FileUpload } from './components/FileUpload';
import { ScoreCard } from './components/ScoreCard';
import { CutProgress } from './components/CutProgress';
import { ExportPanel } from './components/ExportPanel';
import { api } from './services/api';
import './App.css';

// 演示用的模拟评分数据
const DEMO_SCORES = [
  {
    total_score: 8.5,
    recommendation: 'excellent',
    summary: '优质片段，强烈推荐发布',
    dimensions: [
      { name: 'virality', score: 9.0, weight: 0.3, description: '包含多个爆款关键词' },
      { name: 'emotion', score: 8.5, weight: 0.25, description: '情感类内容，感染力强' },
      { name: 'density', score: 8.0, weight: 0.25, description: '时长最优(30-90秒)、信息点丰富' },
      { name: 'completeness', score: 8.0, weight: 0.2, description: '时长充足、内容描述完整' },
    ],
  },
  {
    total_score: 6.2,
    recommendation: 'good',
    summary: '质量良好，可以考虑发布',
    dimensions: [
      { name: 'virality', score: 6.0, weight: 0.3, description: '传播力一般' },
      { name: 'emotion', score: 7.0, weight: 0.25, description: '幽默内容，易传播' },
      { name: 'density', score: 5.5, weight: 0.25, description: '时长稍短' },
      { name: 'completeness', score: 6.5, weight: 0.2, description: '时长基本够用' },
    ],
  },
  {
    total_score: 4.5,
    recommendation: 'fair',
    summary: '质量一般，建议优化后发布',
    dimensions: [
      { name: 'virality', score: 4.0, weight: 0.3, description: '传播力一般' },
      { name: 'emotion', score: 5.0, weight: 0.25, description: '情感表达适中' },
      { name: 'density', score: 4.5, weight: 0.25, description: '时长过长，可能拖沓' },
      { name: 'completeness', score: 5.0, weight: 0.2, description: '完整性待验证' },
    ],
  },
];

function App() {
  const [subtitleFile, setSubtitleFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [subtitleData, setSubtitleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDemo, setShowDemo] = useState(false);

  const handleSubtitleSelect = async (file) => {
    setSubtitleFile(file);
    setError(null);
    setSubtitleData(null);

    if (!file) return;

    setLoading(true);
    try {
      const result = await api.subtitle.upload(file);
      if (result.success) {
        setSubtitleData(result.data);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(err.message || '解析字幕失败');
    } finally {
      setLoading(false);
    }
  };

  const handleVideoSelect = (file) => {
    setVideoFile(file);
  };

  return (
    <Layout>
      <div className="home">
        <section className="hero">
          <h1>智能视频剪辑助手</h1>
          <p className="hero-subtitle">
            上传视频和字幕，AI 自动提取高光片段，生成爆款标题
          </p>
        </section>

        <section className="upload-section">
          <div className="upload-grid">
            <div className="upload-item">
              <h3>📹 视频文件</h3>
              <FileUpload
                accept="video/*"
                label="拖拽视频到此处"
                hint="支持 MP4, MKV, AVI 等格式"
                onFileSelect={handleVideoSelect}
              />
            </div>
            
            <div className="upload-item">
              <h3>📝 字幕文件</h3>
              <FileUpload
                accept=".srt,.vtt"
                label="拖拽字幕到此处"
                hint="支持 SRT, VTT 格式"
                onFileSelect={handleSubtitleSelect}
                disabled={loading}
              />
            </div>
          </div>

          {loading && (
            <div className="status-bar">
              <div className="spinner"></div>
              <span>正在解析字幕...</span>
            </div>
          )}

          {error && (
            <div className="status-bar error">
              <span>❌ {error}</span>
            </div>
          )}

          {/* 状态和操作区 */}
          <div className="status-action-bar">
            <div className="file-status">
              {videoFile && (
                <span className="status-item success">✅ 视频已选择</span>
              )}
              {subtitleData && (
                <span className="status-item success">
                  ✅ 字幕已解析 ({subtitleData.entries.length} 条，{Math.floor(subtitleData.total_duration / 60)}:{String(Math.floor(subtitleData.total_duration % 60)).padStart(2, '0')})
                </span>
              )}
            </div>
            
            <button 
              className="btn btn-primary"
              disabled={!videoFile || !subtitleData}
            >
              🚀 开始分析
            </button>
          </div>
        </section>

        {/* 切割进度组件 */}
        <CutProgress />

        {/* 导出面板 */}
        <ExportPanel />

        {/* 评分组件演示区 */}
        <section className="demo-section">
          <div className="demo-header">
            <h2>🎯 评分组件演示</h2>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowDemo(!showDemo)}
            >
              {showDemo ? '隐藏演示' : '显示演示'}
            </button>
          </div>

          {showDemo && (
            <div className="score-demo-grid">
              {DEMO_SCORES.map((score, index) => (
                <div key={index} className="demo-item">
                  <h4>片段 {index + 1}</h4>
                  <ScoreCard score={score} />
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}

export default App;

