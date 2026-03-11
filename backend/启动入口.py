"""
启动入口模块

FastAPI 应用入口，负责创建 app 实例、注册路由、处理生命周期事件。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.路由注册 import 注册所有路由
from backend.models.数据库 import 初始化数据库, 关闭数据库
from backend.配置 import 配置实例


@asynccontextmanager
async def 生命周期(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化资源，关闭时清理资源。
    """
    # === 启动阶段 ===
    await 初始化数据库()

    # 初始化任务注册表
    from tasks.任务注册表 import 初始化任务注册表
    from browser.任务回调 import 设置回调地址
    from backend.services.心跳服务 import 心跳服务实例

    初始化任务注册表()

    if 配置实例.AGENT_CALLBACK_URL:
        设置回调地址(配置实例.AGENT_CALLBACK_URL)

    await 心跳服务实例.启动()

    print(f"[后端启动完成] 端口: {配置实例.BACKEND_PORT}")

    try:
        yield  # --- 应用运行中 ---
    finally:
        # === 关闭阶段 ===
        await 心跳服务实例.停止()
        await 关闭数据库()
        print("[后端已关闭]")


def 创建应用() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例

    返回:
        FastAPI: 配置完成的应用实例
    """
    app = FastAPI(
        title="抖店自动化工具",
        description="基于 Playwright 的电商自动化桌面应用后端",
        version="0.1.0",
        lifespan=生命周期,
        redirect_slashes=False,  # 禁用自动重定向，避免 POST/DELETE 请求 body 丢失
    )

    # --- CORS 中间件（允许前端跨域访问）---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # 局域网无鉴权，允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- 注册所有 API 路由 ---
    注册所有路由(app)

    return app


# 全局 app 实例（uvicorn 直接引用）
app = 创建应用()


# === 直接运行入口 ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.启动入口:app",
        host="0.0.0.0",
        port=配置实例.BACKEND_PORT,
        reload=True,
        loop="asyncio",  # 强制使用标准 asyncio 事件循环，兼容 Windows + Playwright
    )
