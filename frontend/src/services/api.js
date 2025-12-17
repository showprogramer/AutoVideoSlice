/**
 * API 服务层
 * 封装后端 API 调用
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * 通用请求函数
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    ...options,
    headers: {
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || data.message || '请求失败');
    }
    
    return data;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * 健康检查
 */
export async function checkHealth() {
  return request('/health');
}

/**
 * 上传并解析字幕文件
 */
export async function uploadSubtitle(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  return request('/api/subtitle/upload', {
    method: 'POST',
    body: formData,
  });
}

/**
 * 解析字幕内容
 */
export async function parseSubtitle(content, filename) {
  return request('/api/subtitle/parse', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content, filename }),
  });
}

/**
 * 获取支持的字幕格式
 */
export async function getSubtitleFormats() {
  return request('/api/subtitle/formats');
}

/**
 * 分析字幕内容
 */
export async function analyzeContent(subtitleText, options = {}) {
  return request('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      subtitle_text: subtitleText,
      video_duration: options.videoDuration,
      max_highlights: options.maxHighlights || 10,
      min_segment_duration: options.minDuration || 15,
      max_segment_duration: options.maxDuration || 120,
      generate_titles: options.generateTitles !== false,
    }),
  });
}

/**
 * 评分单个片段
 */
export async function scoreSegment(segment) {
  return request('/api/score', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(segment),
  });
}

/**
 * 批量评分
 */
export async function scoreBatch(segments) {
  return request('/api/score/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ segments }),
  });
}

/**
 * API 服务对象
 */
export const api = {
  checkHealth,
  subtitle: {
    upload: uploadSubtitle,
    parse: parseSubtitle,
    getFormats: getSubtitleFormats,
  },
  analyze: {
    content: analyzeContent,
  },
  score: {
    single: scoreSegment,
    batch: scoreBatch,
  },
};

export default api;

