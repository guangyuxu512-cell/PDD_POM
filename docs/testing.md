# 测试策略

## 1. 测试框架

- `pytest`
- `pytest-asyncio`

## 2. 配置文件

- 测试配置位于 `tests/pytest.ini`
- 当前关键配置：
  - `asyncio_mode = auto`
  - `python_files = test_*.py 测试_*.py`
  - `python_classes = Test* 测试_*`

## 3. 当前测试目录

```text
tests/
├─ unit/          # 当前主测试目录
├─ 单元测试/       # 历史中文测试目录，仍保留部分回归
├─ conftest.py
└─ pytest.ini
```

说明：

- 当前新增测试主要落在 `tests/unit/`
- `tests/单元测试/` 仍有历史回归测试，短期内需要兼容
- 当前项目暂无独立的端到端集成测试目录

## 4. 当前覆盖范围

- FastAPI API 与 service 层回归
- Celery / Worker / Redis 相关桥接逻辑
- 浏览器管理、恢复、回调和页面对象
- 流程参数、流程输入、批量执行、运行监控
- 前端静态结构回归
- 打包、运行时路径和脚本回归

## 5. 测试文件命名与风格

- 测试文件命名遵循：
  - `test_*.py`
  - `测试_*.py`
- 新增功能或修复缺陷时，优先补针对性回归测试
- 当代码修改位于兼容层或历史模块时，也要检查对应旧目录测试是否仍覆盖到

## 6. 当前测试结构特点

- `tests/unit/`
  - 是当前主要增量测试目录
  - 覆盖 API、service、task、frontend static、打包和脚本
- `tests/单元测试/`
  - 保留历史中文命名测试文件
  - 对旧模块和部分兼容路径仍有保护作用
- 前端测试
  - 目前以 Python 静态断言和构建回归为主
  - 当前没有独立的浏览器 E2E 测试体系

## 7. 常用命令

- 运行全部测试：

```bash
python -m pytest -c tests/pytest.ini -q
```

- 运行指定目录：

```bash
python -m pytest tests/unit -q
```

- 前端构建回归：

```bash
cd frontend && npm run build
```

## 8. 文档约束

- 不要在文档中写死固定通过数，例如 `29 passed`
- 最近一轮回归结果应以 `PLAN.md`、`改造进度.md`、`.pipeline/progress.md` 中的记录为准

## 9. 当前缺失项

- 强制覆盖率阈值：当前项目暂无此内容
- 独立集成测试目录：当前项目暂无此内容
- 前端自动化 E2E：当前项目暂无此内容
