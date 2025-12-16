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
 * API 服务对象
 */
export const api = {
  checkHealth,
  subtitle: {
    upload: uploadSubtitle,
    parse: parseSubtitle,
    getFormats: getSubtitleFormats,
  },
};

export default api;
