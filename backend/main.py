"""
FastAPI 应用入口

注册路由、中间件和应用配置。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="智能视频剪辑助手 API",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    register_routes(app)
    
    return app


def register_routes(app: FastAPI) -> None:
    """注册所有路由"""
    
    # 注册 API 路由
    from api.subtitle import router as subtitle_router
    from api.ai import router as ai_router
    from api.analyze import router as analyze_router
    from api.score import router as score_router
    from api.video import router as video_router
    from api.export import router as export_router
    
    app.include_router(subtitle_router)
    app.include_router(ai_router)
    app.include_router(analyze_router)
    app.include_router(score_router)
    app.include_router(video_router)
    app.include_router(export_router)
    
    @app.get("/health", tags=["系统"])
    async def health_check():
        """
        健康检查接口
        
        返回服务运行状态，用于监控和负载均衡器健康检查。
        """
        settings = get_settings()
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }
    
    @app.get("/", tags=["系统"])
    async def root():
        """API 根路径"""
        return {
            "message": "欢迎使用 AutoVideoSlice API",
            "docs": "/docs",
        }


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
