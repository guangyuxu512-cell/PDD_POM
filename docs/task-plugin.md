# 新增任务标准模板

## 目标

新增任务时，默认只需要新增一个 `tasks/xxx任务.py` 文件，其它注册、发现、Schema 暴露和预检校验能力由任务注册表自动处理。

## 标准写法

1. 在 `tasks/` 目录下新建 `xxx任务.py`
2. 按需定义输入 Schema
3. 使用 `@register_task(...)` 注册任务
4. 继承 `基础任务` 并实现 `执行()` 方法
5. 保持页面选择器仍放在 `pages/`，不要写进 Task

## 示例

```python
from pydantic import BaseModel, Field

from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


class 示例任务输入(BaseModel):
    shop_id: str = Field(..., description="店铺 ID")


@register_task(
    "示例任务",
    "示例说明",
    category="示例",
    tags=["示例"],
    input_schema=示例任务输入,
    timeout=1800,
)
class 示例任务(基础任务):
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        return "ok"
```

## 装饰器参数

- `requires_input`: 是否依赖外部输入
- `required_fields`: 必填字段列表；未传且声明 `input_schema` 时会自动推导
- `supports_empty_context`: 是否允许空上下文执行
- `input_schema`: 输入参数的 Pydantic 模型
- `output_schema`: 输出结果的 Pydantic 模型
- `category`: 任务分类
- `tags`: 任务标签
- `timeout`: 超时秒数
- `retry_policy`: 重试策略配置

## 自动化能力

- `GET /api/task-registry/` 可发现所有已注册任务与输入 Schema
- `GET /api/task-registry/{task_name}/schema` 可读取单任务 Schema
- `POST /api/task-registry/{task_name}/validate` 可提前校验参数
- 流程预检会自动复用 `input_schema` 做参数校验
