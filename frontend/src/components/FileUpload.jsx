/**
 * 文件上传组件
 * 支持拖拽上传视频和字幕文件
 */

import { useState, useRef } from 'react';
import './FileUpload.css';

export function FileUpload({ 
  accept = '*',
  label = '拖拽文件到此处',
  hint = '或点击选择文件',
  onFileSelect,
  disabled = false,
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const inputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileChange(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  };

  const handleInputChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileChange(files[0]);
    }
  };

  const handleFileChange = (file) => {
    setSelectedFile(file);
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleClear = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
    if (onFileSelect) {
      onFileSelect(null);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div
      className={`upload-zone ${isDragOver ? 'dragover' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleInputChange}
        style={{ display: 'none' }}
        disabled={disabled}
      />
      
      {selectedFile ? (
        <div className="upload-file-info">
          <div className="upload-file-icon">📄</div>
          <div className="upload-file-details">
            <span className="upload-file-name">{selectedFile.name}</span>
            <span className="upload-file-size">{formatFileSize(selectedFile.size)}</span>
          </div>
          <button 
            className="upload-file-clear" 
            onClick={handleClear}
            title="清除文件"
          >
            ✕
          </button>
        </div>
      ) : (
        <>
          <div className="upload-zone-icon">📁</div>
          <div className="upload-zone-text">{label}</div>
          <div className="upload-zone-hint">{hint}</div>
        </>
      )}
    </div>
  );
}

export default FileUpload;
