ask 36：聚合执行框架 + 前端执行结果展示 + 推广选择器修复
一、做什么
三件事：
流程步骤支持"聚合执行"：同店铺同批次多条记录在同一步骤聚合处理
前端流程参数Tab展示执行结果（step_results）
修复推广页3个选择器（投产比输入框、确认按钮、开启推广按钮）
二、涉及文件
后端：
backend/services/流程参数服务.py — 新增 查询同批次待聚合记录(shop_id, batch_id, flow_id, step_name) 方法
backend/services/任务服务.py — 执行任务() 增加聚合判断逻辑
backend/services/流程服务.py — 流程 steps 结构支持 aggregable 字段
backend/models/数据结构.py — 流程创建/更新请求里 steps 结构允许 aggregable
前端：
frontend/src/views/FlowManage.vue — 步骤编辑区加"聚合执行"开关
frontend/src/views/FlowParamsTab.vue（或流程参数展示的组件） — 加执行结果列，展示 step_results
选择器：
selectors/推广页选择器.py — 修复3个选择器
三、聚合执行设计
1) flows 表 steps JSON 结构变更：
每个步骤增加 "aggregable" 字段，默认 false
例：{"task_name": "设置推广", "aggregable": true}
​
2) 执行框架逻辑（在 任务服务.py 的执行入口）：
读取当前步骤配置
如果 aggregable == false（默认）:
    正常执行单条，不变
如果 aggregable == true:
    查询同店铺、同batch_id、同flow_id、同current_step的所有记录
    过滤：该步骤的 step_results 里没有 "status": "completed" 的
    合并所有记录的参数：
      - 商品相关字段（商品ID/新商品ID/商品父ID）→ 合并成列表
      - 其他字段（投产比、日限额等）→ 保留各自的值，放入列表
    调用任务执行（传入合并后的参数）
    执行完毕后，逐条回写每条记录的 step_results：
      该步骤名: {"status": "completed", ...各自的结果}
    推进每条记录到下一步
​
3) 回写防重复：
查询聚合记录时过滤条件：
  step_results -> '{步骤名}' -> 'status' 不存在或不等于 'completed'
​
4) 任务层适配：
各任务（发布相似、限时限量、推广）的 _读取商品ID列表 已经支持列表输入。聚合时框架层把多条记录的商品ID合并成列表传入即可。但每个商品的个性化参数（投产比、日限额）需要按商品ID索引：
合并参数格式：
{
  "商品ID列表": ["111", "222", "333"],
  "商品参数映射": {
    "111": {"投产比": 5.0, "日限额": 50},
    "222": {"投产比": 4.0, "日限额": null},
    "333": {"投产比": 5.5, "日限额": 30}
  }
}
​
推广任务从 商品参数映射[商品ID] 读取每个商品各自的投产比和日限额。
四、前端执行结果展示
流程参数Tab表格新增列：
"执行结果" 列：读取 step_results JSON
展示方式：折叠/展开，每个步骤一行，显示步骤名 + status + 关键数据（如新商品ID）
颜色标记：completed=绿色，failed=红色，pending=灰色
五、推广选择器修复
selectors/推广页选择器.py 修改以下3个选择器：
投产比输入框（固定选择器）：
主用：//input[@data-testid="CustomInputNumber" and @class="anq-input" and @placeholder="请输入" and @inputwidth="280"]
备用：//input[@data-testid="CustomInputNumber" and @type="text"]
投产设置确认按钮（动态选择器，绑定商品ID）：
主用：//button[@data-testid="confirm_{商品ID}" and @class="anq-btn anq-btn-primary anq-btn-sm"]
备用：//button[@data-testid="confirm_{商品ID}" and contains(@class, "anq-btn-primary") and .//span[text()="确定"]]
开启推广按钮（固定选择器）：
主用：//button[@data-testid="beginPromotionButton" and @class="anq-btn anq-btn-primary" and contains(span/text(), "开启推广")]
备用：//button[contains(@class, "anq-btn-primary") and not(contains(@class, "anq-btn-disabled")) and @data-testid="beginPromotionButton" and .//span[contains(text(), "开启推广")]]
六、约束
aggregable 默认 false，不影响现有任何流程
聚合查询必须过滤已完成记录，防止重复执行
每个商品的个性化参数通过 商品参数映射 字典索引，不丢失
前端流程编排步骤编辑器里加"聚合执行"Switch开关，保存到 steps JSON
前端执行结果列不影响现有列布局，加在最后
选择器修复不改变 POM 层和任务层代码，只改选择器配置
测试全部同步更新，确保 pytest 通过