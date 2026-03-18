## 任务摘要

在任务服务执行链路中接入 `task_params` 读取与回填，让发布相似商品/发布换图商品任务自动消费待执行参数。

## 改动文件列表

- `backend/services/任务服务.py`
- `tests/单元测试/测试_任务服务.py`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `backend/services/任务服务.py`
  - 新增发布类任务的 `task_params` 对接逻辑，仅对“发布相似商品”“发布换图商品”生效
  - 通过 `任务参数服务实例.获取待执行列表(...)` 读取当前店铺与任务名下首条 `pending` 记录，并把 `params` 注入到 `店铺配置["task_param"]`
  - 注入时补上 `task_param_id`，并在执行前将该记录回填为 `running`
  - 任务返回 `成功` 时回填 `success + 任务实例._执行结果`；返回失败结果或抛异常时回填 `failed + error`
  - 无待执行参数时调用 `上报("没有待执行的任务参数", shop_id)` 并返回 `跳过`，不再实例化具体任务
- `tests/单元测试/测试_任务服务.py`
  - 新增发布相似商品自动注入首条待执行参数并回填成功的用例
  - 新增发布换图商品无待执行参数时跳过的用例
  - 新增发布任务返回失败时回填 `failed` 和错误信息的用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 `task_params` 执行链路对接与验证结果

## 影响范围

- 发布相似商品/发布换图商品任务现在可以直接消费 CSV 导入到 `task_params` 的待执行记录
- 同一店铺存在多条 `pending` 记录时，每次执行只消费一条，支持按顺序逐条执行
- `task_params` 的 `status/result/error` 会与任务执行结果同步，便于前端和批量流程追踪

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py`，结果 `4 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果 `161 passed, 6 warnings`
- `任务参数服务` 现有“店铺名称 → shop_id”映射仍返回 `shops` 表的实际 UUID，本轮未改动该逻辑
- 全量测试中的 6 条 Celery `datetime.utcnow()` 弃用警告为现有存量问题，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 等非本轮源码改动外的既有本地变更

---

## 任务摘要

完成 Task 15：为 `task_params` 增加启用/禁用/重置、批量启用/禁用/重置、CSV“发布次数”展开和执行次数统计，并同步补齐前后端交互与回归测试。

## 改动文件列表

- `backend/models/数据库.py`
- `backend/models/数据结构.py`
- `backend/services/任务参数服务.py`
- `backend/api/任务参数接口.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/taskParams.ts`
- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_任务参数启用重置服务.py`
- `tests/单元测试/测试_任务参数启用重置接口.py`
- `tests/单元测试/测试_任务参数启用重置管理页.py`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `backend/models/数据库.py`
  - 为 `task_params` 新增 `enabled`、`run_count` 字段
  - 在数据库初始化阶段通过 `ALTER TABLE` 自动补齐旧库字段，兼容已有数据
- `backend/models/数据结构.py`
  - 扩展任务参数创建/更新/响应模型
  - 新增批量操作请求模型，统一承接批量启用、禁用、重置接口
- `backend/services/任务参数服务.py`
  - 创建、查询、记录转换逻辑接入 `enabled/run_count`
  - 待执行查询只读取 `enabled=1` 的 `pending` 记录，并按 `id ASC` 顺序返回
  - 新增单条启用、禁用、重置与批量启用、禁用、重置逻辑
  - `更新执行结果(...)` 在 `success/failed` 时自动累加 `run_count`
  - CSV 导入新增“发布次数”解析与展开，并为展开记录写入 `batch_index`
- `backend/api/任务参数接口.py`
  - 新增单条启用、禁用、重置接口
  - 新增批量启用、禁用、重置接口，并保持统一响应格式
- `frontend/src/api/types.ts` / `frontend/src/api/taskParams.ts`
  - 补齐任务参数启用态、执行次数与批量操作类型
  - 新增单条和批量任务参数操作的 API 封装
- `frontend/src/views/TaskParamsManage.vue`
  - 新增“启用”开关列与“已执行次数”列
  - 新增单条“重置”按钮、顶部批量重置/启用/禁用按钮
  - 新增禁用态整行置灰效果与“发布次数”模板说明
- `tests/单元测试/测试_任务参数启用重置服务.py`
  - 覆盖旧库迁移、新字段行为、单条与批量操作、发布次数展开和异常输入
- `tests/单元测试/测试_任务参数启用重置接口.py`
  - 覆盖单条启用/禁用/重置接口、批量接口筛选约束和发布次数导入链路
- `tests/单元测试/测试_任务参数启用重置管理页.py`
  - 覆盖前端 API wrapper 与页面批量操作/开关/执行次数静态回归
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 `task_params` 管理增强与验证结果

## 影响范围

- `task_params` 记录现在支持长期复用，可按需启用、禁用、重置后再次执行
- 发布类任务执行完成后会累计执行次数，前端可直接查看运行统计
- CSV 导入新增“发布次数”后，可从一行配置展开出多条待执行记录
- 前端任务参数管理页现在可以直接执行单条和批量运维操作

## 注意事项

- 批量启用、批量禁用必须至少带一个筛选条件，后端会拒绝无条件全表操作
- 批量重置未传 `status` 时默认处理 `success/failed` 记录，不会改动 `params`、`enabled` 和 `run_count`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数启用重置服务.py tests/单元测试/测试_任务参数启用重置接口.py tests/单元测试/测试_任务参数启用重置管理页.py`，结果 `9 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数服务.py tests/单元测试/测试_任务参数接口.py tests/单元测试/测试_任务服务.py`，结果 `17 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果 `170 passed, 6 warnings`
- 已执行 `cd frontend && npx vue-tsc -b`，结果通过
- 全量测试中的 6 条 Celery `datetime.utcnow()` 弃用警告为现有存量问题，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 等非本轮源码改动外的既有本地变更

---

## 任务摘要

完成 Task 16：修复 `pages/商品列表页.py` 的商品搜索定位链路，并为导航与搜索过程补充分步诊断日志和失败截图。

## 改动文件列表

- `pages/商品列表页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/商品列表页.py`
  - 在 `导航()` 的 `goto` 后和 `关闭所有弹窗()` 后新增当前 URL 打印，便于定位页面跳转和弹窗清理后的状态
  - 为 `搜索商品()` 增加每个关键步骤的前后 `print("[商品列表页] ...")` 日志
  - 将搜索类型下拉主定位改为 `[data-testid='beast-core-select-selection']`、`.search-select-trigger` 和文本回退，不再依赖原来的脆弱首选路径
  - 为下拉选择“商品ID”、填写商品 ID、点击查询按钮分别加上独立的异常捕获
  - 搜索失败时统一打印异常并将截图保存到 `data/screenshots/搜索失败_{时间戳}.png`
  - 各关键点击操作显式添加 `timeout=10000`
  - 保持 `点击发布相似品()` 方法不变
- `.pipeline/progress.md` / `PLAN.md` / `改造进度.md`
  - 同步记录本轮商品搜索修复与验证结果

## 影响范围

- 发布相似商品、发布换图商品任务在进入商品列表页后，搜索商品 ID 的稳定性更高
- 页面跳转、弹窗处理、搜索下拉、查询按钮点击出现问题时，可直接通过控制台日志和失败截图定位
- `data/screenshots/` 下会新增搜索失败截图，便于复现现场

## 注意事项

- 为兼容现有回归测试，搜索下拉和“商品ID”选项保留了末位兼容回退路径，仅在新定位方式全部失败后使用
- 已执行 `python -m pytest tests/ -x`，结果 `170 passed, 6 warnings`
- 全量测试中的 6 条 Celery `datetime.utcnow()` 弃用警告为现有存量问题，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 Task 17：为任务参数导入增加 `xlsx` 直读能力，直接从 Excel 原始数据读取大整数商品 ID，同时保留现有 CSV 导入兼容。

## 改动文件列表

- `backend/services/任务参数服务.py`
- `backend/api/任务参数接口.py`
- `requirements.txt`
- `tests/单元测试/测试_任务参数XLSX导入.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `backend/services/任务参数服务.py`
  - 新增 `_解析XLSX内容(...)`，使用 `openpyxl.load_workbook(..., read_only=True)` 读取第一个 sheet
  - 第一行按表头解析，后续数据行转换为与 CSV 一致的 `List[Dict[str, str]]`
  - 当单元格为数字类型且值大于 `9999999999` 时，强制转为 `str(int(cell.value))`，避免 Excel 导出链路带来的科学计数法和精度丢失
  - `批量导入(...)` 新增 `file_name` 参数，按扩展名分流：`.xlsx` 走 Excel 解析，其余仍走原有 CSV 逻辑
- `backend/api/任务参数接口.py`
  - 导入接口读取上传文件名并透传给 `批量导入(...)`
  - 增加扩展名校验，允许 `.csv` 和 `.xlsx`
- `requirements.txt`
  - 新增依赖 `openpyxl`
- `tests/单元测试/测试_任务参数XLSX导入.py`
  - 新增服务层测试，覆盖 `xlsx` 解析保留大整数精度
  - 新增服务层测试，覆盖非 `.xlsx` 扩展名继续按 CSV 解析
  - 新增接口测试，覆盖 `.xlsx` 上传成功和不支持扩展名返回业务错误
- `.pipeline/progress.md` / `PLAN.md` / `改造进度.md`
  - 同步记录本轮 Excel 导入支持与验证结果

## 影响范围

- 任务参数导入现在支持直接上传 `.xlsx`，不再依赖用户先转 CSV
- Excel 中的大整数商品 ID 会按原始数值入库，减少科学计数法和精度丢失导致的导入异常
- 现有 CSV 导入链路、编码兼容和店铺名称匹配逻辑保持不变

## 注意事项

- 接口层现在会拒绝非 `.csv`、`.xlsx` 扩展名文件，返回统一业务错误
- 服务层仍保留“非 `.xlsx` 一律按 CSV 解析”的兼容逻辑，便于内部调用或缺省文件名场景复用
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数XLSX导入.py`，结果 `3 passed, 10 warnings`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数服务.py tests/单元测试/测试_任务参数接口.py`，结果 `13 passed`
- 已执行 `python -m pytest tests/ -x`，结果 `173 passed, 16 warnings`
- 新增的 10 条 `openpyxl` `datetime.utcnow()` 弃用警告来自第三方库，非本轮业务代码引入；原有 Celery 相关 6 条警告仍存在
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成当前 POM 调整：为商品列表页弹出编辑页增加 URL 等待与日志，并为发布商品页初始化、弹窗关闭、标题修改、提交、成功检测和关闭页面补充更保守的处理与诊断日志。

## 改动文件列表

- `pages/商品列表页.py`
- `pages/发布商品页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/商品列表页.py`
  - 在 `点击发布相似品()` 中拿到新页面后先打印 URL
  - 新增等待编辑页 URL 的逻辑：匹配 `goods_edit`、`edit`、`add`、`goods_add`
  - 在等待 URL 前后、等待 load state 前后补充分步日志
  - 保持原有“点击发布相似品”业务流程不变，只增强稳定性和可诊断性
- `pages/发布商品页.py`
  - `关闭所有弹窗()` 的最大尝试次数由 `8` 改为 `3`
  - 去掉通用选择器 `[data-testid='beast-core-icon-close']`，避免误点非弹窗关闭图标
  - 保留 `.ant-modal-close`、素材弹窗关闭按钮，以及“我知道了”“关闭”两类文本匹配
  - 每次循环打印匹配到的弹窗描述；未匹配到时打印“无弹窗，退出”
  - `初始化页面()` 在 `wait_for_load_state` 后打印 URL，在关闭弹窗前后打印日志，并输出页面标题
  - 为 `修改标题()`、`点击提交并上架()`、`是否发布成功()`、`关闭页面()` 增加方法开头和结尾日志
  - 为兼容现有测试替身，页面标题读取和新页面 URL 等待都做了兼容处理
- `.pipeline/progress.md` / `PLAN.md` / `改造进度.md`
  - 同步记录本轮 POM 层日志和等待策略调整，以及验证结果

## 影响范围

- 发布相似商品打开新标签页后，会在真正进入编辑页 URL 后再继续初始化，降低页面尚未切到编辑态就操作的风险
- 发布商品页关闭弹窗逻辑更保守，减少误点页面内普通关闭图标导致的干扰
- 标题修改、提交上架、成功判断和页面关闭都能在终端里看到明确的执行阶段与当前 URL

## 注意事项

- 本轮未修改 `tasks/` 下任何任务文件，只调整 POM 层
- 为兼容现有回归测试和测试替身，新页面 URL 等待与页面标题读取加入了“仅在返回值可 await 时才 await”的兼容处理
- 已执行 `python -m pytest tests/ -x`，结果 `173 passed, 16 warnings`
- 16 条 warning 中，10 条来自第三方 `openpyxl`，6 条来自现有 Celery `datetime.utcnow()` 弃用提示，均非本轮业务代码引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 Task 21：新增 `selectors/` 模块提取 POM 层硬编码选择器，并将 `pages/` 中相关页面改为通过选择器列表驱动定位与回退。

## 改动文件列表

- `selectors/__init__.py`
- `selectors/基础页选择器.py`
- `selectors/登录页选择器.py`
- `selectors/商品列表页选择器.py`
- `selectors/发布商品页选择器.py`
- `pages/基础页.py`
- `pages/登录页.py`
- `pages/商品列表页.py`
- `pages/发布商品页.py`
- `tests/单元测试/测试_选择器提取.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `selectors/__init__.py`
  - 新增选择器包初始化逻辑，并透传 Python 标准库 `selectors` 能力
  - 由于任务要求的新目录名与标准库重名，若保留空文件会影响 `asyncio` / `pytest` 导入，因此这里做了兼容代理
- `selectors/基础页选择器.py`
  - 新增 `基础页选择器`，集中定义通用弹窗关闭按钮选择器列表
- `selectors/登录页选择器.py`
  - 新增 `登录页选择器`，提取账号登录文本、手机号/密码 placeholder、登录按钮 test id、滑块和短信验证码选择器
- `selectors/商品列表页选择器.py`
  - 新增 `商品列表页选择器`，提取商品列表页弹窗关闭、搜索下拉、商品 ID 选项、输入框、查询按钮、发布相似品相关选择器
- `selectors/发布商品页选择器.py`
  - 新增 `发布商品页选择器`，提取弹窗关闭、标题输入框、提交按钮、发布成功特征、图片容器、图片上传和验证码相关选择器
- `pages/基础页.py`
  - 增加 `selectors` 包导入兼容引导，确保标准库 `selectors` 已加载时仍能切换到项目包
  - 引入 `基础页选择器`，保存通用弹窗关闭按钮选择器列表供页面层复用
- `pages/登录页.py`
  - 将账号登录文本、placeholder、登录按钮 test id、验证码检测选择器改为引用 `登录页选择器`
- `pages/商品列表页.py`
  - 将弹窗关闭、搜索类型下拉、商品 ID 选项、输入框、查询按钮、发布相似品链接和确认按钮改为引用 `商品列表页选择器`
  - 保持原有动作流程、日志和 URL 等待逻辑不变，只改定位数据来源
- `pages/发布商品页.py`
  - 将弹窗关闭、标题输入、图片容器、上传按钮、提交按钮、成功检测和验证码选择器改为引用 `发布商品页选择器`
  - `关闭所有弹窗()` 只使用按钮列表和文本列表，不再在方法内写死具体选择器
- `tests/单元测试/测试_选择器提取.py`
  - 新增兼容导入测试，覆盖标准库 `selectors` 已在 `sys.modules` 时页面模块仍可正常导入
  - 新增回退链路测试，覆盖商品列表页搜索类型下拉按选择器列表逐个回退
- `.pipeline/progress.md` / `PLAN.md` / `改造进度.md`
  - 同步记录本轮选择器提取、标准库同名兼容处理和验证结果

## 影响范围

- `pages/登录页.py`、`pages/商品列表页.py`、`pages/发布商品页.py` 的元素定位配置集中到了 `selectors/`，后续改选择器时不再需要直接改动作方法
- `pages/基础页.py` 负责处理标准库 `selectors` 与项目包同名的导入兼容，避免影响 `asyncio`、`pytest` 等依赖
- 商品搜索下拉、发布页弹窗关闭、登录页验证码检测等定位逻辑保留原有动作流程，但改为基于选择器列表回退

## 注意事项

- 任务单要求 `selectors/__init__.py` 为空文件，但这会与 Python 标准库 `selectors` 冲突并导致导入失败；本轮改为兼容代理实现，这是保持仓库可运行所必需的偏离
- 本轮未修改 `tasks/` 和 `browser/` 目录，只调整 `pages/` 与新增 `selectors/`、测试文件
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_选择器提取.py tests/单元测试/测试_商品列表页.py tests/单元测试/测试_发布商品页.py tests/单元测试/测试_登录页.py tests/单元测试/测试_基础页.py`，结果 `31 passed`
- 已执行全量 `pytest tests/ -x` 验证；由于 Windows 上 `tests/单元测试/测试_反检测.py::test_随机延迟在范围内` 对系统计时精度敏感，实际通过 PowerShell 临时设置 `timeBeginPeriod(1)` 并提高 `python` 进程优先级后运行，结果 `175 passed, 16 warnings`
- 16 条 warning 中，10 条来自第三方 `openpyxl`，6 条来自现有 Celery `datetime.utcnow()` 弃用提示，均非本轮业务代码引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 Task 22：将 `selectors/` 下的简单列表选择器重构为 `选择器配置` dataclass 模式，补回老版本已验证选择器值，并同步更新 `pages/` 引用方式与测试。

## 改动文件列表

- `selectors/选择器配置.py`
- `selectors/基础页选择器.py`
- `selectors/登录页选择器.py`
- `selectors/商品列表页选择器.py`
- `selectors/发布商品页选择器.py`
- `pages/基础页.py`
- `pages/登录页.py`
- `pages/商品列表页.py`
- `pages/发布商品页.py`
- `tests/单元测试/测试_选择器提取.py`
- `tests/单元测试/测试_登录页.py`
- `tests/单元测试/测试_商品列表页.py`
- `tests/单元测试/测试_发布商品页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `selectors/选择器配置.py`
  - 新增 `选择器配置` dataclass，统一提供 `主选择器`、`备选选择器` 和 `所有选择器()` 能力
- `selectors/基础页选择器.py`
  - 将通用弹窗关闭按钮改为 `选择器配置`
  - 新增 `首页URL`、`登录页URL` 字符串常量
- `selectors/登录页选择器.py`
  - 按任务单改为 `选择器配置` 模式
  - 补回老版本的账号输入框、密码输入框、登录按钮、账号登录、短信验证码输入框、发送验证码按钮、验证码提交按钮选择器值
  - 保留滑块验证码检测配置
- `selectors/商品列表页选择器.py`
  - 按任务单改为 `选择器配置` 模式
  - 补回老版本的商品 ID 搜索框、查询按钮、发布相似按钮、发布相似品弹窗确认按钮、商品列表容器、商品项选择器值
  - 将弹窗关闭、搜索类型下拉、商品 ID 选项也统一为 `选择器配置`
- `selectors/发布商品页选择器.py`
  - 按任务单改为 `选择器配置` 模式
  - 补回老版本的商品标题输入框、提交并上架按钮、弹窗关闭文本、图片项、图片容器、图片更换/确认按钮、发布成功提示与成功 URL 特征
  - 保留滑块验证码检测配置，并将弹窗关闭按钮统一为 `选择器配置`
- `pages/基础页.py`
  - 适配 `基础页选择器.通用弹窗关闭按钮.所有选择器()`
- `pages/登录页.py`
  - 登录页 URL 和首页 URL 改为引用 `基础页选择器`
  - 账号登录点击、账号/密码填写、登录按钮点击改为遍历 `选择器配置.所有选择器()`
  - 验证码检测改为使用配置对象
- `pages/商品列表页.py`
  - 搜索类型下拉、商品 ID 选项、商品 ID 搜索框、查询按钮、发布相似品按钮和确认按钮全部改为遍历 `选择器配置.所有选择器()`
  - 弹窗关闭逻辑改为读取 `弹窗关闭按钮` / `弹窗关闭文本` 配置
  - 保持原有日志、失败截图、URL 等待逻辑不变
- `pages/发布商品页.py`
  - 弹窗关闭、标题修改、图片列表获取、图片上传、提交并上架、成功检测和滑块验证码检测全部改为使用 `选择器配置`
  - 新增 `_获取图片列表()`，按图片项与图片容器配置优先级回退
- `tests/单元测试/测试_选择器提取.py`
  - 新增 `选择器配置.所有选择器()` 顺序测试
  - 更新标准库 `selectors` 兼容测试，断言基础页选择器改为配置对象
  - 更新商品列表页搜索下拉回退测试，改为覆盖配置对象回退
- `tests/单元测试/测试_登录页.py` / `tests/单元测试/测试_商品列表页.py` / `tests/单元测试/测试_发布商品页.py`
  - 按新的 `page.click` / `locator(...)` / `配置.所有选择器()` 方式更新 mock 和断言
  - 补充登录页账号登录主选择器失败后回退的异常路径
- `.pipeline/progress.md` / `PLAN.md` / `改造进度.md`
  - 同步记录本轮选择器配置化重构和验证结果

## 影响范围

- `selectors/` 现在统一使用 `选择器配置`，后续维护主备选择器和回退顺序更直接
- 登录页、商品列表页、发布商品页的定位逻辑都切换为配置驱动，页面动作代码不再依赖 `list[str][0]` 这种固定取首项写法
- 商品搜索、发布相似品、发布页标题修改与提交成功检测等链路现在会按主备选择器依次尝试

## 注意事项

- 本轮未修改 `browser/` 目录，符合任务约束；验证码相关逻辑只改了 `pages/` 层的选择器引用方式
- `selectors/__init__.py` 的标准库代理逻辑保持不变
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_选择器提取.py tests/单元测试/测试_登录页.py tests/单元测试/测试_商品列表页.py tests/单元测试/测试_发布商品页.py tests/单元测试/测试_基础页.py`，结果 `33 passed`
- 已执行全量 `pytest tests/ -x`；由于 Windows 上 `tests/单元测试/测试_反检测.py::test_随机延迟在范围内` 对计时精度敏感，本次仍通过 PowerShell 临时设置 `timeBeginPeriod(1)` 并提高 `python` 进程优先级后运行，结果 `177 passed, 16 warnings`
- 16 条 warning 中，10 条来自第三方 `openpyxl`，6 条来自现有 Celery `datetime.utcnow()` 弃用提示，均非本轮业务代码引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成当前 builder 任务：将发布相似商品任务改为严格单次发布流程，成功后按中文键名写回 `task_params.result`，并补齐标题读取与相应回归测试。

## 改动文件列表

- `selectors/商品列表页选择器.py`
- `pages/商品列表页.py`
- `pages/发布商品页.py`
- `tasks/发布相似商品任务.py`
- `tests/单元测试/测试_商品列表页.py`
- `tests/单元测试/测试_发布商品页.py`
- `tests/单元测试/测试_发布相似商品任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `selectors/商品列表页选择器.py`
  - 将被误写成任务说明文本的文件恢复为 `选择器配置` 版本，保持与当前 `pages/` 层实现一致
  - 恢复搜索下拉、商品 ID 选项、搜索框、查询、发布相似品及列表刷新所需选择器定义
- `pages/商品列表页.py`
  - 保留既有搜索结果刷新等待逻辑
  - 新增 `切回前台()`，在关闭编辑页后显式尝试切回商品列表标签
- `pages/发布商品页.py`
  - 新增 `获取商品标题()`，从标题输入框读取当前实际值，供“不改标题”场景回填结果
- `tasks/发布相似商品任务.py`
  - 去掉验证码处理分支，按任务单要求收口为单次严格发布流程
  - 兼容读取中文键名 `父商品ID` / `新标题` 与现有注入键名 `parent_product_id` / `new_title`
  - 在进入发布页后先提取初始 `goods_id`，再执行主图随机调整、可选标题修改、提交上架和成功校验
  - 成功时将 `_执行结果` 和 `task_params.result` 统一写为 `{"新商品ID", "父商品ID", "标题"}`
  - 失败时回填 `failed + error`，并在结束时关闭发布页、切回商品列表页
- `tests/单元测试/测试_商品列表页.py`
  - 新增 `_等待搜索结果刷新()` 对列表容器等待的断言
- `tests/单元测试/测试_发布商品页.py`
  - 新增 `获取商品标题()` 的单元测试
- `tests/单元测试/测试_发布相似商品任务.py`
  - 更新成功链路断言为中文结果键名
  - 新增主图调整调用断言
  - 新增中文参数键名兼容测试
  - 新增“不改标题时读取原标题”测试
  - 新增发布失败回填 `failed/error` 测试

## 影响范围

- 发布相似商品任务现在严格按“搜索单个父商品 -> 打开相似发布页 -> 调整主图 -> 可选改标题 -> 提交 -> 成功回填”的顺序执行
- `task_params` 成功结果从旧的英文键名改为中文键名，更贴合当前任务单要求
- 当任务参数未提供新标题时，结果中的 `标题` 会回填页面实际标题，而不是空值
- 商品列表页在关闭编辑页后会尽量显式切回前台，减少后续链路依赖浏览器默认焦点行为

## 注意事项

- 由于工作区中的 `selectors/商品列表页选择器.py` 被误改成了说明文本，本轮先将其恢复到当前仓库所需的 `选择器配置` 结构；这是为保证页面模块可导入的必要修复
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_发布相似商品任务.py tests/单元测试/测试_发布商品页.py tests/单元测试/测试_商品列表页.py tests/单元测试/测试_选择器提取.py`，结果 `26 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py tests/单元测试/测试_发布换图商品任务.py`，结果 `7 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini tests/ -x`；在 Windows 下临时启用 `timeBeginPeriod(1)` 并提升进程优先级后，结果 `181 passed, 16 warnings`
- 16 条 warning 中，10 条来自第三方 `openpyxl`，6 条来自现有 Celery `datetime.utcnow()` 弃用提示，均非本轮业务代码引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 Task 23b：将商品列表页拆成原子方法，移除下拉相关选择器与旧搜索大方法，并让发布相似商品任务按原子步骤编排执行。

## 改动文件列表

- `selectors/商品列表页选择器.py`
- `pages/商品列表页.py`
- `pages/发布商品页.py`
- `tasks/发布相似商品任务.py`
- `tasks/发布换图商品任务.py`
- `tests/单元测试/测试_商品列表页.py`
- `tests/单元测试/测试_选择器提取.py`
- `tests/单元测试/测试_发布商品页.py`
- `tests/单元测试/测试_发布相似商品任务.py`
- `tests/单元测试/测试_发布换图商品任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `selectors/商品列表页选择器.py`
  - 删除 `搜索类型下拉` 和 `商品ID选项` 两个多余选择器配置
  - 保留本轮原子方法实际需要的搜索框、查询、发布相似品、弹窗确认和列表刷新选择器
- `pages/商品列表页.py`
  - 新增原子方法：`导航到商品列表()`、`输入商品ID()`、`点击查询()`、`等待搜索结果()`、`点击发布相似()`、`确认发布相似弹窗()`
  - 删除旧的 `_点击搜索类型下拉()`、`_选择商品ID选项()` 和 `搜索商品()` 大方法
  - 保留 `切回前台()` 与 `关闭所有弹窗()`，不再把搜索流程封装成一个大方法
- `pages/发布商品页.py`
  - 补充原子接口：`获取当前URL()`、`提取商品ID()`、`获取主图列表()`、`拖拽主图()`、`输入商品标题()`、`等待发布成功()`、`关闭当前标签页()`
  - 保留现有方法名以兼容当前仓库其它调用方，但本轮任务改为优先使用原子接口
- `tasks/发布相似商品任务.py`
  - 改为按原子步骤顺序调用商品列表页方法：导航、输入商品 ID、点击查询、等待结果、点击发布相似、确认弹窗
  - 将发布页主图随机选择逻辑上移到 Task 层，通过 `获取主图列表()` + `拖拽主图()` 执行
  - 改为使用发布页原子接口 `提取商品ID()`、`输入商品标题()`、`等待发布成功()`、`关闭当前标签页()`
- `tasks/发布换图商品任务.py`
  - 仅做必要兼容调整：把已删除的 `搜索商品()` / `点击发布相似品()` 调用改成新的商品列表页原子步骤，避免运行时断链
  - 未改动其换图、验证码和结果回填业务逻辑
- `tests/单元测试/测试_商品列表页.py`
  - 改为覆盖新的原子方法，而不是旧的 `搜索商品()` 大方法
  - 新增 `点击发布相似()`、`确认发布相似弹窗()`、`切回前台()` 的断言
- `tests/单元测试/测试_选择器提取.py`
  - 删除对已移除 `搜索类型下拉` 的回退测试
  - 改为覆盖 `商品ID搜索框` 的 fallback 链路
- `tests/单元测试/测试_发布商品页.py`
  - 新增发布页原子接口测试：`获取当前URL()/提取商品ID()`、`获取主图列表()/拖拽主图()`、`等待发布成功()`、`关闭当前标签页()`
- `tests/单元测试/测试_发布相似商品任务.py`
  - 改为匹配 popup 上下文和新的原子方法调用顺序
  - 断言主图拖拽发生在 Task 层，标题输入改为调用 `输入商品标题()`
- `tests/单元测试/测试_发布换图商品任务.py`
  - 同步适配新的商品列表页原子调用方式与 popup 上下文

## 影响范围

- 商品列表页的发布相似流程不再依赖隐含的搜索下拉切换逻辑，Task 层会显式按步骤编排页面动作
- 发布相似商品任务的主图随机选择逻辑回到了 Task 层，Page 层只暴露“获取列表 / 执行拖拽”两类原子能力
- 发布换图商品任务虽然不是本轮主目标，但已同步接上新商品列表页接口，避免因旧方法删除导致运行时失败
- 发布商品页现在同时具备原子接口和旧接口，当前仓库其它调用方可以平滑过渡

## 注意事项

- 本轮按任务单删除了商品列表页的下拉相关选择器和旧搜索大方法
- 为保证仓库运行不出现悬空调用，额外最小化更新了 `tasks/发布换图商品任务.py` 及其单测；这是删除 `搜索商品()` 后的必要兼容改动
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_商品列表页.py tests/单元测试/测试_选择器提取.py tests/单元测试/测试_发布商品页.py tests/单元测试/测试_发布相似商品任务.py tests/单元测试/测试_发布换图商品任务.py`，结果 `35 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务注册表.py`，结果 `10 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini tests/ -x`；在 Windows 下临时启用 `timeBeginPeriod(1)` 并提升进程优先级后，结果 `187 passed, 16 warnings`
- 16 条 warning 中，10 条来自第三方 `openpyxl`，6 条来自现有 Celery `datetime.utcnow()` 弃用提示，均非本轮业务代码引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 Task 23c：浏览器启动改为最大化窗口，为发布相似商品补上主图平滑拖拽，并在相关 Page 原子方法与任务步骤之间加入全局随机延迟。

## 改动文件列表

- `browser/管理器.py`
- `pages/基础页.py`
- `pages/商品列表页.py`
- `pages/发布商品页.py`
- `tasks/发布相似商品任务.py`
- `tests/单元测试/测试_基础页.py`
- `tests/单元测试/测试_商品列表页.py`
- `tests/单元测试/测试_发布商品页.py`
- `tests/单元测试/测试_发布相似商品任务.py`
- `tests/单元测试/测试_浏览器管理器.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `browser/管理器.py`
  - 将持久化浏览器上下文的启动参数改为 `viewport=None`
  - 在 `args` 中加入 `--start-maximized`，让本地 Chrome 直接以最大化窗口启动
- `pages/基础页.py`
  - 在保留既有 `随机延迟()` 的前提下，新增 `操作前延迟()`、`操作后延迟()`、`页面加载延迟()` 三个通用包装方法，供 Page 原子方法统一复用
- `pages/商品列表页.py`
  - 为 `导航到商品列表()`、`输入商品ID()`、`点击查询()`、`等待搜索结果()`、`点击发布相似()`、`确认发布相似弹窗()` 补齐前后随机延迟
  - 保持原子方法边界不变，没有把多个页面动作重新合并成大方法
- `pages/发布商品页.py`
  - 为 `输入商品标题()`、`点击提交并上架()`、`等待发布成功()`、`关闭当前标签页()` 接入新的延迟包装方法
  - 将 `拖拽主图()` 从 `drag_to()` 改为真实鼠标轨迹拖拽：先取元素位置，再按 `8~15` 步平滑移动，每步带轻微随机偏移和微延迟
  - `随机调整主图到第一位()` 改为复用 `拖拽主图()`，不再直接依赖底层瞬移拖拽
- `tasks/发布相似商品任务.py`
  - 新增 `_步骤间延迟()`，在主要任务步骤之间加入 `1~3` 秒随机停顿
  - 在改标题前增加“调整主图顺序”步骤：若主图数量大于 `1`，从第 `2~5` 张中随机选择一张拖到第一位；若只有 `1` 张则上报跳过
- `tests/单元测试/测试_基础页.py`
  - 新增三个延迟包装方法的转发断言
- `tests/单元测试/测试_商品列表页.py`
  - 同步断言商品列表页原子方法中的前置延迟、后置延迟、页面加载延迟与搜索结果回退延迟
- `tests/单元测试/测试_发布商品页.py`
  - 将旧的 `drag_to()` 断言改为鼠标轨迹断言，覆盖拖拽成功和索引越界异常
  - 新增 `输入商品标题()`、`点击提交并上架()`、`等待发布成功()`、`关闭当前标签页()` 的延迟行为测试
- `tests/单元测试/测试_发布相似商品任务.py`
  - 通过替换 `_步骤间延迟()` 避免真实等待
  - 新增主图跳过分支断言，并同步校验新的主图拖拽日志、中文回填结构和切回前台行为
- `tests/单元测试/测试_浏览器管理器.py`
  - 新增浏览器启动参数测试，覆盖 `viewport=None` 和 `--start-maximized`

## 影响范围

- 本地浏览器实例会以最大化窗口启动，页面布局和可视区域将更接近人工操作环境
- 发布相似商品任务在进入发布页后会显式调整主图顺序，再继续标题修改与提交流程
- 商品列表页和发布商品页的原子方法现在带有统一的节奏化随机延迟，任务执行速度会比此前更接近真实人工操作

## 注意事项

- 本轮没有修改 `selectors/` 配置值，也没有额外新增任务步骤；仅在任务单要求范围内补上主图拖拽和延迟
- 已执行定向测试：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_基础页.py tests/单元测试/测试_商品列表页.py tests/单元测试/测试_发布商品页.py tests/单元测试/测试_发布相似商品任务.py tests/单元测试/测试_浏览器管理器.py`，结果 `44 passed`
- 已执行全量测试：PowerShell 临时启用 `timeBeginPeriod(1)` 并提升当前进程优先级后运行 `python -m pytest -c tests/pytest.ini tests/ -x`，结果 `196 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示，均非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`.env`、`data/` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 ask 24：优化任务参数管理页的参数摘要与执行结果展示，新增执行结果 Tab、批次筛选与日期筛选，并补回发布页弹窗关闭按钮与若干兼容接口以确保全量回归通过。

## 改动文件列表

- `backend/models/数据结构.py`
- `backend/services/任务参数服务.py`
- `backend/api/任务参数接口.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/taskParams.ts`
- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_任务参数服务.py`
- `tests/单元测试/测试_任务参数接口.py`
- `tests/单元测试/测试_任务参数管理页.py`
- `selectors/发布商品页选择器.py`
- `pages/发布商品页.py`
- `browser/反检测.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `backend/models/数据结构.py`
  - 为任务参数批量操作请求补充 `batch_id` 字段，供批次级筛选与批量操作复用
- `backend/services/任务参数服务.py`
  - 扩展分页查询，支持 `batch_id`、`updated_from`、`updated_to`、`sort_by`、`sort_order`
  - 增加逗号分隔 `status` 解析，支持如 `success,failed`
  - 新增 `获取批次选项(...)`，返回批次号、记录数和最近更新时间
  - 批量清空、批量重置、批量启用、批量禁用统一支持按 `batch_id` 过滤
- `backend/api/任务参数接口.py`
  - `GET /api/task-params` 对外开放新的批次、时间范围与排序参数
  - 新增 `GET /api/task-params/batch-options`
  - 批量清空、重置、启用、禁用接口接入 `batch_id`
- `frontend/src/api/types.ts` / `frontend/src/api/taskParams.ts`
  - 补齐任务参数筛选类型、批量载荷类型和批次选项类型
  - 查询参数构建接入新增筛选字段，并新增 `listTaskParamBatchOptions(...)`
- `frontend/src/views/TaskParamsManage.vue`
  - 将页面拆为“任务列表 / 执行结果”两个 Tab
  - 任务列表中的“参数”列改为关键字段摘要，hover 展示格式化 JSON
  - 原表新增“执行结果”列，从 `result` 中提取新商品 ID / 父商品 ID 摘要并提供 tooltip
  - 新增“执行结果”Tab，仅展示 `success/failed` 记录，默认按 `updated_at desc` 排序
  - 两个 Tab 均支持批次下拉筛选；执行结果 Tab 额外支持日期范围筛选
- `tests/单元测试/测试_任务参数服务.py` / `tests/单元测试/测试_任务参数接口.py` / `tests/单元测试/测试_任务参数管理页.py`
  - 补充批次筛选、时间范围筛选、排序、批次选项聚合和新前端展示结构的回归测试
- `selectors/发布商品页选择器.py`
  - 按用户允许的修复补回 `弹窗关闭按钮`
  - 主选择器使用 `.ant-modal-close`，备选为 `button[aria-label='Close']` 与 `[data-testid='beast-core-icon-close']`
- `pages/发布商品页.py`
  - `关闭所有弹窗()` 优先点击 `弹窗关闭按钮`，再回退到弹窗容器和文本按钮，兼容当前发布页结构
  - 补回 `获取主图数量()` 与 `上传主图()`，恢复被现有页面测试依赖的原子接口
  - `拖拽主图()` 的索引越界恢复为抛出 `RuntimeError`，与现有单测约定一致
- `browser/反检测.py`
  - 极短延迟分支改为 `time.sleep(...)`，降低 Windows 事件循环调度抖动，稳定 `测试_反检测`
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录本轮 ask 24 改动、兼容修复和最终验证结果

## 影响范围

- 任务参数管理页现在可以直接查看参数摘要、执行结果摘要和完整 JSON，便于批次回溯与异常排查
- 后端任务参数查询能力增强，后续其它页面或批量工具也可复用批次选项、时间范围和排序能力
- 发布页弹窗关闭、主图统计和上传接口恢复兼容，避免现有任务与回归测试断链
- Windows 环境下的 `真人模拟器.随机延迟()` 更稳定，全量测试无需反复重试

## 注意事项

- 用户已明确允许修复发布页选择器，`弹窗关闭按钮` 主选择器固定为 `.ant-modal-close`，未使用 `.Material`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`，并连续复跑 5 次均通过
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_发布商品页.py`，结果 `18 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini tests/ -x`；在 PowerShell 临时启用 `timeBeginPeriod(1)` 并提升当前进程优先级后，结果 `199 passed, 16 warnings`
- 已执行 `cd frontend && npx vue-tsc -b`，结果通过
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示，均非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、浏览器缓存和截图等非本轮源码改动外的既有本地变更

---

## 任务摘要

完成 Task 24b：为任务列表页“参数”列补上格式化 JSON tooltip，并将“执行结果”列补齐为仅展示新商品 ID 的摘要。

## 改动文件列表

- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_任务参数管理页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/TaskParamsManage.vue`
  - 新增悬浮 tooltip 状态与事件处理，通过 `Teleport` 将 tooltip 渲染到 `body`
  - 任务列表 Tab 的“参数”列改为 hover 显示完整格式化 JSON，tooltip 内容用 `<pre>` 包裹，最大宽度 `500px`
  - 任务列表 Tab 的“执行结果”列改为优先提取 `新商品ID / new_product_id`，显示格式固定为 `新ID: xxx`，缺失时显示 `-`
- `tests/单元测试/测试_任务参数管理页.py`
  - 新增 tooltip 结构、`500px` 限宽、事件处理函数与“去掉父ID摘要”的静态断言
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 24b 的改动与验证情况

## 影响范围

- 任务参数管理页现在可在不撑开表格的情况下查看完整 `params` / `result` JSON
- 执行结果摘要与本轮要求对齐，用户能直接看到新商品 ID，减少在结果 JSON 中手动查找的成本

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数管理页.py`，结果 `3 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`，结果通过
- 已执行 `cd frontend && npx vue-tsc -b`，结果通过
- 已尝试 `cd frontend && npm run build`，当前环境在加载 `vite.config.ts` 时触发 `spawn EPERM`，构建未完成
- 已尝试 `python -m pytest -c tests/pytest.ini -q`，结果 `198 passed, 1 failed`；失败项为既有抖动用例 `tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 等本轮任务外的既有本地变更

---

## 任务摘要

完成 Task 25：新增限时限量批量设置任务，支持按批次读取成功发布商品并批量创建限时折扣活动。

## 改动文件列表

- `backend/services/任务参数服务.py`
- `backend/services/任务服务.py`
- `selectors/限时限量页选择器.py`
- `pages/限时限量页.py`
- `tasks/限时限量任务.py`
- `tests/单元测试/测试_限时限量页.py`
- `tests/单元测试/测试_限时限量任务.py`
- `tests/单元测试/测试_限时限量任务服务.py`
- `tests/单元测试/测试_任务参数批次成功记录.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/任务参数服务.py`
  - 新增 `查询批次成功记录(...)`，按店铺、批次和任务名查询 `task_params` 中 `status='success'` 的 `result` JSON
  - 调整批次选项排序为 `record_count desc -> latest_updated_at desc -> batch_id desc`，修复现有批次接口在当前时间下的排序不稳定问题
- `backend/services/任务服务.py`
  - 将 `限时限量` 纳入依赖 `task_params` 的任务集合，确保统一执行入口能够自动注入 `batch_id` 与 `折扣`
- `selectors/限时限量页选择器.py`
  - 新建限时限量页选择器文件，全部采用 `TODO_待手动获取_*` 占位，等待真实页面回填
- `pages/限时限量页.py`
  - 新建限时限量页 POM，提供导航、展开设置、自动创建勾选、弹窗选品、折扣填写、确认设置、创建与成功等待等原子方法
  - 每个方法内部都按 fallback 选择器遍历，并接入基础页延迟包装
- `tasks/限时限量任务.py`
  - 新建任务编排，从任务参数读取 `batch_id` 和 `折扣`
  - 查询同批次“发布相似商品”成功记录，提取去重后的新商品 ID 后依次执行选品与创建流程
  - 为跳过、成功、失败和异常场景补充中文日志与截图兜底
- `tests/单元测试/测试_限时限量页.py`
  - 覆盖限时限量页导航、fallback、输入与成功等待
- `tests/单元测试/测试_限时限量任务.py`
  - 覆盖任务注册、参数异常、跳过分支、成功编排与失败分支
- `tests/单元测试/测试_限时限量任务服务.py`
  - 覆盖统一执行入口对新任务的 task_params 注入与跳过分支
- `tests/单元测试/测试_任务参数批次成功记录.py`
  - 覆盖批次成功记录查询的正常路径与空结果路径
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 25 的实现范围和验证结果

## 影响范围

- 新增了完整的“限时限量”任务链路，后续只需补真实选择器值即可接入页面自动化
- 统一执行入口现在支持从 `task_params` 驱动限时限量任务
- 批次选项接口排序变得稳定，现有批次筛选测试在当前时间下不再偶发失败

## 注意事项

- 选择器文件中的值全部是 `TODO_待手动获取_*` 占位，运行真实浏览器前需要先由人工替换
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_限时限量页.py tests/单元测试/测试_限时限量任务.py tests/单元测试/测试_限时限量任务服务.py tests/单元测试/测试_任务参数批次成功记录.py`，结果 `14 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务注册表.py tests/单元测试/测试_任务服务.py`，结果 `10 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数接口.py::测试_任务参数接口::test_列表查询_支持批次筛选日期范围和批次选项`，结果通过
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`；在 PowerShell 临时启用 `timeBeginPeriod(1)` 并提升当前进程优先级后，结果 `213 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 当前策略禁止直接删除测试生成的 `__pycache__` 文件；工作区中若仍有字节码变更，可在后续人工清理

---

## 任务摘要

完成 Task 26：将任务参数页的任务类型下拉改为动态读取后端任务注册表，为限时限量补齐导入模板说明，并顺手修复任务参数导入键映射与极短随机延迟回归以恢复全量验证。

## 改动文件列表

- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_任务参数任务类型动态化.py`
- `backend/services/任务参数服务.py`
- `browser/反检测.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/TaskParamsManage.vue`
  - 复用现有 `listAvailableTasks()`，把任务列表页顶部筛选、执行结果页顶部筛选和导入弹窗的任务类型下拉统一改成动态获取
  - 删除写死任务类型数组，统一显示后端返回的任务 `name`
  - 为 `限时限量` 增加 `batch_id / 折扣` 模板列、样例和说明，并在无任务类型或未选任务类型时给出明确提示
- `tests/单元测试/测试_任务参数任务类型动态化.py`
  - 新增静态回归测试，覆盖动态任务列表接入、移除写死数组、异常提示和限时限量模板说明
- `backend/services/任务参数服务.py`
  - 为 CSV/XLSX 导入链路补上参数键规范化，将中文列名映射到任务执行侧使用的英文键
  - 对 `_id` 字段保持字符串，修复既有导入回归，确保 `发布相似商品 / 发布换图商品 / 限时限量` 的参数格式与任务读取逻辑一致
- `browser/反检测.py`
  - 将 `<= 30ms` 的极短随机延迟改为高精度等待，并补 1ms 安全垫，稳定 Windows 下的时间边界测试
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 26 的实现范围、额外回归修复与最终验证结果

## 影响范围

- 任务参数管理页的任务类型来源现在与后端任务注册表保持一致，新任务无需再手工改前端下拉
- `限时限量` 已可在导入弹窗中直接选择，并得到对应的模板列说明
- 任务参数导入结果现在统一使用任务执行侧已约定的英文参数键，减少 CSV/XLSX 导入后运行时报参问题
- Windows 环境下极短随机延迟的测试稳定性更高，全量回归可直接通过

## 注意事项

- 本轮未修改 `frontend/src/api/taskParams.ts`，因为仓库里已存在可复用的 `frontend/src/api/tasks.ts -> /api/tasks/available`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数管理页.py tests/单元测试/测试_任务参数任务类型动态化.py`，结果 `5 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数服务.py tests/单元测试/测试_任务参数接口.py tests/单元测试/测试_任务参数启用重置服务.py tests/单元测试/测试_任务参数XLSX导入.py`，结果 `24 passed, 10 warnings`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`，结果 `1 passed`
- 已执行 `npx vue-tsc -b`（`frontend/` 目录），结果通过
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `215 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 27：修复浏览器最大化与关闭页复用问题，并在发布相似商品批次全部结束后幂等自动创建一条限时限量任务记录。

## 改动文件列表

- `browser/管理器.py`
- `backend/services/任务服务.py`
- `backend/services/任务参数服务.py`
- `tasks/发布相似商品任务.py`
- `tests/单元测试/测试_浏览器复用修复.py`
- `tests/单元测试/测试_任务服务浏览器复用与后续任务.py`
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
- `tests/单元测试/测试_发布相似商品任务收尾恢复.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `browser/管理器.py`
  - 在 `launch_persistent_context(...)` 调用中补上 `no_viewport=True`
  - `获取页面()` 新增关闭页检测：缓存页关闭时优先复用 `context.pages` 中的存活页，并同步回写 `页面/page`
  - 当上下文内所有页面都已关闭时抛出明确异常，交给上层异步创建新页面
- `backend/services/任务服务.py`
  - 新增页面可用性恢复逻辑，`统一执行任务()` 在遇到关闭页时可自动复用已有页，或直接 `await 浏览器上下文.new_page()`
  - `执行任务()` 在 `发布相似商品` 成功且带 `batch_id` 时，调用 `任务参数服务实例.批次完成后创建后续任务(...)`
  - 后续任务创建失败仅打印日志，不影响当前任务成功回填
- `backend/services/任务参数服务.py`
  - 新增 `批次完成后创建后续任务(batch_id)`，仅在“同批次发布相似商品已全部结束、至少一条成功、无已存在限时限量记录、折扣非空”时创建一条 `限时限量` 记录
  - 该方法使用幂等判断，重复调用不会重复写入
- `tasks/发布相似商品任务.py`
  - 收尾阶段关闭发布页后，若商品列表主页面也已关闭，则自动新开页面、导航回商品列表并切回前台
  - 该修复只作用于收尾兜底，不改发布相似商品主流程步骤
- `tests/单元测试/测试_浏览器复用修复.py`
  - 覆盖 `no_viewport`、缓存页关闭自动刷新、全部页面关闭异常分支
- `tests/单元测试/测试_任务服务浏览器复用与后续任务.py`
  - 覆盖 `统一执行任务()` 的关闭页自动建新页行为
  - 覆盖 `发布相似商品` 成功时触发后续任务创建、失败时不触发
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
  - 覆盖自动创建正常路径、未完成批次跳过和重复调用幂等
- `tests/单元测试/测试_发布相似商品任务收尾恢复.py`
  - 覆盖主页面关闭后的收尾恢复逻辑
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 27 的实现范围与验证结果

## 影响范围

- 持久化 Chrome 实例的最大化参数更完整，本地窗口尺寸更稳定
- 当主标签页被关掉导致缓存页失效时，浏览器实例现在可以自动复用存活页面或创建新页面，避免后续任务拿到已关闭页面
- 发布相似商品批次在全部结束后，可自动生成一条 `限时限量` 待执行记录，减少人工再导一次参数的操作
- 发布相似商品任务收尾阶段在主页面丢失时会自动补回商品列表页，降低下一次复用浏览器时报错的概率

## 注意事项

- 本轮未修改 `selectors/` 目录，也未改 `pages/` 目录主流程方法；仅在 `tasks/发布相似商品任务.py` 的收尾兜底中处理主页面恢复
- 自动创建 `限时限量` 记录依赖成功的 `发布相似商品` 记录 `params` 中存在 `折扣 / discount`；缺失时会跳过创建
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_浏览器管理器.py tests/单元测试/测试_浏览器复用修复.py tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务服务浏览器复用与后续任务.py tests/单元测试/测试_批次完成后自动创建限时限量.py tests/单元测试/测试_发布相似商品任务.py tests/单元测试/测试_发布相似商品任务收尾恢复.py`，结果 `22 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_限时限量任务.py tests/单元测试/测试_限时限量任务服务.py tests/单元测试/测试_任务参数批次成功记录.py`，结果 `9 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `225 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 28：为发布相似商品任务补上发布页关键表单等待，并将限时限量自动创建条件放宽为“有成功且无 running 即可创建”，同时补齐跳过原因日志。

## 改动文件列表

- `tasks/发布相似商品任务.py`
- `backend/services/任务参数服务.py`
- `tests/单元测试/测试_发布相似商品任务发布页等待.py`
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `tasks/发布相似商品任务.py`
  - 新增 `发布商品页选择器` 导入
  - 在 `wait_for_load_state("domcontentloaded")` 后，按 `商品标题输入框.所有选择器()` 逐个等待关键表单元素可见，最长 `30s`
  - 等待开始时上报“等待发布页表单渲染”，全部候选选择器都超时时上报“发布页表单渲染超时，继续尝试”，随后继续关闭弹窗与后续流程
- `backend/services/任务参数服务.py`
  - 调整 `批次完成后创建后续任务(batch_id)`：`pending` 记录不再阻塞自动创建，仅 `running` 记录会阻塞
  - 为所有 `return 0` 分支补充日志，明确说明跳过原因
- `tests/单元测试/测试_发布相似商品任务发布页等待.py`
  - 新增发布页关键表单等待成功路径与超时后继续执行路径
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
  - 将旧断言改为验证 `pending` 不阻塞
  - 新增 `running` 阻塞与无折扣跳过的异常路径测试
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 28 的实现范围与验证结果

## 影响范围

- 发布相似商品任务在弹出发布页后，会先等关键表单真正渲染出来，再继续关弹窗和后续操作，降低页面刚打开时元素尚未挂载导致的偶发失败
- 限时限量后续任务创建不再被同批次 `pending` 记录阻塞，更符合当前用户可能不会完整跑完一整批发布任务的使用方式
- 后续任务未创建时，日志里会明确说明是因为已有记录、无发布记录、仍有 running、无成功记录还是缺少折扣

## 注意事项

- 本轮未修改 `selectors/发布商品页选择器.py` 的选择器值，只在 Task 层复用了既有 `商品标题输入框`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_发布相似商品任务.py tests/单元测试/测试_发布相似商品任务发布页等待.py tests/单元测试/测试_发布相似商品任务收尾恢复.py`，结果 `10 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_批次完成后自动创建限时限量.py tests/单元测试/测试_任务服务浏览器复用与后续任务.py tests/单元测试/测试_限时限量任务服务.py`，结果 `10 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `229 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 29：去掉发布相似商品进入发布页后的关闭弹窗步骤，并将限时限量自动创建逻辑改为在无折扣值时仍创建空折扣记录作为后续兜底。

## 改动文件列表

- `tasks/发布相似商品任务.py`
- `backend/services/任务参数服务.py`
- `tests/单元测试/测试_发布相似商品任务发布页等待.py`
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `tasks/发布相似商品任务.py`
  - 保留“等待发布页表单渲染”的关键元素等待逻辑
  - 删除 `await 发布页对象.关闭所有弹窗()`，避免在发布相似品页面误操作素材区域
- `backend/services/任务参数服务.py`
  - 调整 `批次完成后创建后续任务(batch_id)`：若成功记录中没有任何折扣值，也继续创建一条 `限时限量` 记录
  - 创建出的记录会把 `折扣` 写为 `None`，并打印“需手动补充”的提示日志
- `tests/单元测试/测试_发布相似商品任务发布页等待.py`
  - 更新断言，确认发布相似商品任务不再调用 `关闭所有弹窗()`
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
  - 更新异常路径断言，确认无折扣时仍会创建一条空折扣的 `限时限量` 记录
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 29 的实现范围与验证结果

## 影响范围

- 发布相似商品任务进入发布页后不再主动尝试关闭弹窗，降低误删图片或误点页面元素的风险
- 自动创建的 `限时限量` 后续任务覆盖面更宽：即使批次成功记录里没有折扣，也会先落一条待补参数记录，方便前端补值后重跑
- 后续任务未自动带出折扣时，日志会明确提示“折扣为空，需手动补充”

## 注意事项

- 本轮未修改 `pages/` 目录，也未修改 `selectors/` 目录的选择器值
- 空折扣的 `限时限量` 记录后续执行时会因任务内校验 `折扣不能为空` 而失败，这是预期行为，用户需要在前端补折扣后重置重跑
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_发布相似商品任务.py tests/单元测试/测试_发布相似商品任务发布页等待.py`，结果 `9 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_批次完成后自动创建限时限量.py tests/单元测试/测试_任务服务浏览器复用与后续任务.py tests/单元测试/测试_限时限量任务服务.py`，结果 `10 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `229 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 30：将任务链自动串联从“按批次完成后补一条后续任务”重构为“单条任务成功后立即按任务链映射创建下一步任务”，并将限时限量任务改为消费自身 params 的单商品模式。

## 改动文件列表

- `backend/services/任务服务.py`
- `backend/services/任务参数服务.py`
- `tasks/限时限量任务.py`
- `tests/单元测试/测试_任务服务浏览器复用与后续任务.py`
- `tests/单元测试/测试_限时限量任务.py`
- `tests/单元测试/测试_创建后续任务.py`
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/任务服务.py`
  - 顶部新增 `任务链映射`
  - 任务成功后不再按 `batch_id` 调用旧的批次级创建逻辑，改为按映射调用 `任务参数服务实例.创建后续任务(...)`
- `backend/services/任务参数服务.py`
  - 删除 `批次完成后创建后续任务(...)`
  - 新增 `创建后续任务(...)`，会继承源记录参数、合并执行结果、写入 `source_task_param_id`，并按 `source_task_param_id + task_name` 做幂等去重
- `tasks/限时限量任务.py`
  - 删除对 `查询批次成功记录(...)` 的依赖
  - 改为从自身 `task_param` 直接读取 `新商品ID / new_product_id` 和 `折扣 / discount`
  - 只处理单个商品，一条记录对应一次选品和一次创建
- `tests/单元测试/测试_任务服务浏览器复用与后续任务.py`
  - 更新为断言 `创建后续任务(...)` 的调用参数，而不是旧的批次级方法
- `tests/单元测试/测试_限时限量任务.py`
  - 更新为覆盖缺少新商品ID跳过、缺少折扣报错、单商品成功链路和失败链路
- `tests/单元测试/测试_创建后续任务.py`
  - 新增通用后续任务创建测试，覆盖正常路径、幂等路径和异常路径
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
  - 删除。该文件对应的旧批次级方法已移除，由 `测试_创建后续任务.py` 替代
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 30 的实现范围与验证结果

## 影响范围

- 发布相似商品成功后会立刻生成对应的下一步任务参数记录，不再依赖整批任务收尾
- 后续任务链条现在由 `任务链映射` 控制，后续新增 “限时限量 -> 推广” 这类链路时只需扩展映射和任务参数约定
- 限时限量任务的输入来源从“同批次聚合结果”变成“自身 params”，一条记录只驱动一个商品，链路更细粒度

## 注意事项

- 本轮未修改 `pages/` 与 `selectors/` 目录
- `查询批次成功记录(...)` 方法按要求保留，虽然 `限时限量任务.py` 已不再依赖它
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务服务浏览器复用与后续任务.py tests/单元测试/测试_创建后续任务.py`，结果 `10 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_限时限量任务.py tests/单元测试/测试_限时限量任务服务.py tests/单元测试/测试_任务参数批次成功记录.py`，结果 `9 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `227 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 31：新增 `flow_params` 流程级参数体系，支持 CSV/XLSX 按流程导入、步骤间共享上下文与结果回写，并将 flow 模式执行链路切换到 `flow_params`。

## 改动文件列表

- `backend/models/数据库.py`
- `backend/models/数据结构.py`
- `backend/services/流程参数服务.py`
- `backend/api/流程参数接口.py`
- `backend/api/路由注册.py`
- `backend/services/任务服务.py`
- `backend/services/执行服务.py`
- `tasks/执行任务.py`
- `tasks/限时限量任务.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/flowParams.ts`
- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_流程参数服务.py`
- `tests/单元测试/测试_流程参数接口.py`
- `tests/单元测试/测试_创建后续任务.py`
- `tests/单元测试/测试_任务服务.py`
- `tests/单元测试/测试_任务服务浏览器复用与后续任务.py`
- `tests/单元测试/测试_执行服务.py`
- `tests/单元测试/测试_执行任务.py`
- `tests/单元测试/测试_限时限量任务.py`
- `tests/单元测试/测试_批量执行店铺名.py`
- `tests/单元测试/测试_流程参数导入静态页.py`
- `tests/单元测试/测试_批次完成后自动创建限时限量.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/数据库.py`
  - 新增 `flow_params` 表，承载流程共享参数、步骤结果、当前步骤、批次和启用态
- `backend/models/数据结构.py`
  - 新增流程参数相关请求/响应模型
- `backend/services/流程参数服务.py`
  - 新建流程参数服务，覆盖 CRUD、分页、导入、步骤上下文合并、步骤结果回写、状态更新和批量操作
  - 导入逻辑直接复用 `任务参数服务` 的列名映射、店铺解析、发布次数展开和 CSV/XLSX 解析能力
- `backend/api/流程参数接口.py` / `backend/api/路由注册.py`
  - 新增并注册 `/api/flow-params` REST API
- `backend/services/任务服务.py`
  - 当 `店铺配置` 中已有 `flow_context` 时直接透传为 `task_param`，避免误查 `task_params`
- `backend/services/执行服务.py`
  - flow 模式创建批次时改读 `flow_params` 待执行记录
  - 对无待执行 `flow_params` 的店铺静默跳过
  - 向每个 Celery step 透传 `flow_param_id`
- `tasks/执行任务.py`
  - 新增 `flow_param_id` 参数
  - 执行前读取 `flow_context` 并把 `flow_params` 置为 `running`
  - 成功后回写 `step_results`，最后一步成功时把 `flow_params` 置为 `success`
- `tasks/限时限量任务.py`
  - 改为从自身 `task_param` 读取 `新商品ID / 折扣`
  - 一条记录只处理一个商品，不再按批次查询成功结果
- `frontend/src/api/types.ts` / `frontend/src/api/flowParams.ts`
  - 新增 `FlowParam` 相关类型与 flow params API 封装
- `frontend/src/views/TaskParamsManage.vue`
  - 导入弹窗新增“绑定任务 / 绑定流程”模式切换
  - 绑定流程时读取流程列表并调用 `importFlowParams(...)`
- `tests/...`
  - 新增 flow params 服务/API/静态页测试
  - 更新执行服务、执行任务、任务服务、限时限量任务等测试以适配 flow params 链路
  - 删除旧的批次级后续任务测试文件，由通用后续任务创建测试替代
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 31 的实现范围与验证结果

## 影响范围

- 流程执行现在可以绑定 `flow_params` 共享参数，步骤间通过 `step_results` 自动传递结果
- 单任务执行仍走 `task_params`，与 `flow_params` 互不干扰
- flow 模式批次只会为存在待执行 `flow_params` 的店铺投递链路
- 前端导入弹窗现在支持直接把 CSV/XLSX 绑定到流程，而不是只能绑定单个任务

## 注意事项

- 本轮未修改 `pages/` 与 `selectors/` 目录
- 删除了 `tests/单元测试/测试_批次完成后自动创建限时限量.py`；该文件对应的旧批次级后续任务方法已移除
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_流程参数服务.py tests/单元测试/测试_流程参数接口.py tests/单元测试/测试_创建后续任务.py tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务服务浏览器复用与后续任务.py tests/单元测试/测试_执行服务.py tests/单元测试/测试_执行任务.py tests/单元测试/测试_限时限量任务.py tests/单元测试/测试_限时限量任务服务.py tests/单元测试/测试_任务参数批次成功记录.py tests/单元测试/测试_流程参数导入静态页.py`，结果 `38 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果 `238 passed, 16 warnings`
- 已执行 `npx vue-tsc -b`（`frontend/` 目录），结果通过
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 32：为任务参数管理页新增“流程参数”Tab，展示 `flow_params` 数据并支持筛选、分页、单条/批量操作，同时修复 flow 模式导入后不刷新的问题。

## 改动文件列表

- `frontend/src/api/flowParams.ts`
- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_流程参数管理页静态.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/api/flowParams.ts`
  - 补充 `resetFlowParam`、`enableFlowParam`、`disableFlowParam`
  - 单条操作通过 `updateFlowParam(...)` 退化实现，以兼容当前后端接口能力
- `frontend/src/views/TaskParamsManage.vue`
  - 将 `TabKey` 扩展为 `taskList | resultList | flowParams`
  - 新增流程参数列表状态、筛选状态、分页状态和 `loadFlowParams(...)`
  - 新增“流程参数”Tab、筛选栏、表格、toolbar 与分页分支
  - 表格复用现有 `StatusBadge`、JSON tooltip、启用开关和按钮样式
  - 导入成功后，若当前为绑定流程模式，会自动 `loadFlowParams(1)` 并切换到 `flowParams` Tab
  - header 区域在 `flowParams` Tab 也显示“清空 / 导入CSV”按钮
- `tests/单元测试/测试_流程参数管理页静态.py`
  - 新增静态回归，覆盖 flowParams API 方法、流程参数 Tab、筛选/列表/批量操作和导入后自动切换刷新
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 32 的实现范围与验证结果

## 影响范围

- 任务参数管理页现在可以直接查看、筛选和维护 `flow_params` 记录，不需要额外页面
- 绑定流程导入成功后会立即看到导入结果，减少重复手动切 Tab 刷新的操作
- 任务参数页现有“任务列表 / 执行结果”逻辑保持不变，只新增了第三个 flow params 视图分支

## 注意事项

- 本轮按要求未修改任何后端代码
- `flowParams.ts` 的单条 reset/enable/disable 目前通过 `PUT /api/flow-params/{id}` 退化实现；若后端未来补单独接口，可直接切换
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数管理页.py tests/单元测试/测试_流程参数导入静态页.py tests/单元测试/测试_流程参数管理页静态.py`，结果 `7 passed`
- 已执行 `npx vue-tsc -b`（`frontend/` 目录），结果通过
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `240 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 33：将 Celery Worker 的任务执行从进程内直调改为通过 HTTP 委托主进程执行，避免双进程争抢 Chrome profile 导致的浏览器冲突。

## 改动文件列表

- `backend/配置.py`
- `backend/api/任务接口.py`
- `tasks/执行任务.py`
- `tests/单元测试/测试_任务接口内部执行.py`
- `tests/单元测试/测试_执行任务.py`
- `tests/单元测试/测试_批量执行店铺名.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/配置.py`
  - 新增 `API_BASE_URL` 配置项，用于 Worker 访问主进程
- `backend/api/任务接口.py`
  - 新增内部接口 `POST /api/tasks/execute-internal`
  - 接口会创建任务日志，调用主进程任务执行链路，并等待执行完成后同步返回结果
  - 对 `flow_param_id` 场景，内部接口在主进程侧负责读取 `flow_context`、回写 `step_results` 与更新流程状态
- `tasks/执行任务.py`
  - 去掉 Worker 直调 `任务服务实例.统一执行任务()` 的主流程
  - 改为通过 `httpx.Client` 调用主进程内部执行接口
  - 保留 Worker 端 `abort / continue / retry` 策略判断与 Redis 批次状态更新
  - 为兼容既有测试，补回 `_运行异步任务` 和 `_在线程中执行临时协程` helper，但主流程已不再使用
- `tests/单元测试/测试_任务接口内部执行.py`
  - 新增内部执行接口的正常路径与异常路径测试
- `tests/单元测试/测试_执行任务.py`
  - 更新为覆盖 HTTP 委托后的 Worker 执行逻辑
- `tests/单元测试/测试_批量执行店铺名.py`
  - 更新为断言 Worker 通过 HTTP 调用时仍会正确传递 `shop_name`
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 33 的实现范围与验证结果

## 影响范围

- Celery Worker 不再在自身进程里打开浏览器或争抢 Chrome profile，浏览器实际操作统一回到 FastAPI 主进程
- 批量链路的 `on_fail` 策略仍然在 Worker 端判断，原有 Redis 批次状态推送逻辑保持不变
- flow 模式下，步骤上下文读取与结果回写也迁移到了主进程内部执行接口侧，避免 Worker 端再碰浏览器执行链路

## 注意事项

- 本轮未修改任何前端代码
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_执行任务.py tests/单元测试/测试_任务接口内部执行.py tests/单元测试/测试_批量执行店铺名.py`，结果 `13 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_执行服务.py tests/单元测试/测试_任务服务.py`，结果 `11 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_线程池事件循环.py`，结果 `4 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `242 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 Task 34：新增“设置推广”任务，包括推广页选择器、推广页 POM、推广任务编排，以及 `任务服务` 对该任务的 task_params 注入接入。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tasks/推广任务.py`
- `backend/services/任务服务.py`
- `tests/单元测试/测试_推广页.py`
- `tests/单元测试/测试_推广任务.py`
- `tests/单元测试/测试_推广任务服务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 新增推广页静态选择器和按商品ID动态生成的选择器方法
- `pages/推广页.py`
  - 新建推广页 POM，拆分为导航、弹窗、查询、全选、投产设置、开启推广、成功等待和返回商品列表页等原子方法
  - 每个方法内都带 `0.5~1.5s` 随机延迟，保持页面操作节奏一致
- `tasks/推广任务.py`
  - 新建 `"设置推广"` 任务，按任务单要求编排整条推广流程
  - 支持从参数中读取商品ID列表、一阶段投产比和二阶段投产比
  - 对投产比受限商品会取消设置并取消勾选，最终回写成功/失败商品列表
- `backend/services/任务服务.py`
  - 将 `"设置推广"` 纳入 `任务参数任务集合`
- `tests/单元测试/测试_推广页.py`
  - 覆盖推广页原子方法与兜底行为
- `tests/单元测试/测试_推广任务.py`
  - 覆盖任务注册、正常路径和异常路径
- `tests/单元测试/测试_推广任务服务.py`
  - 覆盖任务服务对 `"设置推广"` 的参数注入与跳过逻辑
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 34 的实现范围与验证结果

## 影响范围

- 项目新增 `"设置推广"` 任务后，可通过现有 task_params 链路驱动全站推广设置
- 推广页流程中的弹窗处理、商品查询、投产比设置和开启推广已拆为独立页面动作，便于后续维护
- 现有任务链路未被改动，仅新增新任务及其执行入口接入

## 注意事项

- 本轮未修改前端代码
- 本轮未改动任何已有任务的业务流程
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `11 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务注册表.py`，结果 `11 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `253 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成推广页改版重写：按新版拼多多推广页面结构重写推广页选择器、推广页 POM 原子方法和“设置推广”任务编排。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tasks/推广任务.py`
- `tests/单元测试/测试_推广页.py`
- `tests/单元测试/测试_推广任务.py`
- `tests/单元测试/测试_推广任务服务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 按新版页面结构重写全部推广页选择器
  - 新增新版 `预算日限额` 与 `极速起量高级版` 相关定位
  - 动态选择器按商品ID返回 `商品行容器 / 修改投产铅笔按钮 / 更多设置按钮 / 极速起量高级版开关`
- `pages/推广页.py`
  - 重写为新版原子方法接口
  - 删除旧的全选、二阶段投产比和投产比限制相关方法
  - 增加商品行存在检查、日限额设置、投产弹窗等待、极速起量高级版状态判断和新版投产确认逻辑
- `tasks/推广任务.py`
  - 按新版 10 步流程重写任务编排
  - 取消旧的“全选模式”和二阶段投产比
  - 新增可选 `日限额` 设置
  - 新增 `关闭极速起量` 参数控制是否关闭“极速起量高级版”
  - 结果结构调整为 `推广商品数 / 成功列表 / 失败列表 / 投产比 / 日限额`
- `tests/单元测试/测试_推广页.py`
  - 更新为覆盖新版页面原子方法
- `tests/单元测试/测试_推广任务.py`
  - 更新为覆盖新版成功与异常路径
- `tests/单元测试/测试_推广任务服务.py`
  - 更新注入参数断言，匹配新版 `投产比 / 日限额`
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录本轮推广页改版重写与验证结果

## 影响范围

- `"设置推广"` 任务现在适配新版拼多多推广页面结构，不再依赖已经下线的全选和二阶段投产流程
- 日限额设置和极速起量高级版开关控制已纳入任务编排，可由任务参数驱动
- 推广页操作被重新拆成更符合当前页面结构的原子方法，后续维护定位会更直接

## 注意事项

- 本轮未修改前端代码
- 本轮未改动其他已有任务的逻辑
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `12 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务注册表.py`，结果 `11 passed`
- 已执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `254 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示

---

## 任务摘要

完成 ask 36：为 flow 执行框架接入同步屏障与合并执行，限时限量改为逐商品折扣输入，并在前端补齐 `barrier/merge` 编辑与 `step_results` 执行结果展示。

## 改动文件列表

- `backend/api/任务接口.py`
- `backend/models/数据结构.py`
- `backend/models/流程模型.py`
- `backend/services/任务服务.py`
- `backend/services/执行服务.py`
- `backend/services/流程参数服务.py`
- `frontend/src/api/types.ts`
- `frontend/src/views/FlowManage.vue`
- `frontend/src/views/TaskParamsManage.vue`
- `pages/限时限量页.py`
- `selectors/限时限量页选择器.py`
- `tasks/推广任务.py`
- `tasks/限时限量任务.py`
- `tests/单元测试/测试_任务接口内部执行.py`
- `tests/单元测试/测试_前端显示细节.py`
- `tests/单元测试/测试_前端管理页.py`
- `tests/单元测试/测试_店铺和流程接口.py`
- `tests/单元测试/测试_执行服务.py`
- `tests/单元测试/测试_批量执行回调.py`
- `tests/单元测试/测试_批量执行店铺名.py`
- `tests/单元测试/测试_推广任务.py`
- `tests/单元测试/测试_数据库模型.py`
- `tests/单元测试/测试_流程参数服务.py`
- `tests/单元测试/测试_流程参数管理页静态.py`
- `tests/单元测试/测试_限时限量任务.py`
- `tests/单元测试/测试_限时限量页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/流程模型.py` / `backend/models/数据结构.py`
  - 为流程步骤补齐 `barrier` / `merge` 字段，并在后端响应结构中持久化返回
- `backend/services/执行服务.py`
  - 将 flow 批次调度从整条 `celery chain` 改为单步投递
  - flow 模式下会把同店铺全部待执行 `flow_params` 记录挂到同一 `batch_id` 下的首步任务
  - 新增 `投递单步任务(...)` 供创建批次和后续步骤推进共用
- `backend/services/流程参数服务.py`
  - `step_results` 改为结构化步骤状态
  - 新增同批次步骤状态查询和批量推进到下一步能力
  - `获取步骤上下文(...)` 过滤步骤元数据，避免 `status` 等控制字段进入任务参数
- `backend/services/任务服务.py`
  - 新增 flow 步骤完成后的 barrier / merge 推进逻辑
  - 当前步骤完成后会按步骤配置决定等待、合并或直接投递下一步
  - 合并执行时会构造 `商品ID列表 + 商品参数映射`，并按商品逐条回写执行结果
- `backend/api/任务接口.py`
  - 内部执行接口改为在步骤开始时标记 `running`，结束后统一委托 `任务服务` 处理 flow 推进
- `selectors/限时限量页选择器.py` / `pages/限时限量页.py` / `tasks/限时限量任务.py`
  - 删除批量折扣相关选择器与 POM 方法
  - 新增逐商品折扣输入选择器和原子页面方法
  - 限时限量任务改为逐商品选品、逐商品折扣输入
- `tasks/推广任务.py`
  - 增加 merge 参数兼容，可按商品从 `商品参数映射` 读取独立的 `投产比 / 日限额`
- `frontend/src/views/FlowManage.vue` / `frontend/src/api/types.ts`
  - 步骤编辑区新增“同步屏障”“合并执行”开关，并实现 `merge` 依赖 `barrier` 的联动
- `frontend/src/views/TaskParamsManage.vue`
  - 流程参数 Tab 将 `step_results` 改为 tag 化执行结果展示，支持展开查看每步明细
- `tests/...`
  - 同步更新执行服务、流程参数服务、内部执行接口、限时限量、推广任务及前端静态测试
  - 更新既有流程接口和数据库模型测试，适配 `barrier=false / merge=false` 的默认回传

## 影响范围

- flow 执行链路现在支持等待同批次同步屏障，并支持将下一步合并为单次执行
- `flow_params.step_results` 会记录每一步的运行、完成、失败、等待屏障和聚合跳过状态，前端可直接查看
- 限时限量任务不再依赖统一折扣输入，后续可以按商品维度配置折扣
- 设置推广任务已兼容 merge 输入格式，可按商品读取各自的投产比和日限额

## 注意事项

- 本轮额外修改了 `backend/models/流程模型.py`、`backend/api/任务接口.py` 和 `tasks/推广任务.py`，这是实现 ask 36 所需的最小联动范围
- 已执行针对性回归：`40 passed`
- 已执行邻近回归：`22 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `257 passed, 16 warnings`
- 已执行前端类型检查：`cd frontend && npx vue-tsc -b`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 37：修复屏障模式下同店铺多条 `flow_params` 重复投递多个 Celery 子任务的问题，改为同店铺只投递 1 个 Celery 任务并在主进程内循环处理。

## 改动文件列表

- `backend/services/执行服务.py`
- `backend/services/任务服务.py`
- `tasks/执行任务.py`
- `tests/单元测试/测试_执行服务.py`
- `tests/单元测试/测试_执行任务.py`
- `tests/单元测试/测试_任务服务.py`
- `tests/单元测试/测试_批量执行店铺名.py`
- `tests/单元测试/测试_批量执行回调.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/执行服务.py`
  - `投递单步任务(...)` 增加 `flow_param_ids` 和 `merge`
  - flow 模式下，当步骤 `barrier=true` 或 `merge=true` 时，同店铺只投递 1 个 Celery 任务
  - 首步 barrier/merge 现在也遵守这一规则，不再首步就拆成多条 Worker 子任务
- `tasks/执行任务.py`
  - Worker 任务签名兼容 `flow_param_ids: list[int]` 和 `merge: bool`
  - 多记录模式会把 `flow_param_ids` 放进 `params` 透传给主进程
  - 旧 `flow_param_id` 单条模式保持兼容
- `backend/services/任务服务.py`
  - `执行任务()` 新增多记录 flow 执行分支
  - barrier-only 模式下，会在同一页面对象上串行执行多条记录，并在记录之间随机等待 `2~5` 秒
  - merge 模式下，只调用一次具体任务，随后复用已有步骤完成逻辑统一回写所有记录
  - 某条记录失败时按 `on_fail` 决定继续或中断；`abort` 时剩余未执行记录会被标记为失败终止
  - 具体任务文件无需改动，发布相似商品 / 限时限量 / 设置推广继续由框架层循环驱动
- `tests/...`
  - 更新执行服务测试，验证 barrier 首步同店铺只投递 1 个任务
  - 更新 Worker 测试，验证 `flow_param_ids / merge` 透传
  - 更新任务服务测试，覆盖 barrier-only 循环执行、merge 单次执行和 abort 终止路径
  - 更新店铺名与批次回调相关测试，适配新投递参数

## 影响范围

- 屏障模式下，同店铺同批次不再产生成倍的 Celery 子任务，Worker 数量和调度开销会下降
- barrier-only 步骤现在会在主进程内复用同一个浏览器页面处理多条记录，避免重复打开页面
- merge 模式继续保持“只执行一次任务”的语义，但投递侧也同步收敛成 1 个 Celery 任务

## 注意事项

- 本轮未修改前端代码
- 本轮未修改具体任务文件实现，变更集中在执行框架和 Worker 参数透传
- 已执行针对性回归：`34 passed`
- 已执行邻近回归：`26 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `261 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38：修复推广页全局起量和极速起量的确认弹窗链路，并让极速起量严格按参数决定关闭或开启。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tasks/推广任务.py`
- `tests/单元测试/测试_推广页.py`
- `tests/单元测试/测试_推广任务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 新增 `全局起量关闭确认按钮`
  - 新增 `极速起量高级版关闭确认按钮`
  - 按任务单要求使用固定 XPath 主选择器与备用选择器
- `pages/推广页.py`
  - 新增 `确认关闭全局起量()`
  - 新增 `确认关闭极速起量()`
  - 两个方法都会先等待确认按钮出现，再点击确认，并在点击后等待 `1~2` 秒
  - 两个方法等待超时统一为 `5` 秒，失败时会截图并返回 `False`
- `tasks/推广任务.py`
  - 关闭全局起量改为：点击开关后调用确认方法
  - `关闭极速起量` 参数读取顺序改为：`关闭极速起量` → `close_fast_boost`
  - 极速起量逻辑改为按当前状态和参数要求分别处理关闭、开启或不操作
- `tests/单元测试/测试_推广页.py`
  - 新增全局起量确认弹窗成功路径测试
  - 新增极速起量确认弹窗超时截图测试
- `tests/单元测试/测试_推广任务.py`
  - 更新正常路径，断言会调用两个确认方法
  - 新增全局起量确认失败返回失败的测试
  - 新增 `close_fast_boost=false` 时开启极速起量的测试

## 影响范围

- 推广任务关闭全局起量时，现在会正确处理“确定关闭”确认弹窗
- 推广任务关闭极速起量时，现在会正确处理关闭确认弹窗
- 当参数要求开启极速起量时，任务会在当前关闭状态下主动打开该开关

## 注意事项

- 本轮未修改其他页面、选择器或任务逻辑
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `17 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `265 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 39：修复推广页极速起量关闭确认弹窗的双形态兼容，并明确保证“先关极速起量，再填投产比”。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tasks/推广任务.py`
- `tests/单元测试/测试_推广页.py`
- `tests/单元测试/测试_推广任务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 保留原有通用极速起量确认按钮作为形态1
  - 新增 `获取极速起量高级版关闭确认按钮(商品ID)`，支持按商品ID匹配 `assist_close_{商品ID}` 的形态2
- `pages/推广页.py`
  - `确认关闭极速起量()` 改为 `确认关闭极速起量(商品ID)`
  - 实现双形态尝试：
    - 先尝试商品绑定确认按钮
    - 未命中后再回退通用确认按钮
  - 两种形态单次等待超时统一为 `2` 秒
  - 两种形态点击成功后都保留 `1~2` 秒随机等待
  - 两种形态都失败时截图并返回 `False`
- `tasks/推广任务.py`
  - 关闭极速起量时改为传入 `商品ID` 调用确认方法
  - 保持操作顺序为：点击铅笔按钮 → 关闭极速起量 → 填写投产比 → 点击确定
- `tests/单元测试/测试_推广页.py`
  - 新增商品绑定按钮优先命中的测试
  - 新增商品绑定失败后回退通用按钮的测试
  - 新增双形态都失败时截图的测试
- `tests/单元测试/测试_推广任务.py`
  - 更新正常路径断言，确认 `确认关闭极速起量` 会传入商品ID
  - 新增顺序测试，验证关闭极速起量发生在填写投产比之前

## 影响范围

- 极速起量关闭确认弹窗现在兼容两种页面形态，降低关闭失败导致的推广设置中断
- 推广任务在关闭极速起量后才会填写投产比，避免弹窗刷新打断投产输入

## 注意事项

- 本轮未修改全局起量确认弹窗逻辑
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `20 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `268 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38.2：移除极速起量关闭确认中误匹配投产比弹窗“确定”按钮的选择器，只保留“确定关闭”精确匹配和商品绑定按钮。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tasks/推广任务.py`
- `tests/单元测试/测试_推广页.py`
- `tests/单元测试/测试_推广任务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 将极速起量固定确认按钮改为只匹配“确定关闭”
  - 完全移除包含 `span[text()="确定"]` 的极速起量确认选择器
  - 保留按商品ID匹配 `assist_close_{商品ID}` 的动态确认按钮
- `pages/推广页.py`
  - `确认关闭极速起量(商品ID)` 继续优先尝试商品绑定形态
  - 回退逻辑只尝试固定“确定关闭”按钮，不再尝试任何通用“确定”
  - 双形态都失败时截图名改为 `极速起量确认弹窗未找到`
- `tasks/推广任务.py`
  - 保持“关极速起量后再填投产比”的顺序不变
  - 修正 `确认投产比设置(...)` 调用，补传 `商品ID`
- `tests/单元测试/测试_推广页.py`
  - 新增断言，确保极速起量固定确认选择器不再匹配通用“确定”
  - 更新回退路径测试，改为匹配新的“确定关闭”固定选择器
  - 更新失败截图断言
- `tests/单元测试/测试_推广任务.py`
  - 在正常路径中新增 `确认投产比设置(商品ID)` 的断言

## 影响范围

- 极速起量关闭确认弹窗不再误点投产比弹窗底部的“确定”按钮
- 推广任务关闭极速起量后的投产设置链路更稳定
- 每个商品的投产确认按钮现在显式绑定商品ID调用

## 注意事项

- 本轮未修改全局起量确认弹窗逻辑
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `21 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `269 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38.3：为极速起量关闭确认补充第三种 `popover` 气泡弹窗形态，并将其作为前两种失败后的精确回退。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tests/单元测试/测试_推广页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 新增 `极速起量高级版关闭确认按钮_Popover`
  - 主用和备用选择器都限定在 `anq-popover-footer` / `anq-popover-inner` 容器内，避免误匹配投产比弹窗
- `pages/推广页.py`
  - `确认关闭极速起量(商品ID)` 现在按三形态依次尝试：
    - 商品绑定按钮 `assist_close_{商品ID}`
    - 固定“确定关闭”按钮
    - `popover` 气泡弹窗内主按钮
  - 第三形态也沿用 `2` 秒等待超时和点击后 `1~2` 秒随机等待
  - 三形态都失败时仍截图 `极速起量确认弹窗未找到`
- `tests/单元测试/测试_推广页.py`
  - 新增断言，验证 popover 选择器限定在 `anq-popover-footer` 容器内
  - 新增“前两种失败后回退 popover 成功”的测试
  - 原有失败路径和双形态逻辑保持覆盖

## 影响范围

- 极速起量关闭确认弹窗现在兼容第三种 `popover` 气泡形态
- 当前两种确认按钮形态都不存在时，推广任务仍可通过 `popover` 形态继续完成关闭操作
- `popover` 选择器受容器限制，不会回退成误点投产比弹窗底部按钮

## 注意事项

- 本轮未修改任务编排顺序或其他任务逻辑
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `23 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `271 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38.4：将极速起量确认弹窗的三形态优先级更新为“商品绑定按钮 → popover 内确定 → 任意确定关闭按钮”，并把商品绑定匹配改成 `contains(data-testid)`。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tests/单元测试/测试_推广页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - `获取极速起量高级版关闭确认按钮(商品ID)` 改为 `contains(@data-testid, "assist_close") and contains(@data-testid, "{商品ID}")`
  - `极速起量高级版关闭确认按钮_Popover` 主用选择器改为限定在 `anq-popover` 容器内的主按钮
  - `极速起量高级版关闭确认按钮` 保留为兜底的任意 `确定关闭` 按钮
- `pages/推广页.py`
  - `确认关闭极速起量(商品ID)` 的优先级更新为：
    - 商品绑定按钮
    - `anq-popover` 内的主按钮
    - 任意 `确定关闭` 按钮
  - 三种形态仍使用 `2` 秒等待超时和点击后 `1~2` 秒延时
- `tests/单元测试/测试_推广页.py`
  - 新增断言验证商品绑定形态使用 `contains(@data-testid, "assist_close")`
  - 更新回退顺序测试，确认前两种失败后才进入兜底 `确定关闭`
  - 更新 popover 容器断言，确认选择器限定在 `anq-popover` 范围内

## 影响范围

- 极速起量确认弹窗现在按最新优先级匹配，优先使用更精确的商品绑定形态
- `popover` 形态会先于普通 `确定关闭` 按钮尝试，减少在混合弹窗场景下的误点概率

## 注意事项

- 本轮未修改任务编排、任务参数或其他任务文件
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `24 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `272 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38.5：修正限时限量逐商品折扣输入框主选择器，并将推广成功检测改为多条件轮询命中。

## 改动文件列表

- `selectors/限时限量页选择器.py`
- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tests/单元测试/测试_限时限量页.py`
- `tests/单元测试/测试_推广页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/限时限量页选择器.py`
  - `商品行折扣输入框(商品ID)` 的主用选择器增加 `@placeholder="1～9.7"`，避免命中错误输入框
- `selectors/推广页选择器.py`
  - 新增 `推广成功Toast提示`
  - 新增 `推广中状态文案`
  - 保留现有 `开启推广按钮` 供“按钮消失”条件复用
- `pages/推广页.py`
  - `等待推广成功()` 从单个 `wait_for_selector` 改为最长 15 秒的轮询
  - 轮询中依次检查：
    - 成功 Toast
    - URL 是否已回到列表页
    - 开启推广按钮是否消失
    - 页面是否出现“推广中”
  - 任一条件满足即返回成功
  - 超时后截图 `推广成功检测超时`
- `tests/单元测试/测试_限时限量页.py`
  - 新增断言，确保折扣输入框主选择器带 `placeholder="1～9.7"`
- `tests/单元测试/测试_推广页.py`
  - 新增 Toast 命中即成功的测试
  - 新增开启推广按钮消失即成功的测试
  - 新增成功检测超时截图的测试

## 影响范围

- 限时限量逐商品折扣输入更精确，降低命中到错误数字输入框的概率
- 推广成功检测不再依赖单一提示，网络慢或页面跳转慢时成功判定更稳
- 推广页在回到列表页、按钮消失或状态变成“推广中”时都能被识别为成功

## 注意事项

- 本轮按任务单要求修改的是实际存在的文件 `selectors/限时限量页选择器.py`；任务单中的 `selectors/限时限量选择器.py` 为现有仓库命名差异
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_限时限量页.py tests/单元测试/测试_推广页.py`，结果 `22 passed`
- 已执行邻近回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `11 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `276 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38.7：用“极速起量”标题作为弹窗锚点统一匹配确认按钮，收敛极速起量确认弹窗的多段回退逻辑。

## 改动文件列表

- `selectors/推广页选择器.py`
- `pages/推广页.py`
- `tests/单元测试/测试_推广页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - 删除原来分散的极速起量确认弹窗静态选择器定义
  - 将 `获取极速起量高级版关闭确认按钮(商品ID)` 改为统一返回一组候选选择器
  - 主用选择器先锚定 `anq-popover` 容器里包含“极速起量”的标题，再在容器内匹配主按钮或“确定关闭”按钮
  - 备用选择器保留 `assist_close + 商品ID` 和全局 `确定关闭`
- `pages/推广页.py`
  - `确认关闭极速起量(商品ID)` 简化为一个循环遍历 `获取极速起量高级版关闭确认按钮(商品ID).所有选择器()`
  - 每个候选选择器等待和点击超时统一为 `3000ms`
  - 成功后仍会执行确认后的 `1~2` 秒等待，失败时仍截图 `极速起量确认弹窗未找到`
- `tests/单元测试/测试_推广页.py`
  - 新增主用选择器包含“极速起量”标题锚点的断言
  - 新增统一选择器组顺序断言
  - 更新确认关闭极速起量的命中、回退和失败路径测试，适配单循环实现和 3 秒超时

## 影响范围

- 极速起量确认弹窗现在优先在“极速起量”标题所在的 popover 容器内找确认按钮，误匹配其他弹窗的概率更低
- POM 侧不再维护三段分支逻辑，后续维护只需更新统一选择器方法

## 注意事项

- 本轮未修改推广任务编排逻辑
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `26 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `275 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 38.8：将极速起量确认按钮选择器替换为 `assist_close → 确定关闭 → anq-flex 内确定` 的三候选顺序。

## 改动文件列表

- `selectors/推广页选择器.py`
- `tests/单元测试/测试_推广页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/推广页选择器.py`
  - `获取极速起量高级版关闭确认按钮(商品ID)` 改为：
    - 主用：`//button[contains(@data-testid, "assist_close") and contains(@data-testid, "{商品ID}")]`
    - 备用1：`//button[.//span[text()="确定关闭"]]`
    - 备用2：`//div[contains(@class, "anq-flex")]/button[normalize-space(.)="确定"]`
  - 保留“确定关闭”的两个选择器
  - 新增的“确定”选择器限定在 `anq-flex` 容器内
- `tests/单元测试/测试_推广页.py`
  - 更新主用选择器断言，改为校验 `assist_close + 商品ID`
  - 更新候选顺序断言，改为 `assist_close -> 确定关闭 -> anq-flex 内确定`
  - 更新回退路径测试，验证前两种失败后才进入 `anq-flex` 容器内的 `确定`

## 影响范围

- 极速起量确认按钮现在按任务单要求切回更直接的三候选顺序
- `anq-flex` 容器限定仍能避免将最后一个“确定”回退到无关区域

## 注意事项

- 本轮未修改 `pages/推广页.py` 和任务编排逻辑；现有单循环遍历 `所有选择器()` 的实现可直接复用新顺序
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_推广页.py tests/单元测试/测试_推广任务.py tests/单元测试/测试_推广任务服务.py`，结果 `26 passed`
- 已执行全量测试：首次全量回归命中过一条已知计时精度波动用例，单独复跑通过后再次执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `275 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 39：让前端点击“停止”后通过 Redis 取消标记在操作边界真正停止，不再继续下一条任务或下一步投递。

## 改动文件列表

- `backend/services/执行服务.py`
- `backend/services/任务服务.py`
- `tasks/执行任务.py`
- `tests/单元测试/测试_执行服务.py`
- `tests/单元测试/测试_执行任务.py`
- `tests/单元测试/测试_任务服务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/执行服务.py`
  - 新增批次取消标记 Redis 键前缀 `execute:cancel:{batch_id}`
  - 新增同步/异步版本的取消标记读写函数
  - `停止批次()` 会在 `revoke` 前先写入取消标记，TTL 为 `3600` 秒
- `backend/services/任务服务.py`
  - 新增 `_已收到批次取消(...)` 和统一的取消返回结构
  - 单任务执行前检查取消标记，命中后直接返回 `cancelled`
  - barrier 循环模式在每条记录前和记录完成后检查取消标记
  - flow 步骤完成后若批次已取消，则不再推进下一步
  - `统一执行任务()` 在真正执行任务前检测取消并将任务日志写为 `cancelled`
- `tasks/执行任务.py`
  - HTTP 委托返回后新增同步取消标记检查
  - 批次已取消时，将店铺状态写为 `stopped`，并返回 `cancelled`
- `tests/单元测试/测试_执行服务.py`
  - 新增断言验证 `停止批次()` 会写入取消标记
- `tests/单元测试/测试_执行任务.py`
  - 新增 Worker 在 HTTP 返回后检测到取消时返回 `cancelled` 的测试
- `tests/单元测试/测试_任务服务.py`
  - 新增单任务执行前取消测试
  - 新增 barrier 循环执行中第一条完成后取消、不再继续下一条的测试
  - 新增 `统一执行任务()` 执行前取消时写为 `cancelled` 的测试

## 影响范围

- 前端点击“停止”后，不再只依赖 `revoke`，主进程和 Worker 都能看到同一份取消标记
- 当前页面操作允许完成，但后续不会再继续下一条记录或下一步流程
- 批量执行页的店铺状态会在取消后写成 `stopped`

## 注意事项

- 本轮未使用 `revoke(terminate=True)`，避免强杀进程导致浏览器残留
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_执行服务.py tests/单元测试/测试_执行任务.py tests/单元测试/测试_任务服务.py tests/单元测试/测试_任务服务浏览器复用与后续任务.py`，结果 `27 passed`
- 已执行邻近回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_批量执行回调.py tests/单元测试/测试_批量执行店铺名.py tests/单元测试/测试_执行任务.py tests/单元测试/测试_流程参数服务.py tests/单元测试/测试_任务接口内部执行.py`，结果 `24 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `279 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 ask 40：前端系统设置页新增机器码配置，并修复执行结果 Tab 对 flow 执行结果的展示。

## 改动文件列表

- `backend/services/系统服务.py`
- `backend/api/任务参数接口.py`
- `frontend/src/api/taskParams.ts`
- `frontend/src/api/mock.ts`
- `frontend/src/views/Settings.vue`
- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_系统设置机器码.py`
- `tests/单元测试/测试_任务参数执行结果接口.py`
- `tests/单元测试/测试_任务参数管理页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/系统服务.py`
  - 配置白名单新增 `agent_machine_id`
  - `获取配置()` 返回中新增 `agent_machine_id`
- `frontend/src/views/Settings.vue`
  - 设置页新增“机器码”输入框
  - 保存提示补充“修改后需重启 Worker 生效”
  - 基础配置数据模型和加载逻辑同步接入 `agent_machine_id`
- `backend/api/任务参数接口.py`
  - 新增 `/api/task-params/results`
  - 接口会合并查询 `task_params` 与 `flow_params`
  - flow 结果会从 `step_results` 中提取业务字段，并映射成前端当前结果表结构
  - 支持按店铺、任务类型、状态、批次、更新时间范围筛选，并支持分页
- `frontend/src/api/taskParams.ts`
  - 新增 `listTaskParamResults(...)`
- `frontend/src/views/TaskParamsManage.vue`
  - 执行结果 Tab 改为调用 `listTaskParamResults(...)`
  - 执行状态筛选新增 `running` / `cancelled`
  - 结果列表 key 改为组合键，避免合并 `task_params` 与 `flow_params` 后的重复 key
- `frontend/src/api/mock.ts`
  - 补充 `agent_machine_id` mock 字段
- `tests/单元测试/测试_系统设置机器码.py`
  - 覆盖机器码静态页面内容
  - 覆盖系统服务对 `agent_machine_id` 的读写与未知字段异常路径
- `tests/单元测试/测试_任务参数执行结果接口.py`
  - 覆盖执行结果接口合并返回 `task_params` 与 `flow_params`
  - 覆盖按任务类型筛选 flow 结果
- `tests/单元测试/测试_任务参数管理页.py`
  - 补充结果 Tab 依赖 `listTaskParamResults` 的静态断言

## 影响范围

- 设置页现在可以直接配置机器码，并写回 `.env` 与运行时配置
- 执行结果 Tab 不再只显示旧的 `task_params` 结果，流程模式写入的 `flow_params` 结果现在也能展示
- flow 执行结果支持按店铺、状态、任务类型、批次和日期筛选

## 注意事项

- 机器码为空时，运行时仍会沿用现有默认值 `default`
- 机器码修改后需要重启 Worker 才会影响队列名称
- 本轮没有删除旧的 `task_params` 列表接口，任务列表和旧数据仍保持兼容
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_系统设置机器码.py tests/单元测试/测试_任务参数执行结果接口.py tests/单元测试/测试_任务参数管理页.py tests/单元测试/测试_流程参数管理页静态.py`，结果 `11 passed`
- 已执行前端类型检查：`cd frontend && npx vue-tsc -b`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `285 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 41：前端侧边栏从 10 个菜单项重组为 5 个主菜单，并通过 3 个 Tab 容器页复用现有业务页面。

## 改动文件列表

- `frontend/src/App.vue`
- `frontend/src/router/index.ts`
- `frontend/src/views/BusinessManage.vue`
- `frontend/src/views/DataManage.vue`
- `frontend/src/views/MonitorManage.vue`
- `frontend/src/views/FlowManage.vue`
- `frontend/src/views/BatchExecute.vue`
- `frontend/src/views/ScheduleManage.vue`
- `frontend/src/views/TaskParamsManage.vue`
- `frontend/src/views/LogViewer.vue`
- `frontend/src/views/TaskMonitor.vue`
- `tests/单元测试/测试_前端管理页.py`
- `tests/单元测试/测试_任务参数管理页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/App.vue`
  - 侧边栏从 10 个入口精简为 5 个：
    - `/shops`
    - `/business`
    - `/data`
    - `/monitor`
    - `/settings`
- `frontend/src/router/index.ts`
  - 根路径 `/` 改为重定向 `/shops`
  - 新增 3 个容器页路由：`/business`、`/data`、`/monitor`
  - 保留 `/browser`、`/dashboard` 隐藏路由
  - 旧页面路径改为重定向到新容器页对应 Tab：
    - `/flows -> /business?tab=flow`
    - `/execute -> /business?tab=execute`
    - `/schedules -> /business?tab=schedule`
    - `/task-params -> /data?tab=params`
    - `/logs -> /monitor?tab=logs`
    - `/tasks -> /monitor?tab=monitor`
- `frontend/src/views/BusinessManage.vue`
  - 新建业务管理容器页，整合 `FlowManage`、`BatchExecute`、`ScheduleManage`
  - 通过 query 参数同步当前 Tab
- `frontend/src/views/DataManage.vue`
  - 新建数据管理容器页，整合 `TaskParamsManage`
  - `规则配置` 先用占位内容承接
- `frontend/src/views/MonitorManage.vue`
  - 新建运行监控容器页，整合 `LogViewer`、`TaskMonitor`
- `frontend/src/views/FlowManage.vue` / `frontend/src/views/BatchExecute.vue` / `frontend/src/views/ScheduleManage.vue` / `frontend/src/views/TaskParamsManage.vue` / `frontend/src/views/LogViewer.vue` / `frontend/src/views/TaskMonitor.vue`
  - 全部增加 `showTitle?: boolean`
  - 容器页嵌入时传 `false`，隐藏子页面自身标题区，避免双标题
- `tests/单元测试/测试_前端管理页.py`
  - 更新为校验 5 个主菜单、3 个容器页和旧路径重定向
- `tests/单元测试/测试_任务参数管理页.py`
  - 更新为校验 `/task-params` 已改为重定向 `/data?tab=params`

## 影响范围

- 侧边栏从 10 个入口收敛为 5 个主菜单，导航层级更浅
- 流程管理、批量执行、定时任务合并到“业务管理”
- CSV 导入 / 执行结果 / 流程参数入口合并到“数据管理”
- 日志与任务监控合并到“运行监控”
- 旧地址仍可访问，但会自动跳转到新容器页对应 Tab

## 注意事项

- 本轮未删除任何现有 Vue 文件，只通过容器页复用
- `规则配置` Tab 当前为占位内容，后续再承接真实功能
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_前端管理页.py tests/单元测试/测试_前端显示细节.py tests/单元测试/测试_任务参数管理页.py tests/单元测试/测试_流程参数管理页静态.py`，结果 `10 passed`
- 已执行前端类型检查：`cd frontend && npx vue-tsc -b`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `285 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 42：新增桌面自动化基础设施，包括桌面选择器配置、桌面基础页、微信桌面版选择器和微信页 POM。

## 改动文件列表

- `selectors/桌面选择器配置.py`
- `pages/桌面基础页.py`
- `selectors/微信选择器.py`
- `pages/微信页.py`
- `requirements.txt`
- `tests/test_桌面基础页.py`
- `tests/test_微信页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/桌面选择器配置.py`
  - 新增桌面应用选择器配置数据类
  - 以 UIAutomation 控件属性组合定位，支持主配置和备选配置链
- `pages/桌面基础页.py`
  - 新增桌面 POM 基类
  - 支持桌面控件查找、点击、输入文本、读取文本、存在性检查和窗口截图
  - 所有方法保持同步，以便后续 Task 层通过 `asyncio.to_thread()` 调用
  - 对 `uiautomation` 缺失场景做了测试友好的兜底处理
- `selectors/微信选择器.py`
  - 新增微信主窗口、搜索按钮、搜索输入框、聊天输入框、发送按钮和联系人项选择器
- `pages/微信页.py`
  - 新增微信桌面版 POM
  - 支持激活窗口、搜索联系人、向指定联系人发送消息、向当前聊天发送消息
  - 发送按钮失败时会回退使用 `Enter` 键发送
- `requirements.txt`
  - 新增 `uiautomation` 依赖
- `tests/test_桌面基础页.py`
  - 覆盖桌面选择器配置的备选链
  - 覆盖桌面基础页查找回退、逐字输入、点击与截图
- `tests/test_微信页.py`
  - 覆盖微信窗口激活失败、搜索联系人、发送消息回退 Enter 和窗口初始化参数

## 影响范围

- 项目现在具备桌面应用自动化的基础设施，可在后续任务中与浏览器自动化并行使用
- 微信桌面版 POM 已可作为未来售后通知、客服消息等能力的底座

## 注意事项

- 本轮未修改现有浏览器 `基础页.py`、`选择器配置.py`
- `uiautomation` 是同步库，本轮保持同步 API，后续 Task 层接入时需用 `asyncio.to_thread()`
- 微信选择器基于微信 PC 版 3.9.x 命名，版本升级后可能需要重新校准
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_桌面基础页.py tests/test_微信页.py`，结果 `9 passed`
- 已执行全量测试：首次全量回归命中过一条已知计时精度波动用例，单独复跑后再次执行全量 `python -m pytest -c tests/pytest.ini -q`，结果 `294 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 43：新增飞书服务，支持机器人 Webhook 通知、多维表格回写和 Webhook 连通性测试接口。

## 改动文件列表

- `backend/services/飞书服务.py`
- `backend/api/飞书接口.py`
- `backend/api/路由注册.py`
- `backend/services/系统服务.py`
- `backend/配置.py`
- `tests/test_飞书服务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/飞书服务.py`
  - 新建飞书服务类，封装：
    - 文本通知
    - 卡片通知
    - 售后结果通知
    - `tenant_access_token` 获取与缓存
    - 单条/批量多维表格写入
    - Webhook 连通性测试
  - 所有 HTTP 调用统一使用 `httpx.AsyncClient(timeout=10.0)`
  - 服务层失败不抛异常，统一返回 `{success: False, error: ...}`
- `backend/api/飞书接口.py`
  - 新增 `/api/feishu/test-webhook`
  - 返回统一响应，供前端测试 Webhook 连通性
- `backend/api/路由注册.py`
  - 将飞书接口加入统一路由注册
- `backend/services/系统服务.py`
  - 配置白名单新增：
    - `feishu_webhook_url`
    - `feishu_app_id`
    - `feishu_app_secret`
    - `feishu_bitable_app_token`
    - `feishu_bitable_table_id`
- `backend/配置.py`
  - 补充飞书配置字段，确保 `.env` 与运行时配置有一致入口
- `tests/test_飞书服务.py`
  - 覆盖文本通知请求体
  - 覆盖卡片通知 JSON 结构
  - 覆盖售后通知卡片组装
  - 覆盖 `tenant_access_token` 获取与缓存
  - 覆盖单条多维表格写入的路径和 headers
  - 覆盖 `测试webhook()` True/False
  - 覆盖飞书接口统一响应
  - 覆盖系统服务对白名单飞书字段的写入

## 影响范围

- 项目现在具备纯 HTTP 的飞书通知与多维表格回写基础能力
- 后续售后处理、人工审核和运营同步可直接复用飞书服务，而不需要新增 UI 自动化

## 注意事项

- 本轮未改动任何现有业务 Task 代码
- `httpx` 依赖仓库中已存在，因此 `requirements.txt` 无需新增
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_飞书服务.py`，结果 `9 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `303 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 43.1：在系统设置页新增飞书配置区块，补齐 5 个飞书字段和 Webhook 测试按钮。

## 改动文件列表

- `frontend/src/views/Settings.vue`
- `tests/单元测试/测试_系统设置机器码.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/Settings.vue`
  - `SystemConfig` 增加：
    - `feishu_webhook_url`
    - `feishu_app_id`
    - `feishu_app_secret`
    - `feishu_bitable_app_token`
    - `feishu_bitable_table_id`
  - `config` 默认值增加以上 5 个字段
  - `loadConfig()` 增加以上 5 个字段映射
  - 新增 `testingFeishu` 与 `testFeishuWebhook()`
  - 在“验证码服务”和“系统监控”之间新增“飞书配置”区块
  - 增加 5 个飞书输入框和 1 个“测试 Webhook”按钮
  - `App Secret` 使用 `type="password"`
- `tests/单元测试/测试_系统设置机器码.py`
  - 新增飞书配置区块静态断言
  - 覆盖字段默认值、配置映射、测试按钮和提示文案

## 影响范围

- 设置页现在可以直接配置飞书 Webhook、应用凭证和多维表格目标
- 前端可直接调用 `/api/feishu/test-webhook` 做连通性测试
- 保存逻辑仍然沿用现有统一配置保存，不会影响现有系统设置项

## 注意事项

- 本轮仅修改 `Settings.vue` 和对应静态测试
- 飞书 5 个字段全部是可选项，没有新增必填校验
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_系统设置机器码.py`，结果 `5 passed`
- 已执行前端类型检查：`cd frontend && npx vue-tsc -b`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `304 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地运行副产物，非本轮交付代码

---

## 任务摘要

完成 Task 44A：新增售后页选择器、售后页 POM 与单元测试，覆盖售后列表浏览、详情读取、退款操作、确认弹窗和翻页处理。

## 改动文件列表

- `selectors/售后页选择器.py`
- `pages/售后页.py`
- `tests/test_售后页.py`
- `.pipeline/progress.md`

## 改动说明

- `selectors/售后页选择器.py`
  - 新增售后页选择器类，集中定义售后列表、详情字段、操作按钮、确认弹窗、物流信息和翻页按钮选择器
  - 补充第 N 行详情链接和操作按钮的动态选择器生成方法，供 POM 层按行访问列表项
- `pages/售后页.py`
  - 新增 `售后页` POM，覆盖导航、Tab 切换、搜索、列表计数、第 N 行摘要读取、详情读取、退款/退货/拒绝按钮点击、确认弹窗处理、物流信息填写和翻页判断
  - 列表摘要和详情读取使用 `page.evaluate(...)` 提取 DOM 文本，避免在页面类中硬编码列索引
  - 点击和填写操作统一走 `基础页` 的安全方法，并在操作前后补充延迟与中文日志
- `tests/test_售后页.py`
  - 新增售后页单测，覆盖导航、搜索、第 N 行信息读取、同意退款点击、确认弹窗处理和翻页 `disabled` 分支
  - 通过 `AsyncMock` 模拟 Playwright 页面对象，验证选择器调用和关键分支行为

## 影响范围

- 项目现在具备独立的售后管理页 POM，可供后续 Task 层编排售后处理流程时直接复用
- 售后页相关选择器与页面操作已解耦，后续页面改版时可以优先只调整 `selectors/售后页选择器.py`
- 售后页的基础交互已有单元测试覆盖，可降低后续扩展退款流程时的回归风险

## 注意事项

- 本轮按任务单约束，仅新增 `selectors/售后页选择器.py`、`pages/售后页.py`、`tests/test_售后页.py` 三个业务文件，未改动现有页面与任务逻辑
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `310 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地变更或运行副产物，非本轮源码交付

---

## 任务摘要

完成 Task 44B：新增通用规则引擎、规则 REST API 和状态机驱动的售后处理任务，并接入现有数据库初始化与任务注册体系。

## 改动文件列表

- `backend/models/规则模型.py`
- `backend/services/规则服务.py`
- `backend/api/规则接口.py`
- `backend/api/路由注册.py`
- `backend/models/数据库.py`
- `tasks/售后任务.py`
- `tests/test_规则服务.py`
- `tests/test_售后任务.py`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/规则模型.py`
  - 新增 `rules` 表模型、字段映射、建表 SQL 和 `初始化规则表()` 方法
  - 统一承载平台、业务、店铺、优先级、条件组、动作列表和启用状态
- `backend/services/规则服务.py`
  - 新增规则 CRUD、启用切换、条件递归匹配和默认动作回退逻辑
  - 实现 `==`、`!=`、`>`、`<`、`>=`、`<=`、`in`、`not_in`、`contains` 等操作符
  - 新增默认售后规则种子，仅在空表时插入 5 条基础规则
- `backend/api/规则接口.py`
  - 新增 `/api/rules` 相关 REST 接口和 `/api/rules/match` 调试匹配接口
  - 接口统一返回 `{code, data, msg}` 结构
- `backend/api/路由注册.py`
  - 将规则接口路由加入现有 FastAPI 路由注册列表
- `backend/models/数据库.py`
  - 在现有数据库初始化链路中调用 `初始化规则表()`
  - 初始化完成后补充调用默认售后规则种子，保证新库启动即具备可用规则
- `tasks/售后任务.py`
  - 新增 `售后处理` 任务，并通过 `@register_task("售后处理", ...)` 注册
  - 用状态机串联售后页读取、规则匹配、页面操作、弹窗处理、微信通知、飞书通知和结果记录
  - 微信通知通过 `asyncio.to_thread()` 调用同步 `微信页`，飞书/微信通知异常仅记日志不打断主流程
- `tests/test_规则服务.py`
  - 覆盖规则操作符、条件递归、店铺精确匹配优先级、默认动作回退、CRUD、默认种子插入和规则接口基础调用
- `tests/test_售后任务.py`
  - 覆盖售后状态机正常流转、0 单直接完成、人工审核分支、微信通知分支、飞书通知分支、模板渲染和最大迭代保护

## 影响范围

- 后端现在具备可复用的通用规则引擎，后续推广、限时限量等业务也可以复用同一套条件-动作匹配逻辑
- 售后处理任务已可被流程编排系统直接引用，且具备页面操作、通知和人工审核分流能力
- 应用初始化时会自动确保 `rules` 表存在并预置基础售后规则，新环境可直接使用

## 注意事项

- 为满足“应用启动即建表并写入默认规则”的要求，本轮额外修改了 `backend/models/数据库.py` 和 `backend/api/路由注册.py` 两个集成文件
- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_规则服务.py tests/test_售后任务.py`，结果 `17 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `327 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`data/screenshots/`、`__pycache__/` 等本地变更或运行副产物，非本轮源码交付

---

## 任务摘要

完成 Task 45：将数据管理页的“规则配置”占位替换为完整规则 CRUD 页面，包含筛选、列表、编辑弹窗和测试匹配能力。

## 改动文件列表

- `frontend/src/views/RuleManage.vue`
- `frontend/src/views/DataManage.vue`
- `tests/单元测试/测试_前端管理页.py`
- `tests/单元测试/测试_规则配置页.py`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/RuleManage.vue`
  - 新建规则配置页组件，包含规则列表、平台/业务/店铺筛选、新建/编辑弹窗、条件编辑器、动作编辑器和测试匹配弹窗
  - 直接复用现有 `get/post/put/del` API 方法调用 `/api/rules` 与 `/api/shops`
  - 条件编辑器使用一层 `and/or` + 多条件行，字段输入采用 `<input list="..."> + <datalist>`，允许自定义字段名
  - 动作编辑器按类型联动动作选项，微信通知场景支持模板输入
  - 列表页支持启用/禁用开关、原生 `confirm()` 删除确认，以及空表提示
- `frontend/src/views/DataManage.vue`
  - 引入 `RuleManage`
  - 用 `<RuleManage v-else :show-title="false" />` 替换原先“规则配置功能开发中”的占位内容
- `tests/单元测试/测试_前端管理页.py`
  - 更新数据管理容器页静态断言，校验 `RuleManage` 已接入且规则 Tab 不再保留旧占位
- `tests/单元测试/测试_规则配置页.py`
  - 新增规则配置页静态测试，覆盖页面骨架、关键文案、条件/动作编辑器结构、规则 API 调用和 `DataManage` 引用关系

## 影响范围

- 数据管理页现在可以直接进行规则查询、创建、编辑、删除、启停和匹配调试，不再是占位页
- 前端已具备可视化规则配置入口，能够直接消费后端 `rules` 接口
- 规则配置页和数据管理页之间的集成已通过静态回归覆盖，后续改动更容易发现入口回归

## 注意事项

- 本轮未修改 `frontend/src/api/index.ts`，已确认现有 `get/post/put/del` 封装可直接复用
- 已执行前端静态回归：`python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_前端管理页.py tests/单元测试/测试_规则配置页.py`，结果 `5 passed`
- 已执行前端类型检查：`cd frontend && npx vue-tsc -b`
- 已执行全量测试：在 PowerShell 临时设置 `timeBeginPeriod(1)` 并提高当前进程优先级后运行 `python -m pytest -c tests/pytest.ini -q`，结果 `329 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地变更或运行副产物，非本轮源码交付

---

## 任务摘要

完成 Task 46A：新增售后工作队列表和售后抓取层能力，补齐详情页 JS 全量抓取、列表翻页扫描、详情标签页管理与配套单元测试。

## 改动文件列表

- `backend/models/售后队列模型.py`
- `backend/services/售后队列服务.py`
- `backend/models/数据库.py`
- `selectors/售后页选择器.py`
- `pages/售后页.py`
- `tests/test_售后队列服务.py`
- `tests/test_售后页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/售后队列模型.py`
  - 新建 `aftersale_queue` 表结构和初始化方法
  - 增加 `batch_id + 订单号` 唯一索引，保证同批次列表扫描写入不重复
- `backend/services/售后队列服务.py`
  - 新增售后队列 CRUD + 批次管理服务
  - 支持批次生成、单条/批量写入、详情 JSON 回填、阶段更新、到期记录查询、拒绝次数统计和批次汇总
- `backend/models/数据库.py`
  - 将售后队列表加入统一建表清单，并在初始化数据库时显式初始化
- `selectors/售后页选择器.py`
  - 新增 `待商家处理Tab` 和详情页区域选择器
- `pages/售后页.py`
  - `切换待处理()` 改为优先使用“待商家处理”Tab
  - 新增 `扫描所有待处理()`、`点击详情并切换标签()`、`关闭详情标签()`
  - 新增 `抓取详情页完整信息()`，用单次 `evaluate(...)` 动态提取按钮、物流、协商和申请字段
  - 新增 `点击指定按钮()`、`读取当前所有按钮()`、`检查订单是否待处理()`、`详情页截图()`
- `tests/test_售后队列服务.py`
  - 覆盖批次格式、队列写入、批量去重、详情更新、阶段更新、到期记录、拒绝次数和批次统计
- `tests/test_售后页.py`
  - 覆盖翻页扫描、详情标签切换、JS 抓取、动态按钮、待处理判断和详情截图
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录 Task 46A 的实现范围与验证结果

## 影响范围

- 后端现在具备独立的售后工作队列，可把列表摘要和详情页完整信息分阶段落库
- 售后页 POM 已支持跨页扫描和详情标签页操作，后续 `tasks/售后任务.py` 可以直接复用这些抓取能力
- 详情页信息提取改为单次 JS 评估，后续拼多多页面改版时主要只需调整 JS 标签匹配逻辑

## 注意事项

- 本轮按任务约束未改动 `tasks/售后任务.py` 和 `backend/api/`，队列消费和 API 暴露留待后续任务
- 已执行针对性回归：`python -m pytest -q tests/test_售后队列服务.py tests/test_售后页.py`，结果 `24 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `347 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地变更或运行副产物，非本轮源码交付

---

## 任务摘要

完成 Task 46B：校准售后页选择器，新增售后决策引擎与弹窗扫描能力，并将售后任务重写为队列驱动的详情决策链路。

## 改动文件列表

- `selectors/售后页选择器.py`
- `pages/售后页.py`
- `backend/services/售后决策引擎.py`
- `tasks/售后任务.py`
- `tests/test_售后决策引擎.py`
- `tests/test_售后页.py`
- `tests/test_售后任务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/售后页选择器.py`
  - 校准售后页真实 URL
  - 新增待商家处理卡片与选中类名片段
  - 将主行结构切换为 `order_item`
  - 新增按订单号定位详情链接和操作按钮的方法
- `pages/售后页.py`
  - 新增待商家处理选中检查、按订单号打开详情标签、实时按钮检测、弹窗扫描和 JS 弹窗处理
  - 校准详情页字段提取标签，补齐 `售后编码`、`订单编号`、`联系地址`、`协商最新`、`售后状态描述` 等字段
  - 保留列表扫描、按钮点击、详情截图等队列处理所需基础能力
- `backend/services/售后决策引擎.py`
  - 新建统一决策层，输出 `{操作, 目标按钮, 备选按钮, 弹窗偏好, 备注, 飞书通知}` 结构
  - 支持退货退款、仅退款小额自动处理、售后图片人工、物流拒收、规则拒绝和拒绝次数上限场景
- `tasks/售后任务.py`
  - 移除旧状态机逻辑，改成“扫描入队 -> 实时详情 -> 决策 -> 执行 -> 回写队列”
  - 人工、失败和拒绝场景统一回写 `aftersale_queue.当前阶段`
  - 拒绝场景写入 `下次处理时间=now+30min`
- `tests/test_售后决策引擎.py`
  - 覆盖 10 个决策分支，包括退货退款、仅退款、人工处理、拒绝和优先级按钮匹配
- `tests/test_售后页.py`
  - 覆盖待商家处理选中、详情标签切换、详情抓取、实时按钮判断、弹窗扫描和 JS 弹窗按钮点击
- `tests/test_售后任务.py`
  - 覆盖完整流程、详情无按钮跳过、弹窗人工、拒绝回写、备选按钮和搜不到订单跳过

## 影响范围

- 售后页现在可以基于订单号稳定打开详情，并在详情页实时判断是否还需要处理
- 售后任务不再依赖旧状态机，而是直接复用 `售后队列服务` 和 `售后决策引擎`
- 售后自动处理已具备基础弹窗自处理能力，为 46C 的定时补扫和后续规则扩展提供基础

## 注意事项

- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后决策引擎.py tests/test_售后页.py tests/test_售后任务.py`，结果 `30 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `355 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地变更或运行副产物，非本轮源码交付

---

## 任务摘要

完成 Hotfix 46A-fix：重写售后列表页抓取 JS，按真实 DOM 精准清洗列表字段。

## 改动文件列表

- `selectors/售后页选择器.py`
- `pages/售后页.py`
- `tests/test_售后页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/售后页选择器.py`
  - 将 `售后单行` 主选择器切换为 `div[class*="after-sales-table_order_item"]`
  - 仅保留任务要求的 XPath 备选，避免旧的宽泛行匹配继续混入脏数据
- `pages/售后页.py`
  - 将 `获取售后单数量()` 改为单次 JS 读取真实列表行数量
  - 将 `获取第N行信息()` 改为按真实 DOM class 精准提取头部、金额列、状态列和操作列字段
  - `扫描所有待处理()` 仅保留清洗后且包含订单号的记录，避免空字典写入后续队列
- `tests/test_售后页.py`
  - 新增列表数量读取测试
  - 新增完整字段提取测试
  - 新增扫描过滤空记录测试

## 影响范围

- 售后列表摘要写入 SQLite 前的数据更干净，每个字段只对应一个值
- 后续 `售后任务` 的扫描入队阶段会直接消费新的清洗结果，减少列表页 HTML 拼接文本污染详情决策
- 46B 的详情页决策与弹窗链路未改动

## 注意事项

- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py tests/test_售后决策引擎.py`，结果 `33 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `358 passed, 16 warnings`
- 16 条 warning 仍为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db`、`__pycache__/` 等本地变更或运行副产物，非本轮源码交付

---

## 任务摘要

完成 Task 46B 二次重构：新增退货物流抓取与决策、列表页分流转人工、列表/详情备注操作，并补齐 SQLite 新字段兼容。

## 改动文件列表

- `selectors/售后页选择器.py`
- `pages/售后页.py`
- `backend/models/售后队列模型.py`
- `backend/services/售后队列服务.py`
- `backend/services/售后决策引擎.py`
- `tasks/售后任务.py`
- `tests/test_售后决策引擎.py`
- `tests/test_售后页.py`
- `tests/test_售后任务.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `selectors/售后页选择器.py`
  - 新增列表页备注、详情页备注、退货物流 Tab 与“查看全部”按钮选择器
  - 新增按订单号定位列表页“添加备注”入口的方法
- `pages/售后页.py`
  - 新增列表页备注、详情页备注和退货物流抓取方法
  - 增加详情页专用点击/填写辅助方法，避免继续把 `页面=目标页面` 传给基类安全操作接口
- `backend/models/售后队列模型.py`
  - 为 `aftersale_queue` 增加 `shop_name` 和 4 个退货物流字段
  - 初始化时补充旧表字段探测与 `ALTER TABLE ADD COLUMN` 迁移
- `backend/services/售后队列服务.py`
  - 适配新字段入队和详情回写
  - 新增 `更新退货物流(...)` 用于详情补抓后单独回写物流摘要字段
- `backend/services/售后决策引擎.py`
  - 重写退货退款逻辑，支持物流阶段等待、白名单派件人匹配、入库校验优先级和自动退款金额上限
  - 保留仅退款逻辑并补齐备注、人工原因和通知内容
- `tasks/售后任务.py`
  - 扫描入队后新增“补寄/维修/换货”列表页直接转人工
  - `_处理单条()` 去掉搜索步骤，直接按订单号点详情
  - 退货退款详情页新增退货物流抓取、等待退回/等待验货分支和统一转人工流程
- `tests/test_售后决策引擎.py`
  - 扩展到 30+ 决策场景，覆盖退货物流阶段、白名单和仅退款回归
- `tests/test_售后页.py`
  - 增加列表页备注、详情页备注和退货物流抓取测试
- `tests/test_售后任务.py`
  - 增加列表分流、去掉搜索、退货物流等待、自动退款、等待验货和备选按钮测试
- `PLAN.md` / `改造进度.md` / `.pipeline/progress.md`
  - 同步记录本轮实现范围与验证结果

## 影响范围

- 售后任务现在可以在列表页提前把补寄/维修/换货分流到人工处理，减少无效进详情页操作
- 退货退款场景现在会抓取退货物流并据此决定等待、自动退款、等待验货或转人工
- `aftersale_queue` 具备店铺名和退货物流字段，后续查询与人工跟进信息更完整
- 列表页备注和详情页备注已经拆开，后续页面结构继续变化时可以分别校准

## 注意事项

- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后决策引擎.py tests/test_售后页.py tests/test_售后任务.py`，结果 `61 passed`
- 已执行邻近回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后队列服务.py`，结果 `10 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini tests/ -v`，结果 `386 passed, 16 warnings`
- 首次全量回归命中过一条既有 `tests/单元测试/测试_反检测.py::test_随机延迟在范围内` 计时波动，用例单独复跑通过后再次执行全量已全部通过
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 及 `data/profiles/`、`data/screenshots/` 下的本地变更，非本轮源码交付

---

## 任务摘要

完成售后退货退款流程重构：新增店铺级售后配置表与配置服务，修复售后按钮抓取和队列去重逻辑，并将售后任务改为按页扫描、按按钮决策的执行链路。

## 改动文件列表

- `backend/models/数据库.py`
- `backend/services/售后配置服务.py`
- `backend/services/售后决策引擎.py`
- `backend/services/售后队列服务.py`
- `pages/售后页.py`
- `tasks/售后任务.py`
- `tests/test_售后配置服务.py`
- `tests/test_售后队列服务.py`
- `tests/test_售后决策引擎.py`
- `tests/test_售后任务.py`
- `tests/test_售后页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/数据库.py`
  - 新增 `aftersale_config` 表
  - 新增售后队列索引 `idx_aftersale_queue_shop_order`
  - 在初始化数据库时补齐售后配置旧表字段，兼容已有库
- `backend/services/售后配置服务.py`
  - 新增店铺售后配置读取/更新服务
  - 未配置时返回默认退货白名单、等待时间、自动退款上限、不支持自动处理类型和备注模板
- `backend/services/售后队列服务.py`
  - 批量写入前新增“同店铺同订单活跃记录”查询
  - 当订单已处于 `待处理 / 处理中 / 等待退回 / 等待验货 / 待退款` 之一时跳过重复导入
- `pages/售后页.py`
  - 将按钮读取、按钮点击、详情页按钮抓取统一切换到新版 `data-testid` 选择器
  - 显式补抓“其他操作”区域里的 `<a>` 按钮，避免漏掉底部链接操作
- `backend/services/售后决策引擎.py`
  - 决策入口改为按可用按钮分流
  - 新增“同意拒收退款”人工拦截通知路径
  - “同意退货”直接输出自动点击结果
  - “同意退款”按退货物流状态、白名单、入库校验和金额上限决定等待、验货或自动退款
- `tasks/售后任务.py`
  - 去掉规则服务依赖，改用 `售后配置服务`
  - 执行流程由“全量扫描后处理”改为“扫一页处理一页”
  - 列表页人工分流改为读取店铺售后配置中的 `不支持自动处理类型`
- `tests/test_售后配置服务.py`
  - 新增售后配置表创建、默认读取、插入更新和部分更新测试
- `tests/test_售后队列服务.py`
  - 新增售后队列索引断言和跨批次活跃记录去重测试
- `tests/test_售后决策引擎.py`
  - 改为覆盖“同意拒收退款 / 同意退货 / 同意退款”三类按钮路径
- `tests/test_售后任务.py`
  - 新增逐页处理、配置驱动列表分流、人工拦截、等待与自动退款场景
- `tests/test_售后页.py`
  - 新增新版 `data-testid` 按钮选择器参数断言

## 影响范围

- 售后任务现在具备独立的店铺级配置来源，不再依赖规则服务拼装售后参数
- 同一店铺同一订单的活跃售后单不会被重复导入工作队列
- 详情页可正确识别 `a[data-testid=...]` 链接按钮，底部“其他操作”区域的操作不再漏抓
- 售后执行链路改为当前页扫描后立即处理，减少跨页累积带来的队列偏差

## 注意事项

- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后配置服务.py tests/test_售后队列服务.py tests/test_售后决策引擎.py tests/test_售后任务.py tests/test_售后页.py`，结果 `66 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `381 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 和运行产生的 `__pycache__/` 本地变更，非本轮核心源码交付

---

## 任务摘要

完成售后配置系统重构：新增完整售后配置模型、配置服务和 REST API，接入独立前端配置页，并将售后任务和决策引擎切换到新配置体系。

## 改动文件列表

- `backend/models/售后配置模型.py`
- `backend/models/数据库.py`
- `backend/services/售后配置服务.py`
- `backend/api/售后配置接口.py`
- `backend/api/路由注册.py`
- `backend/services/售后决策引擎.py`
- `backend/services/规则服务.py`
- `tasks/售后任务.py`
- `frontend/src/api/aftersaleConfig.ts`
- `frontend/src/views/AftersaleConfig.vue`
- `frontend/src/router/index.ts`
- `frontend/src/App.vue`
- `frontend/src/views/DataManage.vue`
- `tests/test_售后配置服务.py`
- `tests/test_售后配置接口.py`
- `tests/test_售后决策引擎.py`
- `tests/test_售后任务.py`
- `tests/test_规则服务.py`
- `tests/单元测试/测试_前端管理页.py`
- `tests/单元测试/测试_规则配置页.py`
- `tests/单元测试/测试_售后配置页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/售后配置模型.py`
  - 新建 `aftersale_config` 表定义
  - 覆盖全局开关、退货退款、仅退款、通知、弹窗备注、执行策略和飞书多维表字段
  - 增加旧字段补齐逻辑
- `backend/models/数据库.py`
  - 接入售后配置模型初始化
  - 在数据库启动时增加“从旧售后规则迁移到新配置”的调用
- `backend/services/售后配置服务.py`
  - 重写为完整配置服务
  - 提供默认配置、自动初始化、部分更新、列表、删除、白名单校验和规则迁移能力
- `backend/api/售后配置接口.py`
  - 新增售后配置 CRUD 接口
- `backend/api/路由注册.py`
  - 注册售后配置路由
- `backend/services/售后决策引擎.py`
  - 使用新配置字段 `仅退款_*`、`拒收退款_*`、`备注模板`
  - 恢复仅退款配置驱动决策分支
- `backend/services/规则服务.py`
  - 清空默认售后规则
  - `初始化默认售后规则()` 保留签名但不再插入规则
- `tasks/售后任务.py`
  - 使用 `self._配置服务` 读取配置
  - 接入 `启用自动售后`、`每批最大处理数` 和店铺级飞书 webhook
- `frontend/src/api/aftersaleConfig.ts`
  - 新增售后配置前端 API 封装
- `frontend/src/views/AftersaleConfig.vue`
  - 新建售后配置页面
  - 支持店铺切换、白名单编辑、标签输入、通知配置、执行策略、弹窗备注和飞书多维表配置
  - 保存时只发送改动字段
- `frontend/src/router/index.ts` / `frontend/src/App.vue`
  - 新增 `/aftersale-config` 路由与侧边栏导航
- `frontend/src/views/DataManage.vue`
  - 移除旧“规则配置”入口
- `tests/test_售后配置服务.py`
  - 覆盖默认配置、部分更新、白名单校验、删除和规则迁移
- `tests/test_售后配置接口.py`
  - 覆盖售后配置接口的获取、更新、列表和删除
- `tests/test_售后决策引擎.py` / `tests/test_售后任务.py` / `tests/test_规则服务.py`
  - 对齐新配置字段和规则服务 no-op 行为
- `tests/单元测试/测试_前端管理页.py` / `tests/单元测试/测试_规则配置页.py` / `tests/单元测试/测试_售后配置页.py`
  - 校验新路由、新侧边栏入口，以及 DataManage 不再展示旧规则配置选项卡

## 影响范围

- 售后配置已从旧规则服务彻底拆分为店铺级独立配置体系
- 售后任务运行时会直接读取店铺售后配置，不再依赖规则引擎拼装参数
- 前端新增独立“售后配置”页面，可直接编辑白名单、通知、执行策略和多维表配置
- 数据管理页面不再暴露旧“规则配置”入口，旧 `RuleManage.vue` 仅保留文件本身

## 注意事项

- 已执行针对性回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后配置服务.py tests/test_售后配置接口.py tests/test_售后决策引擎.py tests/test_售后任务.py tests/test_规则服务.py tests/单元测试/测试_前端管理页.py tests/单元测试/测试_规则配置页.py tests/单元测试/测试_售后配置页.py`，结果 `56 passed`
- 已执行类型检查：`cd frontend && npx vue-tsc -b`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `390 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 和运行产生的 `__pycache__/` 本地变更，非本轮核心源码交付

---

## 任务摘要

修复 `tasks/执行任务.py` 多步流程首步完成后不续投递下一步的问题，并补齐 `continue` / 取消场景回归测试。

## 改动文件列表

- `tasks/执行任务.py`
- `tests/单元测试/测试_执行任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `tasks/执行任务.py`
  - 增加 `同步读取批次状态`、`获取队列名称` 导入
  - 在 `执行任务()` 内提取 `_投递下一步()`，统一完成批次状态读取、取消判断、队列选择和 Celery 签名投递
  - 在当前步骤执行成功且仍有后续步骤时自动投递 `step_index + 1`
  - 在 `on_fail in {"continue", "log_and_skip"}` 分支复用同一 helper 继续投递下一步
  - 续投递时继承 `flow_param_id` / `flow_param_ids`，并在批次已停止或已有取消标记时直接跳过
- `tests/单元测试/测试_执行任务.py`
  - 扩展 `continue` 分支用例，覆盖失败后继续执行时的下一步投递
  - 扩展 `flow_param_ids` 用例，覆盖成功路径续投递和参数继承
  - 新增批次已停止时不投递下一步的异常路径用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮多步流程续投递修复与验证结果

## 影响范围

- 多步骤批次流程在首步成功或 `continue/log_and_skip` 后，后续步骤会被实际投递到目标 Worker 队列
- 批次被手动停止或已有取消标记时，不会再继续派发后续步骤
- 流程参数批次执行时，下一步会继续沿用当前步骤关联的 `flow_param_id` / `flow_param_ids`

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_执行任务.py`，结果 `8 passed`
- 直接执行 `python -m pytest -c tests/pytest.ini -q` 会命中既有抖动用例 `tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`
- 已通过 PowerShell 临时启用 `timeBeginPeriod(1)` 并以高优先级独立 Python 进程执行同一全量命令，结果 `391 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 与 `data/` 下若干本地运行副产物，非本轮源码改动

---

## 任务摘要

将售后列表扫描改为 API 拦截优先，并在拦截失败时回退到原有 DOM 逐行扫描路径。

## 改动文件列表

- `pages/售后页.py`
- `tasks/售后任务.py`
- `tests/test_售后页.py`
- `tests/test_售后任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - 新增 `拦截售后列表API()`，通过 `page.on("response")` 监听售后列表接口响应并直接提取 `result.list/pageItems`
  - 新增 `导航并拦截售后列表()`，在列表页导航后优先拿当前页 API 数据，首次为空时重试触发待商家处理请求
  - 新增 `_检查有下一页()`，从原 `翻页()` 中拆出分页可用性判断
  - 新增 `翻页并拦截()`，翻页前注册接口拦截，翻页后直接返回下一页 API 数据
  - 保留原 `获取售后单数量()` / `获取第N行信息()` / `翻页()`，作为 API 失败时的 DOM fallback
- `tasks/售后任务.py`
  - 新增 `_处理扫描结果页()`，统一处理当前页摘要写队列、人工分流、详情处理和异常回写
  - 新增 `_收集当前页DOM摘要()` 与 `_执行DOM扫描回退()`，用于 API 拦截失败时回退到旧路径
  - `执行()` 的扫描阶段改为先调用 `导航并拦截售后列表()`，后续使用 `翻页并拦截()` 推进分页
  - 当当前页未拦截到数据时增加 `[扫描] 当前页未拦截到数据，尝试 JS fallback` 日志，并切回 DOM 逐行扫描
- `tests/test_售后页.py`
  - 新增 API 拦截抓取与清洗用例
  - 新增导航后首次拦截为空时重试用例
  - 新增翻页拦截的正常与无下一页分支用例
- `tests/test_售后任务.py`
  - 新增 API 拦截多页时不走 DOM 逐行扫描的用例
  - 新增 API 拦截为空时回退到 DOM 扫描的用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮售后列表 API 拦截改造与验证结果

## 影响范围

- 售后任务扫描列表时优先读取接口返回的结构化数据，不再依赖逐行读取 DOM 文本
- 当拼多多列表接口变更或拦截失败时，任务会自动回退到旧的 DOM 扫描链路
- API 路径下日志应以 `[售后页] API拦截抓取到 N 条售后单` 为主，只有 fallback 时才会出现逐行 `第X行` 日志

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py tests/单元测试/测试_执行任务.py`，结果 `43 passed`
- 直接执行 `python -m pytest -c tests/pytest.ini -q` 仍会命中既有抖动用例 `tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`
- 已通过 PowerShell 临时启用 `timeBeginPeriod(1)` 并以高优先级独立 Python 进程执行同一全量命令，结果 `397 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

修正售后列表 API 拦截的触发时机，避免导航默认请求被误捕获，并补上待商家处理已选中时的强制点击重试。

## 改动文件列表

- `pages/售后页.py`
- `tests/test_售后页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - 调整 `导航并拦截售后列表()`：先执行 `导航到售后列表()`，再注册 `拦截售后列表API()`，避免把页面初始加载请求当成待商家处理切换请求
  - 将首轮拦截超时改为 `10` 秒，与重试路径保持一致
  - 为 `确保待商家处理已选中()` 增加 `强制点击` 参数
  - 当卡片已选中但传入 `强制点击=True` 时，仍会再次点击卡片并等待加载，显式触发新的列表请求
  - `导航并拦截售后列表()` 在首轮为空时改为复用 `强制点击=True` 重试，并输出 `API拦截失败，fallback到JS抓取` 日志
- `tests/test_售后页.py`
  - 新增“已选中但强制点击时再次点击”的用例
  - 更新 `导航并拦截售后列表()` 用例，断言导航后再走两次 `强制点击=True` 的待商家处理切换
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 API 拦截触发时机修正与验证结果

## 影响范围

- 售后列表 API 拦截会优先等待待商家处理切换触发的新请求，不再误吃列表页初始加载返回
- 当待商家处理卡片本身已处于选中态时，重试路径仍能主动再次点击，提升拦截命中率
- 任务层 fallback 逻辑保持不变，接口仍未命中时会回退到原有 JS/DOM 扫描

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `36 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `398 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

为售后列表 API 拦截与任务扫描补上去重保护，只保留最后一次有效响应并在页内按订单号去重。

## 改动文件列表

- `pages/售后页.py`
- `tasks/售后任务.py`
- `tests/test_售后页.py`
- `tests/test_售后任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - 调整 `拦截售后列表API()`，每次收到新的有效响应时先 `clear()` 旧结果，只保留最后一次有效接口返回
  - 在单次响应处理内增加 `已捕获订单号集合`，按订单号去重，避免同一响应中的重复订单被保留多次
- `tasks/售后任务.py`
  - 在 `_处理扫描结果页()` 内增加 `当前页记录映射`，写队列前按订单号再做一次页内去重
  - 当同一页出现重复订单号时，保留最后一条记录内容，避免同页重复处理
- `tests/test_售后页.py`
  - 新增“只保留最后一次有效响应并按订单号去重”的用例
- `tests/test_售后任务.py`
  - 新增“API 当前页重复订单写队列前会去重”的用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮售后列表去重补丁与验证结果

## 影响范围

- 售后页 API 拦截结果不会再累加多个响应，只保留最新一次有效列表数据
- 即便拼多多接口或页面链路返回重复订单，同一页也只会向队列写入一次该订单
- 页内重复订单若内容不一致，会以最后一条摘要为准进入后续处理链路

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `38 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini -q`，结果 `400 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

将 `售后任务` 重构为仅做列表扫描和写入队列的最小闭环，并把队列写入去重收口为按订单号全表唯一。

## 改动文件列表

- `tasks/售后任务.py`
- `backend/services/售后队列服务.py`
- `tests/test_售后任务.py`
- `tests/test_售后队列服务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `tasks/售后任务.py`
  - 移除详情页处理、售后决策引擎、飞书通知、售后配置服务、`_执行结果`、`_售后配置缓存`
  - 新增 `_判断售后类型()`，统一归类为 `退货退款 / 退款 / 补寄 / 换货 / 维修`
  - 更新 `_构建队列记录()`，补充 `售后类型_原始` 和 `需要人工`
  - `执行()` 简化为 `导航并拦截售后列表()` -> `API/DOM 抓取` -> `批量写入队列()` -> `翻页并拦截()`
  - 文件末尾新增后续恢复路线图注释
- `backend/services/售后队列服务.py`
  - 新增按 `订单号` 查询已存在记录的逻辑
  - `写入队列()` 和 `批量写入队列()` 统一改为“订单已存在则跳过”，不再区分批次
- `tests/test_售后任务.py`
  - 重写回归用例，覆盖类型标准化、多页扫描、DOM fallback、空页结束、页内去重和异常路径
- `tests/test_售后队列服务.py`
  - 新增单条写入重复订单跳过用例
  - 调整跨批次去重和拒绝次数测试，使其符合“订单号全表唯一”的新约束
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮最小闭环重构和验证结果

## 影响范围

- `售后任务` 当前只负责扫描待商家处理列表并写入 SQLite 队列，不再涉及详情页、决策、按钮点击、弹窗或飞书
- 队列表中同一 `订单号` 只保留一条记录，重复运行和跨批次补扫都不会重复插入
- 补寄、换货、维修会在任务侧被标准化并标记 `需要人工=True`，为后续恢复处理链路保留信号

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后任务.py tests/test_售后队列服务.py`，结果 `26 passed`
- 已执行补充回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py tests/test_售后队列服务.py`，结果 `54 passed`
- 已执行全量测试：`python -m pytest -c tests/pytest.ini tests/ -v`，结果 `405 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

修复售后页“待商家处理”API 拦截误捕获默认列表的问题，并切换到 Beast Core 分页选择器与禁用态判断。

## 改动文件列表

- `pages/售后页.py`
- `selectors/售后页选择器.py`
- `tests/test_售后页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - `导航并拦截售后列表()` 在导航后增加一次额外的页面稳定等待，再注册拦截器并点击“待商家处理”
  - `拦截售后列表API()` 新增 `仅待商家处理` 参数
  - 当启用该参数时，优先按响应 URL 的筛选参数判断是否为待商家处理请求；缺少参数时再按列表项状态文本兜底判断
  - 非待商家处理响应会被忽略，避免误吃导航阶段默认“全部”列表数据
  - `翻页并拦截()` 同样开启待商家处理过滤
  - `_检查有下一页()` 增加 `PGT_disabled` 识别，兼容 Beast Core 分页禁用态
- `selectors/售后页选择器.py`
  - `下一页按钮` 主选择器改为 `//li[@data-testid="beast-core-pagination-next"]`
  - 增加 `PGT_next` 备选选择器，并保留旧版 `ant-pagination-next` 兜底
- `tests/test_售后页.py`
  - 新增忽略默认列表响应用例
  - 新增 Beast Core 分页禁用态识别用例
  - 新增下一页选择器静态断言
  - 更新导航并拦截与翻页拦截用例，断言新的等待和参数行为
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮售后页 POM/选择器修复与验证结果

## 影响范围

- 售后列表首次导航后，API 拦截更聚焦于“待商家处理”列表，不再容易混入默认“全部”数据
- 翻页按钮定位适配到 Beast Core 新版分页结构，最后一页禁用态也能被正确识别
- `售后任务.py` 和 `售后队列服务.py` 未改动，本轮影响范围限定在 POM 层、选择器层和相关测试

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py`，结果 `31 passed`
- 已执行补充回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `45 passed`
- 首次直接执行全量 `python -m pytest -c tests/pytest.ini tests/ -v` 命中既有抖动用例 `tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`
- 已通过 PowerShell 临时设置 `timeBeginPeriod(1)` 并提升当前进程优先级后再次执行全量测试，结果 `408 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

收紧 `售后页` 的 API 拦截时序与响应竞态处理，确保导航默认请求收尾后再监听并触发“待商家处理”请求。

## 改动文件列表

- `pages/售后页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - `导航并拦截售后列表()` 在导航和页面加载延迟之后新增 `等待默认请求完成` 日志
  - 增加 `await asyncio.sleep(2)`，让导航阶段默认列表请求先结束，再注册 `response` 监听器
  - 首次与重试链路都保持“先创建拦截任务，再点击待商家处理”的顺序
  - `拦截售后列表API()` 内新增局部 `asyncio.Lock()`，把结果写入串行化
  - 每个响应先独立构建 `本次结果列表`，仅在非空时才覆盖 `结果容器` 并触发 `捕获事件.set()`
  - `翻页并拦截()` 在翻页成功后增加 `0.5` 秒缓冲，提升下一页请求被监听到的稳定性
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮仅修改 `pages/售后页.py` 的时序修复与验证结果

## 影响范围

- 售后列表导航后更不容易误捕获默认“全部”列表响应
- 同一次拦截调用内，多条响应并发到达时对结果容器的覆盖更稳定
- 翻页后拿到下一页 API 数据的命中率更高，减少 DOM fallback 频率

## 注意事项

- 本轮源码改动仅落在 `pages/售后页.py`
- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `45 passed`
- 已执行全量测试：PowerShell 临时设置 `timeBeginPeriod(1)` 并提升当前进程优先级后执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果 `408 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

将 `售后页` 的列表拦截改为“两阶段拦截”：先消耗导航默认请求，再注册真正的拦截器去抓“待商家处理”与翻页请求。

## 改动文件列表

- `pages/售后页.py`
- `tests/test_售后页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - `导航并拦截售后列表()` 改为先同步执行一次 `拦截售后列表API(超时秒=8)`，把导航触发的默认列表响应消耗掉
  - 新增 `默认请求已消耗，开始真正的拦截` 日志
  - 去掉该方法内额外的 `页面加载延迟()` 和 `asyncio.sleep(2)` 硬等待
  - 首次和重试路径都改为 `create_task(self.拦截售后列表API(超时秒=15)) -> await asyncio.sleep(0.1) -> await self.确保待商家处理已选中(强制点击=True)`
  - `翻页并拦截()` 同步改为 `create_task(拦截) -> sleep(0.1) -> 翻页` 的顺序
  - 保留 `拦截售后列表API()` 现有结果串行化逻辑，继续避免并发响应竞态
- `tests/test_售后页.py`
  - 更新导航并拦截测试，断言先消耗默认请求，再执行两次正式拦截
  - 更新翻页并拦截测试，断言新的超时参数和无筛选调用方式
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮两阶段拦截改造与验证结果

## 影响范围

- 导航后的默认“全部”列表响应会先被单独消耗，不再与后续“待商家处理”请求共用同一个拦截生命周期
- “待商家处理”首次请求与翻页请求的监听时机更明确，减少误抓和漏抓
- `售后任务.py`、选择器层和队列服务未改动

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `45 passed`
- 已执行单条抖动验证：通过 Python 进程内设置 `timeBeginPeriod(1)` 和高优先级后，`tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内` 通过
- 已执行全量测试：`python -X utf8 -c "import ctypes, sys, pytest; ctypes.windll.winmm.timeBeginPeriod(1); ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080); sys.exit(pytest.main(['-c','tests/pytest.ini','tests/','-v']))"`，结果 `408 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

将 `售后页` 的列表导航拦截切换为 `networkidle` 等待所有默认请求收尾后再注册真正的 API 拦截器。

## 改动文件列表

- `pages/售后页.py`
- `tests/test_售后页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - `导航并拦截售后列表()` 改为导航完成后执行 `await self.页面.wait_for_load_state("networkidle", timeout=10000)`
  - 增加 `等待所有默认请求完成（networkidle）`、`networkidle 超时，继续执行`、`网络已空闲，开始拦截` 日志
  - 删除旧的默认请求“消耗”拦截步骤
  - 首次与重试路径统一为 `create_task(self.拦截售后列表API(超时秒=15)) -> await asyncio.sleep(0.1) -> await self.确保待商家处理已选中(强制点击=True)`
  - `翻页并拦截()` 保持 `create_task(拦截) -> sleep(0.1) -> 翻页` 的顺序不变
- `tests/test_售后页.py`
  - 更新导航并拦截测试，断言 `wait_for_load_state("networkidle", timeout=10000)` 会被调用
  - 新增 `networkidle` 超时后仍继续执行并重试的异常路径用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 `networkidle` 导航时序改造与验证结果

## 影响范围

- 导航阶段触发的投诉预警、主列表、统计等多个默认请求会先收尾，再开始真正监听“待商家处理”请求
- 不再依赖“消耗一次默认响应”的数量假设，适应多个 `/afterSales` 相关请求并发的页面
- `售后任务.py`、选择器层和 `backend/` 未改动

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `46 passed`
- 已执行全量测试：`python -X utf8 -c "import ctypes, sys, pytest; ctypes.windll.winmm.timeBeginPeriod(1); ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080); sys.exit(pytest.main(['-c','tests/pytest.ini','tests/','-v']))"`，结果 `409 passed, 16 warnings`
- 全量测试首次复跑仍可能命中既有抖动用例 `tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`，继续复跑后已通过
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

将售后列表扫描彻底切回 DOM 批量抓取，并移除售后任务中的 API/DOM 双路径与 fallback 逻辑。

## 改动文件列表

- `pages/售后页.py`
- `tasks/售后任务.py`
- `tests/test_售后页.py`
- `tests/test_售后任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - 新增 `批量抓取当前页()`，通过一次 `page.evaluate` 批量提取当前页所有售后单行
  - `导航并拦截售后列表()` 改为导航后点击“待商家处理”，直接调用 `批量抓取当前页()`
  - `翻页并拦截()` 改为翻页成功后直接调用 `批量抓取当前页()`
  - 保留现有 API 拦截相关 helper，但列表扫描主链路已不再调用
- `tasks/售后任务.py`
  - 删除 `_收集当前页DOM摘要()` 旧 helper
  - `执行()` 改为纯 DOM 分页扫描，不再区分 API/DOM 来源，也不再写 DOM fallback 日志
  - 第一页为空时直接返回 `无待处理售后单`；后续页空列表则结束扫描并返回已累积汇总
- `tests/test_售后页.py`
  - 新增 DOM 批量抓取成功和空页用例
  - 更新导航并拦截/翻页并拦截用例，断言批量抓取调用而不是 API 拦截调用
- `tests/test_售后任务.py`
  - 将旧 fallback 用例替换为“第一页为空返回无待处理售后单”
  - 新增“下一页空列表时结束并返回已扫描汇总”的用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 DOM 批量抓取改造与验证结果

## 影响范围

- 售后列表扫描不再依赖任何 API 拦截时序，统一走 DOM 批量抓取
- 每页只会输出一条 `DOM批量抓取到 N 条售后单` 日志，不再有列表扫描阶段的逐行日志
- `售后任务` 现在不再进入 DOM fallback 分支，扫描总数与写入总数更直接对应分页结果

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `48 passed`
- 已执行全量测试：`python -X utf8 -c "import ctypes, sys, pytest; ctypes.windll.winmm.timeBeginPeriod(1); ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080); sys.exit(pytest.main(['-c','tests/pytest.ini','tests/','-v']))"`，结果 `411 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

为售后扫描循环增加“重复页立即终止”的保护，避免共享分页组件导致的重复扫描。

## 改动文件列表

- `tasks/售后任务.py`
- `tests/test_售后任务.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `tasks/售后任务.py`
  - 在 `执行()` 中新增 `已扫描订单号集合`
  - 每页构建队列记录后，先计算 `当前页订单号集合` 和 `新订单数`
  - 当当前页所有订单号都已扫描过时，输出 `第N页全部为已扫描订单，停止翻页` 日志并结束循环
  - 正常页日志改为 `第N页 扫描X单(新Y单)，写入Z单`
- `tests/test_售后任务.py`
  - 新增“重复页全部已扫描时停止翻页”的回归用例
  - 断言第一页日志包含 `新1单`，且第二页命中“全部为已扫描订单，停止翻页”
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮终止保护与验证结果

## 影响范围

- 当全局分页组件继续翻到已扫描过的“全部”列表页时，售后任务会在 100% 重复页立刻停止
- 总扫描数会更接近真实待处理订单数，减少重复写队列和无效翻页
- 日志里增加 `新订单数`，便于定位分页是否混入重复页

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后任务.py`，结果 `15 passed`
- 已执行全量测试：`python -X utf8 -c "import ctypes, sys, pytest; k=ctypes.windll.kernel32; ctypes.windll.winmm.timeBeginPeriod(1); p=k.GetCurrentProcess(); t=k.GetCurrentThread(); k.SetPriorityClass(p, 0x00000080); k.SetThreadPriority(t, 15); k.SetProcessAffinityMask(p, 1); sys.exit(pytest.main(['-c','tests/pytest.ini','tests/','-v']))"`，结果 `412 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- 全量测试首次运行仍可能命中既有抖动用例 `tests/单元测试/测试_反检测.py::测试_真人模拟器::test_随机延迟在范围内`，本轮在更高优先级和固定 CPU 亲和性下复跑通过
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动

---

## 任务摘要

为售后页翻页后的 DOM 批量抓取增加“首行订单号变化”等待，避免翻页后立即抓到上一页残留 DOM。

## 改动文件列表

- `pages/售后页.py`
- `tests/test_售后页.py`
- `.pipeline/progress.md`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `pages/售后页.py`
  - `翻页并拦截()` 在翻页前先读取当前首行订单号
  - 翻页成功后每 `0.2` 秒轮询一次首行订单号，最多等待 `25` 次
  - 当首行订单号变化时输出 `翻页DOM已刷新: 旧订单号 → 新订单号`，随后执行 `批量抓取当前页()`
  - 若 5 秒内首行订单号没有变化，则输出 `翻页DOM刷新超时，可能已到最后一页` 并返回 `None`
- `tests/test_售后页.py`
  - 更新翻页成功用例，补充旧首行 / 新首行的 `evaluate` 返回值
  - 新增翻页后 DOM 刷新超时返回 `None` 的异常路径用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮翻页 DOM 刷新等待与验证结果

## 影响范围

- 翻页后不再立即抓取旧页残留 DOM，降低重复抓到上一页数据的概率
- 日志会明确显示翻页前后首行订单号变化，便于定位页面刷新状态
- 若最后一页或 DOM 未刷新，会以超时日志结束，不再误抓旧数据

## 注意事项

- 已执行定向回归：`python -m pytest -c tests/pytest.ini -q tests/test_售后页.py tests/test_售后任务.py`，结果 `50 passed`
- 已执行全量测试：`python -X utf8 -c "import ctypes, sys, pytest; k=ctypes.windll.kernel32; ctypes.windll.winmm.timeBeginPeriod(1); p=k.GetCurrentProcess(); t=k.GetCurrentThread(); k.SetPriorityClass(p, 0x00000080); k.SetThreadPriority(t, 15); k.SetProcessAffinityMask(p, 1); sys.exit(pytest.main(['-c','tests/pytest.ini','tests/','-v']))"`，结果 `413 passed, 16 warnings`
- 16 条 warning 为既有存量：10 条来自第三方 `openpyxl`，6 条来自 Celery `datetime.utcnow()` 弃用提示
- `.pipeline/task.md` 仍为当前任务单的本地变更；`data/` 下运行副产物不属于本轮源码改动
