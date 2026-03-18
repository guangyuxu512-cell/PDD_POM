售后配置系统重构
背景
当前售后决策引擎的配置通过旧的规则服务（通用条件匹配引擎）确定，存在以下问题：
1. 规则服务的条件匹配在售后决策中未使用——决策引擎已完全硬编码全部业务逻辑
2. _组装规则配置()只要把规则的actions当配置存储用，而不是当规则引擎用
3. 默认售后规则和实际决策逻辑完全不对应
4. 配置无法按店铺隔离，无专用UI，编辑体验差
5. 上次 Codex 任务声称创建了售后配置服务.py但实际尚未实现
目标
1. 新建aftersale_config表（按shop_id隔离）
2. 新建售后配置服务.py（CRUD + 默认值 + 校验）
3. 新建REST API接口
4. 新建前端「售后配置」页面（表单化UI，非JSON编辑）
5. 改造售后任务.py从配置服务读取，不再依赖规则服务
6. 清理规则服务中的售后默认规则
7. 前置隐藏旧的「规则配置」选项卡
￼
一、数据库：aftersale_config表
文件：backend/models/售后配置模型.py（新建）
CREATE TABLE IF
 NOT EXISTS aftersale_config (
    id                          
INTEGER PRIMARY KEY
 AUTOINCREMENT,
    shop_id                     
TEXT NOT NULL
 UNIQUE,

    -- ═══ 全局开关 ═══
    启用自动售后                 
INTEGER DEFAULT 1
,
    不支持自动处理类型           
TEXT DEFAULT '["补寄","维修","换货"]'
,

    -- ═══ 退货退款配置 ═══
    退货物流白名单               
TEXT DEFAULT '[]'
,
    退货等待时间                 
TEXT DEFAULT '{"刚发出":3,"中途运输":1,"到达目的市":0.25}'
,
    需要入库校验                 
INTEGER DEFAULT 0
,
    自动退款金额上限             
REAL DEFAULT 50.0
,

    -- ═══ 仅退款配置 ═══
    仅退款_启用                  
INTEGER DEFAULT 0
,
    仅退款_自动同意金额上限      
REAL DEFAULT 10.0
,
    仅退款_需要拒绝              
INTEGER DEFAULT 0
,
    仅退款_最大拒绝次数          
INTEGER DEFAULT 3
,
    仅退款_拒绝后等待分钟        
INTEGER DEFAULT 30
,
    仅退款_有图片转人工          
INTEGER DEFAULT 1
,
    仅退款_拒收退回自动同意      
INTEGER DEFAULT 1
,

    -- ═══ 拒收退款配置 ═══
    拒收退款_启用                
INTEGER DEFAULT 1
,
    拒收退款_需要检查物流        
INTEGER DEFAULT 1
,

    -- ═══ 通知配置 ═══
    飞书通知_启用                
INTEGER DEFAULT 1
,
    飞书通知_webhook             
TEXT DEFAULT ''
,
    微信通知_启用                
INTEGER DEFAULT 0
,
    微信通知_群ID                
TEXT DEFAULT ''
,
    通知场景                     
TEXT DEFAULT '["人工审核","金额超限","派件人不匹配","入库校验"]'
,

    -- ═══ 弹窗与备注 ═══
    弹窗偏好                     
TEXT DEFAULT '{}'
,
    备注模板                     
TEXT DEFAULT '{"退货匹配":"退回物流匹配，自动退款","人工":"转人工处理","拒绝":"系统拒绝第{n}次"}'
,

    -- ═══ 扫描与执行策略 ═══
    每批最大处理数               
INTEGER DEFAULT 50
,
    单条超时秒数                 
INTEGER DEFAULT 60
,
    失败重试次数                 
INTEGER DEFAULT 3
,
    扫描间隔分钟                 
INTEGER DEFAULT 30
,
    优先处理类型                 
TEXT DEFAULT '["退货退款","仅退款"]'
,

    -- ═══ 飞书多维表 ═══
    飞书多维表_启用              
INTEGER DEFAULT 0
,
    飞书多维表_app_token         
TEXT DEFAULT ''
,
    飞书多维表_table_id          
TEXT DEFAULT ''
,
    飞书多维表_写入场景          
TEXT DEFAULT '["已签收","入库校验"]'
,

    -- ═══ 时间戳 ═══
    created_at                  
TEXT DEFAULT (datetime('now','localtime'
)),
    updated_at                  
TEXT DEFAULT (datetime('now','localtime'
))
);
Copy
白名单字段格式
退货物流白名单存储 JSON 仓库，每条：
[
  {
    "名称": "杭州仓-韵达"
,
    "快递公司": "韵达"
,
    "地区关键词": ["杭州", "萧山", "余杭"
],
    "派件人": ["张三", "李四"
],
    "启用": true
  }
]
Copy
• 快递公司：精确匹配，"*"表示不限
• 地区关键词：地图形状到达{词}/ 到{词}/{词}市
• 派件人：派送中/已签收阶段在账单+派件人+网点文本中匹配
文件：backend/models/数据库.py（修改）
• 在获取建表语句列表()中添加售后配置建表SQL
• 在初始化数据库()中调用初始化售后配置表(连接)
• 添加_补齐旧版表结构()中对aftersale_config表的旧字段补齐逻辑
￼
二、实验室服务：售后配置服务.py（新建）
文件：backend/services/售后配置服务.py
提供以下方法：
class 售后配置服务
:
    # 默认配置常量（所有字段的默认值，和建表 DEFAULT 保持一致）
    默认配置: ClassVar[dict
]

    async def 获取配置(self, shop_id: str) -> dict
:
        """读取指定店铺配置，不存在则自动插入默认配置并返回"""

    async def 更新配置(self, shop_id: str, data: dict) -> dict
:
        """部分更新配置，自动处理 JSON 字段序列化，更新 updated_at"""

    async def 获取所有配置(self) -> list[dict
]:
        """返回所有店铺配置列表"""

    async def 删除配置(self, shop_id: str) -> bool
:
        """删除指定店铺配置"""

    async def 初始化默认配置(self, shop_id: str) -> dict
:
        """为新店铺创建默认配置"""

    def _反序列化(self, row: dict) -> dict
:
        """将 SQLite 行转为 Python dict，JSON 字段自动 parse"""

    def _校验白名单(self, 白名单: list) -> list
:
        """校验白名单格式，每条必须有 快递公司/地区关键词/派件人"""
Copy
关键要求：
• JSON字段（进口物流白名单、进口等待时间、不支持自动处理类型、通知场景、弹窗偏好、备注模板、优先处理类型、飞书多维表_写入场景）读取时自动json.loads，读取时自动json.dumps
• 获取配置()在记录不存在时自动INSERT默认配置（upsert 语义）
• 所有写操作自动更新updated_at
￼
三、云端API：售后配置接口.py（新建）
文件：backend/api/售后配置接口.py
GET    /api/aftersale-config/{shop_id}   → 获取配置
PUT    /api/aftersale-config/{shop_id}   → 更新配置（部分更新）
GET    /api/aftersale-config             → 获取所有店铺配置列表
DELETE /api/aftersale-config/{shop_id}   → 删除配置
Copy
文件：backend/api/路由注册.py（修改）
添加：
from backend.api.售后配置接口 import 路由 as 售后配置路由
Copy
在所有路由列表中加入售后配置路由。
￼
四、售后任务改造
文件：tasks/售后任务.py（修改）
删除：
• from backend.services.规则服务 import 规则服务导入
• self._规则服务 = 规则服务()初始化
• _组装规则配置()方法
• 执行()和_处理单条()中对规则服务.匹配规则()的呼吁
新增：
• from backend.services.售后配置服务 import 售后配置服务导入
• self._配置服务 = 售后配置服务()初始化
• 在执行()引用中配置 = await self._配置服务.获取配置(店铺ID)
• 将配置 dict 直接传给self._决策引擎.决策(详情, 配置, 记录)
改造执行()方法：
• 读取配置后检查启用自动售后，如果为False直接返回“售后自动处理已关闭”
• 不支持自动处理类型从配置读取，替代硬编码的["补寄", "维修", "换货"]
• 每批最大处理数从配置读取，限制单次处理数量
文件：backend/services/售后决策引擎.py（修改）
参数对齐。决策()方法的规则配置参数改名为配置，内部字段名新配置表字段名：
• 退货物流白名单→ 不变
• 退货等待时间→ 不变
• 需要入库校验→ 不变
• 自动退款金额上限→ 不变
• 自动同意金额上限→仅退款_自动同意金额上限
• 需要拒绝→仅退款_需要拒绝
• 弹窗偏好→ 不变
在_决策_退款()中增加读取：
• 仅退款_最大拒绝次数（替代硬编码3）
• 仅退款_有图片转人工（替代硬编码True）
• 仅退款_拒收退回自动同意
在_决策_退货退款()底层增加读取：
• 拒收退款_启用、拒收退款_需要检查物流
￼
五、清理规则服务售后部分
文件：backend/services/规则服务.py（修改）
• 删除默认售后规则列表（5条规则默认全部删除）
• 初始化默认售后规则()方法体改为pass（保留方法签名，避免调用方报错）
• 保留规则服务类本身和通用CRUD/匹配逻辑（未来其他业务可能用）
文件：backend/models/数据库.py（修改）
• 初始化数据库()中初始化默认售后规则()的try- except 块占有，但不会再插入售后规则
￼
六、前端：售后配置页面（新建）
文件：frontend/src/views/AftersaleConfig.vue（新建）
页面结构（使用已有的 Element Plus / 或项目已有的 UI 风格）：
顶部：店铺选择器（下拉，复用 /api/shops 接口）
       ↓ 切换后自动加载该店铺配置

卡片 1：全局设置
├── 启用自动售后（Switch 开关）
└── 不支持自动处理类型（Tag 多选：补寄/维修/换货/自定义输入）

卡片 2：退货退款
├── 白名单表格（可增删改行）
│   每行：名称(input) / 快递公司(input,默认*) / 地区关键词(tag输入) / 派件人(tag输入) / 启用(switch)
├── 等待时间
│   三个数字输入框：刚发出(天) / 中途运输(天) / 到达目的市(小时，显示时转为天)
├── 入库校验（Switch）
└── 自动退款金额上限（InputNumber，单位元）

卡片 3：仅退款
├── 启用开关
├── 自动同意金额上限（InputNumber）
├── 拒绝策略：启用开关 + 最大拒绝次数(InputNumber) + 拒绝后等待(InputNumber,分钟)
├── 有图片转人工（Switch）
└── 拒收退回自动同意（Switch）

卡片 4：通知配置
├── 飞书通知：启用开关 + webhook输入框
├── 微信通知：启用开关 + 群ID输入框
└── 通知场景（Checkbox 多选：人工审核/金额超限/派件人不匹配/入库校验）

卡片 5：执行策略
├── 每批最大处理数（InputNumber）
├── 单条超时秒数（InputNumber）
├── 失败重试次数（InputNumber）
└── 扫描间隔分钟（InputNumber）

卡片 6：飞书多维表
├── 启用开关
├── app_token 输入框
├── table_id 输入框
└── 写入场景（Checkbox 多选）

底部：保存按钮 + 重置为默认按钮
Copy
关键UI要求：
• 风格页面和现有页面（ShopManage.vue、TaskParamsManage.vue）保持一致
• 白色名单表格支持行内编辑、添加行、删除行
• 地区关键词和派件人使用标签输入（输入后回车添加，支持删除）
• 修改保存时调用PUT /api/aftersale-config/{shop_id}，只发送过的字段
• 加载时调用GET /api/aftersale-config/{shop_id}
• 页面初始加载默认时选中第一个店铺
文件：frontend/src/api/aftersaleConfig.ts（新建）
export const getAftersaleConfig = (shopId: string) =>
  request.get(`/api/aftersale-config/${shopId}`)

export const updateAftersaleConfig = (shopId: string, data: Record<string, any>) =>
  request.put(`/api/aftersale-config/${shopId}`, data)

export const getAllAftersaleConfigs = () =>
  request.get('/api/aftersale-config')

export const deleteAftersaleConfig = (shopId: string) =>
  request.delete(`/api/aftersale-config/${shopId}`)
Copy
文件：frontend/src/router/index.ts（修改）
添加路由：
{
  path: '/aftersale-config',
  name: 'AftersaleConfig',
  component: () => import('../views/AftersaleConfig.vue')
}
Copy
文件：frontend/src/App.vue（修改）
在侧边栏nav中添加导航项（置于“业务管理”下方）：
<router-link to="/aftersale-config" class="nav-item">
  <span class="icon">🛡️</span>
  <span>售后配置</span>
</router-link>
Copy
文件：frontend/src/views/DataManage.vue（修改）
删除隐藏或「规则配置」选项卡。RuleManage.vue 本身保留文件不删除（其他业务可能用），但从 DataManage 的选项卡列表中去掉。
￼
七、迁移策略
在backend/services/售后配置服务.py中添加迁移方法：
async def 从规则服务迁移(self) -> int
:
    """
    检查 rules 表中 business='售后' 的启用规则，
    提取 actions 中的配置字段写入 aftersale_config，
    然后将这些规则标记为 enabled=0。
    返回迁移的规则数量。
    """
Copy
在backend/models/数据库.py的初始化数据库()调用此迁移方法（try- except 包裹，失败不停止启动）。
￼
八、测试
新增测试文件：tests/test_售后配置服务.py
覆盖：
1. 获取配置 - 不存在时自动创建默认配置
2. 获取配置 - 已存在时返回现有配置
3. 更新配置 - 部分更新（只改白名单）
4. 更新配置 - JSON 字段序列化/反序列化正确
5. 白名单审核 - 格式正确通过
6. 白名单校验 - 缺少必填字段报错
7. 删除配置
8. 迁移方法 - 从旧规则迁移到新配置表
新增测试文件：tests/test_售后配置接口.py
覆盖：
1. GET 配置 - 200 + 默认值
2. PUT 配置 - 部分更新 + 验证返回
3. 获取所有配置 - 多店铺
4. 删除配置
修改测试文件：已有售后测试
确保在新配置路径下的现有测试仍然通过售后决策引擎。售后任务
￼
九、文件清单
操作
文件路径
新建
backend/models/售后配置模型.py
新建
backend/services/售后配置服务.py
新建
backend/api/售后配置接口.py
新建
frontend/src/views/AftersaleConfig.vue
新建
frontend/src/api/aftersaleConfig.ts
新建
tests/test_售后配置服务.py
新建
tests/test_售后配置接口.py
修改
backend/models/数据库.py— 导入售后配置建表 + 迁移调用
修改
backend/api/路由注册.py— 添加售后配置路由
修改
tasks/售后任务.py— 删除规则服务依赖，改用售后配置服务
修改
backend/services/售后决策引擎.py— 参数名对齐新配置字段
修改
backend/services/规则服务.py— 删除默认售后规则，迁移方法清空
修改
frontend/src/router/index.ts—添加/aftersale-config 路由
修改
frontend/src/App.vue— 侧边栏添加“售后配置”导航
修改
frontend/src/views/DataManage.vue— 隐藏“规则配置”选项卡
十、验收标准
1. 启动后aftersale_config表自动创建
2. 旧规则 表中business='售后' 的规则自动迁移到新表并标记已禁用
3. GET /api/aftersale-config/{shop_id}对新店返回默认配置
4. PUT /api/aftersale-config/{shop_id}部分更新生效
5. 前置「售后配置」页面可正常加载、编辑、保存白名单及所有参数
6. 白色名单表格支持增删改行，标签输入正常
7. 售后任务从配置服务读取配置，不再调用规则服务
8. 数据管理页面不再显示「规则配置」选项卡
9. 全部量回归测试通过（现有381个测试 + 新增测试）