Task 38.2：极速起量确认弹窗选择器精确匹配修复
一、做什么
修复极速起量确认弹窗误匹配投产比弹窗"确定"按钮的问题。去掉通用"确定"选择器，只用精确匹配"确定关闭"。
二、涉及文件
selectors/推广页选择器.py — 替换极速起量确认弹窗选择器
pages/推广页.py — 修改确认关闭极速起量方法的匹配逻辑
测试同步更新
三、选择器修改
selectors/推广页选择器.py：
删除（误匹配投产比弹窗确定按钮）：
(//button[contains(@class, "anq-btn-primary") and span[text()="确定"]])[last()]
替换为两个精确选择器：
极速起量确认关闭 形态1（固定选择器，匹配"确定关闭"文字）：
主用：//button[span[text()="确定关闭"]]
备用：//button[.//span[text()="确定关闭"]]
极速起量确认关闭 形态2（动态选择器，绑定商品ID）：
主用：//button[@data-testid="assist_close_{商品ID}"]
备用：//button[@data-testid="assist_close_{商品ID}"]//span[text()="确定关闭"]/parent::button
四、POM 修改
pages/推广页.py 修改 确认关闭极速起量(商品ID) 方法：
async def 确认关闭极速起量(商品ID: str) -> bool:
    # 优先尝试形态2（带商品ID，最精确）
    形态2 = 等待元素出现(assist_close_{商品ID}, 超时2秒)
    如果找到 → 点击 → 延时1-2秒 → return True
    
    # 再尝试形态1（"确定关闭"文字匹配）
    形态1 = 等待元素出现(//button[span[text()="确定关闭"]], 超时2秒)
    如果找到 → 点击 → 延时1-2秒 → return True
    
    # 都没找到
    截图("极速起量确认弹窗未找到")
    return False
​
关键：绝不尝试匹配通用的"确定"按钮，只匹配"确定关闭"。
五、约束
完全移除所有包含 span[text()="确定"] 的极速起量确认选择器
只保留匹配 "确定关闭" 文字或 assist_close_{商品ID} 的选择器
不影响全局起量确认弹窗（那个也是"确定关闭"文字，但在不同时机触发，不冲突）
不影响投产比弹窗底部的"确定"按钮（那个是投产设置确认，由其他方法处理）
测试同步更新，确保 pytest 通过