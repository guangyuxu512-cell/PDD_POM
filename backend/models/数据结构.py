"""
数据结构模块

定义所有 Pydantic 模型，用于 API 请求和响应。
"""
from typing import Any, Optional, List, Dict
from datetime import datetime
from pydantic import AliasChoices, BaseModel, Field


# ==================== 统一响应 ====================

class 统一响应(BaseModel):
    """API 统一响应格式"""
    code: int = Field(description="状态码，0=成功，1=业务错误")
    data: Any = Field(default=None, description="响应数据")
    msg: str = Field(description="响应消息")


def 成功(data: Any = None, message: str = "ok") -> 统一响应:
    """
    构造成功响应

    参数:
        data: 响应数据
        message: 响应消息

    返回:
        统一响应: 成功响应对象
    """
    return 统一响应(code=0, data=data, msg=message)


def 失败(message: str, data: Any = None) -> 统一响应:
    """
    构造失败响应

    参数:
        message: 错误消息
        data: 额外数据

    返回:
        统一响应: 失败响应对象
    """
    return 统一响应(code=1, data=data, msg=message)


# ==================== 分页响应 ====================

class 分页响应(BaseModel):
    """分页响应格式"""
    list: List[Any] = Field(description="数据列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# ==================== 店铺相关模型 ====================

class 店铺创建请求(BaseModel):
    """创建店铺请求"""
    name: str = Field(description="店铺名称")
    username: Optional[str] = Field(default=None, description="登录用户名")
    password: Optional[str] = Field(default=None, description="登录密码")
    proxy: Optional[str] = Field(default=None, description="代理地址")
    user_agent: Optional[str] = Field(default=None, description="User-Agent")
    smtp_host: Optional[str] = Field(default=None, description="邮箱服务器地址")
    smtp_port: Optional[int] = Field(default=993, description="邮箱服务器端口")
    smtp_user: Optional[str] = Field(default=None, description="邮箱用户名")
    smtp_pass: Optional[str] = Field(default=None, description="邮箱密码")
    smtp_protocol: Optional[str] = Field(default="imap", description="邮箱协议")
    remark: Optional[str] = Field(default=None, description="备注")


class 店铺更新请求(BaseModel):
    """更新店铺请求"""
    name: Optional[str] = Field(default=None, description="店铺名称")
    username: Optional[str] = Field(default=None, description="登录用户名")
    password: Optional[str] = Field(default=None, description="登录密码")
    proxy: Optional[str] = Field(default=None, description="代理地址")
    user_agent: Optional[str] = Field(default=None, description="User-Agent")
    status: Optional[str] = Field(default=None, description="状态")
    smtp_host: Optional[str] = Field(default=None, description="邮箱服务器地址")
    smtp_port: Optional[int] = Field(default=None, description="邮箱服务器端口")
    smtp_user: Optional[str] = Field(default=None, description="邮箱用户名")
    smtp_pass: Optional[str] = Field(default=None, description="邮箱密码")
    smtp_protocol: Optional[str] = Field(default=None, description="邮箱协议")
    remark: Optional[str] = Field(default=None, description="备注")


class 店铺响应(BaseModel):
    """店铺响应"""
    id: str = Field(description="店铺ID")
    name: str = Field(description="店铺名称")
    username: Optional[str] = Field(default=None, description="登录用户名")
    password: Optional[str] = Field(default=None, description="登录密码（脱敏）")
    proxy: Optional[str] = Field(default=None, description="代理地址")
    user_agent: Optional[str] = Field(default=None, description="User-Agent")
    profile_dir: Optional[str] = Field(default=None, description="用户数据目录")
    cookie_path: Optional[str] = Field(default=None, description="Cookie文件路径")
    status: str = Field(description="状态")
    last_login: Optional[str] = Field(default=None, description="最后登录时间")
    smtp_host: Optional[str] = Field(default=None, description="邮箱服务器地址")
    smtp_port: Optional[int] = Field(default=None, description="邮箱服务器端口")
    smtp_user: Optional[str] = Field(default=None, description="邮箱用户名")
    smtp_protocol: Optional[str] = Field(default=None, description="邮箱协议")
    remark: Optional[str] = Field(default=None, description="备注")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


# ==================== 任务相关模型 ====================

class 任务执行请求(BaseModel):
    """执行任务请求"""
    shop_id: str = Field(description="店铺ID")
    task_name: str = Field(
        default="登录",
        description="任务名称",
        validation_alias=AliasChoices("task_name", "task_type")
    )
    params: Optional[Dict[str, Any]] = Field(default=None, description="任务参数")


class 任务日志响应(BaseModel):
    """任务日志响应"""
    id: int = Field(description="日志ID")
    task_id: str = Field(description="任务ID")
    shop_id: Optional[str] = Field(default=None, description="店铺ID")
    task_name: str = Field(description="任务名称")
    status: str = Field(description="状态")
    params: Optional[str] = Field(default=None, description="任务参数")
    result: Optional[str] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    screenshot: Optional[str] = Field(default=None, description="截图路径")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    finished_at: Optional[str] = Field(default=None, description="结束时间")
    created_at: Optional[str] = Field(default=None, description="创建时间")


class 流程创建请求(BaseModel):
    """创建流程请求"""
    name: str = Field(description="流程名称")
    steps: Any = Field(description="流程步骤，支持 JSON 数组或 JSON 字符串")
    description: Optional[str] = Field(default=None, description="流程描述")


class 流程更新请求(BaseModel):
    """更新流程请求"""
    name: Optional[str] = Field(default=None, description="流程名称")
    steps: Optional[Any] = Field(default=None, description="流程步骤，支持 JSON 数组或 JSON 字符串")
    description: Optional[str] = Field(default=None, description="流程描述")


class 流程响应(BaseModel):
    """流程响应"""
    id: str = Field(description="流程ID")
    name: str = Field(description="流程名称")
    steps: List[Dict[str, Any]] = Field(description="流程步骤")
    description: Optional[str] = Field(default=None, description="流程描述")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class 批量执行请求(BaseModel):
    """批量执行请求"""
    flow_id: Optional[str] = Field(default=None, description="流程 ID")
    task_name: Optional[str] = Field(default=None, description="单任务名称")
    shop_ids: List[str] = Field(description="店铺 ID 列表")
    concurrency: int = Field(default=1, ge=1, description="请求并发数，仅记录用途")
    callback_url: Optional[str] = Field(default=None, description="批次完成回调地址（可选）")


class 任务参数创建请求(BaseModel):
    """创建任务参数请求"""
    shop_id: str = Field(description="店铺ID")
    task_name: str = Field(description="任务名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    status: str = Field(default="pending", description="执行状态")
    result: Dict[str, Any] = Field(default_factory=dict, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    enabled: bool = Field(default=True, description="是否启用")


class 任务参数更新请求(BaseModel):
    """更新任务参数请求"""
    shop_id: Optional[str] = Field(default=None, description="店铺ID")
    task_name: Optional[str] = Field(default=None, description="任务名称")
    params: Optional[Dict[str, Any]] = Field(default=None, description="任务参数")
    status: Optional[str] = Field(default=None, description="执行状态")
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    enabled: Optional[bool] = Field(default=None, description="是否启用")


class 任务参数批量操作请求(BaseModel):
    """任务参数批量操作请求"""
    shop_id: Optional[str] = Field(default=None, description="店铺ID")
    task_name: Optional[str] = Field(default=None, description="任务名称")
    status: Optional[str] = Field(default=None, description="状态")
    batch_id: Optional[str] = Field(default=None, description="批次ID")


class 任务参数响应(BaseModel):
    """任务参数响应"""
    id: int = Field(description="主键ID")
    shop_id: str = Field(description="店铺ID")
    shop_name: Optional[str] = Field(default=None, description="店铺名称")
    task_name: str = Field(description="任务名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    status: str = Field(description="执行状态")
    result: Dict[str, Any] = Field(default_factory=dict, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    enabled: bool = Field(description="是否启用")
    run_count: int = Field(description="执行次数")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class 流程参数创建请求(BaseModel):
    """创建流程参数请求"""
    shop_id: str = Field(description="店铺ID")
    flow_id: str = Field(description="流程ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="共享参数")
    step_results: Dict[str, Any] = Field(default_factory=dict, description="步骤结果")
    current_step: int = Field(default=0, description="当前步骤索引")
    status: str = Field(default="pending", description="执行状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    enabled: bool = Field(default=True, description="是否启用")


class 流程参数更新请求(BaseModel):
    """更新流程参数请求"""
    shop_id: Optional[str] = Field(default=None, description="店铺ID")
    flow_id: Optional[str] = Field(default=None, description="流程ID")
    params: Optional[Dict[str, Any]] = Field(default=None, description="共享参数")
    step_results: Optional[Dict[str, Any]] = Field(default=None, description="步骤结果")
    current_step: Optional[int] = Field(default=None, description="当前步骤索引")
    status: Optional[str] = Field(default=None, description="执行状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    enabled: Optional[bool] = Field(default=None, description="是否启用")


class 流程参数导入请求(BaseModel):
    """流程参数导入请求"""
    flow_id: str = Field(description="流程ID")


class 流程参数批量操作请求(BaseModel):
    """流程参数批量操作请求"""
    shop_id: Optional[str] = Field(default=None, description="店铺ID")
    flow_id: Optional[str] = Field(default=None, description="流程ID")
    status: Optional[str] = Field(default=None, description="状态")
    batch_id: Optional[str] = Field(default=None, description="批次ID")


class 流程参数响应(BaseModel):
    """流程参数响应"""
    id: int = Field(description="主键ID")
    shop_id: str = Field(description="店铺ID")
    shop_name: Optional[str] = Field(default=None, description="店铺名称")
    flow_id: str = Field(description="流程ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="共享参数")
    step_results: Dict[str, Any] = Field(default_factory=dict, description="步骤结果")
    current_step: int = Field(description="当前步骤索引")
    status: str = Field(description="执行状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    batch_id: Optional[str] = Field(default=None, description="批次ID")
    enabled: bool = Field(description="是否启用")
    run_count: int = Field(description="执行次数")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class 停止执行请求(BaseModel):
    """停止执行请求"""
    batch_id: Optional[str] = Field(default=None, description="批次 ID，不传则停止当前批次")


class 定时任务创建请求(BaseModel):
    """创建定时任务请求"""
    name: str = Field(description="计划名称")
    flow_id: str = Field(description="流程 ID")
    shop_ids: List[str] = Field(description="店铺 ID 列表")
    concurrency: int = Field(default=1, ge=1, description="并发数")
    interval_seconds: Optional[int] = Field(default=None, ge=1, description="固定间隔秒数")
    cron_expr: Optional[str] = Field(default=None, description="Cron 表达式")
    overlap_policy: str = Field(default="wait", description="重叠执行策略")


class 定时任务更新请求(BaseModel):
    """更新定时任务请求"""
    name: Optional[str] = Field(default=None, description="计划名称")
    flow_id: Optional[str] = Field(default=None, description="流程 ID")
    shop_ids: Optional[List[str]] = Field(default=None, description="店铺 ID 列表")
    concurrency: Optional[int] = Field(default=None, ge=1, description="并发数")
    interval_seconds: Optional[int] = Field(default=None, ge=1, description="固定间隔秒数")
    cron_expr: Optional[str] = Field(default=None, description="Cron 表达式")
    overlap_policy: Optional[str] = Field(default=None, description="重叠执行策略")


class 定时任务响应(BaseModel):
    """定时任务响应"""
    id: str = Field(description="计划 ID")
    name: str = Field(description="计划名称")
    flow_id: str = Field(description="流程 ID")
    shop_ids: List[str] = Field(description="店铺 ID 列表")
    concurrency: int = Field(description="并发数")
    interval_seconds: Optional[int] = Field(default=None, description="固定间隔秒数")
    cron_expr: Optional[str] = Field(default=None, description="Cron 表达式")
    overlap_policy: str = Field(description="重叠执行策略")
    enabled: bool = Field(description="是否启用")
    last_run_at: Optional[str] = Field(default=None, description="上次运行时间")
    next_run_at: Optional[str] = Field(default=None, description="下次运行时间")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


# ==================== Cookie 相关模型 ====================

class Cookie导入请求(BaseModel):
    """导入 Cookie 请求"""
    shop_id: str = Field(description="店铺ID")
    cookie_data: str = Field(description="Cookie 数据（JSON 字符串）")


# ==================== 浏览器相关模型 ====================

class 浏览器初始化配置(BaseModel):
    """浏览器初始化配置"""
    max_instances: int = Field(default=3, description="最大实例数")
    chrome_path: Optional[str] = Field(default=None, description="Chrome 路径")
    default_proxy: Optional[str] = Field(default=None, description="默认代理")


class 浏览器实例响应(BaseModel):
    """浏览器实例响应"""
    instance_id: str = Field(description="实例ID")
    shop_id: str = Field(description="店铺ID")
    shop_name: str = Field(description="店铺名称")
    status: str = Field(description="状态")
    uptime: int = Field(description="运行时长（秒）")
    memory: int = Field(description="内存占用（MB）")
    cpu: float = Field(description="CPU 占用（%）")


# ==================== 日志相关模型 ====================

class 操作日志响应(BaseModel):
    """操作日志响应"""
    id: int = Field(description="日志ID")
    shop_id: Optional[str] = Field(default=None, description="店铺ID")
    level: str = Field(description="日志级别")
    source: Optional[str] = Field(default=None, description="来源")
    message: str = Field(description="日志消息")
    detail: Optional[str] = Field(default=None, description="详细信息")
    created_at: Optional[str] = Field(default=None, description="创建时间")


# ==================== 系统相关模型 ====================

class 系统配置请求(BaseModel):
    """系统配置请求"""
    redis_url: Optional[str] = Field(default=None, description="Redis 连接地址")
    max_browser_instances: Optional[int] = Field(default=None, description="最大浏览器实例数")
    chrome_path: Optional[str] = Field(default=None, description="Chrome 路径")
    default_proxy: Optional[str] = Field(default=None, description="默认代理")
    captcha_service: Optional[str] = Field(default=None, description="验证码服务商")
    captcha_api_key: Optional[str] = Field(default=None, description="验证码 API 密钥")


class Redis连接测试请求(BaseModel):
    """Redis 连接测试请求"""
    redis_url: Optional[str] = Field(default=None, description="Redis 连接地址")


class 系统配置响应(BaseModel):
    """系统配置响应"""
    redis_url: str = Field(description="Redis 连接地址")
    max_browser_instances: int = Field(description="最大浏览器实例数")
    chrome_path: Optional[str] = Field(default=None, description="Chrome 路径")
    default_proxy: Optional[str] = Field(default=None, description="默认代理")
    captcha_service: str = Field(description="验证码服务商")
    captcha_api_key: Optional[str] = Field(default=None, description="验证码 API 密钥")


class 健康检查响应(BaseModel):
    """健康检查响应"""
    status: str = Field(description="状态")
    redis: bool = Field(description="Redis 连接状态")
    database: bool = Field(description="数据库连接状态")
    browser: bool = Field(description="浏览器可用状态")
