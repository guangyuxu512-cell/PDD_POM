Task 38.5：限时限量折扣输入框选择器修正 + 推广成功多条件检测
一、做什么
限时限量逐商品折扣输入框选择器修正（加 placeholder 匹配）
推广成功检测改为多条件组合判断，任一命中即成功
二、涉及文件
selectors/限时限量选择器.py — 折扣输入框选择器修正
selectors/推广页选择器.py — 新增多种成功检测选择器
pages/推广页.py — 等待推广成功() 方法改为多条件竞争检测
pages/限时限量页.py — 确认折扣输入框选择器已更新
测试同步更新
三、限时限量折扣输入框选择器修正
selectors/限时限量选择器.py 修改：
商品行折扣输入框（动态选择器，绑定商品ID）：
主用：//tr[.//div[text()="ID: {商品ID}"]]//input[@data-testid="beast-core-inputNumber-htmlInput" and @placeholder="1～9.7"]
备用：//tr[.//div[contains(text(), "{商品ID}")]]//input[@data-testid="beast-core-inputNumber-htmlInput"]
四、推广成功多条件检测
selectors/推广页选择器.py 新增以下成功检测选择器：
条件1 — Toast 成功提示：
//div[contains(@class, "anq-message")]//span[contains(text(), "成功")]
//div[contains(@class, "anq-message")]//span[contains(text(), "已开启")]
条件2 — "开启推广"按钮消失：
//button[@data-testid="beginPromotionButton"]（等待此元素消失/不可见）
条件3 — 页面出现"推广中"状态：
//*[contains(text(), "推广中")]
五、POM 修改
pages/推广页.py 修改 等待推广成功() 方法：
async def 等待推广成功(超时秒数: int = 15) -> bool:
    在超时时间内，每 0.5 秒轮询检查以下条件，任一命中即返回 True：
    
    1. Toast 检测：页面存在包含"成功"或"已开启"的 anq-message 元素
    2. URL 检测：当前 URL 包含 "promotion/list" 且不包含 "create"（跳转到列表页）
    3. 按钮消失：beginPromotionButton 不再可见或不存在于 DOM
    4. 状态文字：页面出现"推广中"文字
    
    任一条件满足 → return True
    超时 → 截图("推广成功检测超时") → return False
​
实现方式：用循环轮询而非单一 wait_for_selector，每轮依次检查4个条件。
六、约束
折扣输入框主用选择器必须带 @placeholder="1～9.7" 精确匹配
推广成功检测超时设 15 秒，覆盖网络慢的情况
多条件检测用轮询方式，不要用 Promise.all（那是等全部，我们要任一）
Toast 检测要兼容"操作成功"/"推广已开启"/"开启成功"等文字变体，用 contains
URL 检测注意：如果是在推广列表页点的添加推广，成功后可能回到列表页，URL 从 create 变回 list
测试同步更新，确保 pytest 通过