/**
 * AutoVideoSlice 主应用
 */

import { useState } from 'react';
import { Layout } from './components/Layout';
import { FileUpload } from './components/FileUpload';
import { api } from './services/api';
import './App.css';

function App() {
  const [subtitleFile, setSubtitleFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [subtitleData, setSubtitleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
