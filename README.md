# AutoVideoSlice

一个本地优先、快速高效的视频智能剪辑助手，帮助内容创作者从长视频中自动提取精华片段。

## 功能特性

- 📹 视频与字幕导入
- 🤖 AI 内容高光提取
- 📝 爆款标题生成
- ✂️ 智能视频切割
- ⭐ 视频质量评分
- 📤 灵活导出（单个/合集）

## 技术栈

- **前端**: React + Vite
- **后端**: Python + FastAPI
- **AI 模型**: 豆包 doubao-1.5-pro-32k (云端) / Ollama qwen3:4b (本地)
- **视频处理**: FFmpeg

## 快速开始

### 后端

```powershell
cd backend
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -e .
python -m uvicorn main:app --reload
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

## 项目结构

```
AutoVideoSlice/
├── frontend/           # 前端代码 (React + Vite)
├── backend/            # 后端代码 (Python + FastAPI)
├── specs/              # 规格文档
└── output/             # 导出目录
```

## 文档

- [需求文档](specs/requirements.md)
- [技术方案](specs/plan.md)
- [任务分解](specs/tasks.md)
- [开发进度](specs/progress.md)

## License

MIT
