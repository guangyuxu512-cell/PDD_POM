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
