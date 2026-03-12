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
