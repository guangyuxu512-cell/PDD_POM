"""
启动入口模块

FastAPI 应用入口，负责创建 app 实例、注册路由、处理生命周期事件。
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.router import 注册所有路由
from backend.models.database import 初始化数据库, 关闭数据库
from backend.config import 配置实例


后端保留路径 = ("/api", "/docs", "/redoc", "/openapi.json")


@asynccontextmanager
async def 生命周期(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化资源，关闭时清理资源。
    """
    # === 启动阶段 ===
    await 初始化数据库()

    # 初始化任务注册表
    from tasks.task_registry import 初始化任务注册表
    from browser.task_callback import 设置回调地址
    from backend.services.heartbeat_service import 心跳服务实例

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
    挂载前端静态资源(app)

    return app


def 获取前端构建目录() -> Path | None:
    """按运行模式解析前端构建目录。"""
    候选目录列表 = []

    if getattr(sys, "frozen", False):
        候选目录列表.append(Path(sys.executable).resolve().parent.parent / "frontend" / "dist")

    候选目录列表.append(Path(__file__).resolve().parent.parent / "frontend" / "dist")

    for 候选目录 in 候选目录列表:
        if 候选目录.exists():
            return 候选目录

    return None


def 是否后端保留路径(请求路径: str) -> bool:
    """判断路径是否应继续交由后端处理。"""
    标准路径 = f"/{请求路径.lstrip('/')}" if 请求路径 else "/"
    for 保留路径 in 后端保留路径:
        if 标准路径 == 保留路径 or 标准路径.startswith(f"{保留路径}/"):
            return True
    return False


def 挂载前端静态资源(app: FastAPI, 前端构建目录: Path | None = None) -> None:
    """在存在前端构建产物时挂载 SPA 静态资源。"""
    前端目录 = 前端构建目录 or 获取前端构建目录()
    if 前端目录 is None:
        return

    静态资源目录 = 前端目录 / "assets"
    if 静态资源目录.exists():
        app.mount("/assets", StaticFiles(directory=str(静态资源目录)), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def 提供单页应用(full_path: str):
        """所有非 API 路径统一回退到前端单页应用入口。"""
        if 是否后端保留路径(full_path):
            raise HTTPException(status_code=404, detail="Not Found")

        if full_path:
            目标文件 = (前端目录 / full_path).resolve()
            try:
                目标文件.relative_to(前端目录.resolve())
            except ValueError as 异常:
                raise HTTPException(status_code=404, detail="Not Found") from 异常

            if 目标文件.exists() and 目标文件.is_file():
                return FileResponse(str(目标文件))

        return FileResponse(str(前端目录 / "index.html"))


# 全局 app 实例（uvicorn 直接引用）
app = 创建应用()


# === 直接运行入口 ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=配置实例.BACKEND_PORT,
        reload=True,
        loop="asyncio",  # 强制使用标准 asyncio 事件循环，兼容 Windows + Playwright
    )
