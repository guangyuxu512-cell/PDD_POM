# Task 4：短信验证码输入后继续判断登录结果

## 背景
当前登录任务检测到短信验证码后直接 return "需要短信验证码"，任务就结束了。
人工在浏览器里输入完验证码后，没有代码继续判断登录是否成功、也没有保存 Cookie。

## 目标
改为：检测到短信验证码后，轮询等待人工输入完成（页面跳转到首页），然后保存 Cookie。

## 改动范围
- tasks/登录任务.py（主要改动）
- pages/登录页.py（可选，补一个点击验证码确认按钮方法）

## 具体指令

### 1) tasks/登录任务.py — 替换短信验证码处理逻辑

找到这段代码（当前逻辑）：

    if await 登录.检测短信验证码():
        await 上报("需要短信验证码，等待人工输入", 店铺ID)
        await 登录.截图登录状态()
        return "需要短信验证码"

替换为：

    if await 登录.检测短信验证码():
        await 上报("需要短信验证码，等待人工输入（最多等待120秒）", 店铺ID)
        await 登录.截图登录状态()

        # 轮询等待人工输入验证码后页面跳转到首页
        import asyncio
        已成功 = False
        for i in range(40):  # 最多等 120 秒，每 3 秒检查一次
            await asyncio.sleep(3)
            try:
                当前URL = 页面.url
                if "mms.pinduoduo.com/home" in 当前URL:
                    已成功 = True
                    break
            except Exception:
                # 页面可能在跳转中，继续等
                continue

        if 已成功:
            await 上报("[成功] 短信验证码验证通过，已跳转到首页", 店铺ID)
            try:
                await 登录.保存Cookie(店铺ID)
                await 上报("[成功] Cookie 已保存到文件", 店铺ID)
            except Exception as e:
                await 上报(f"[警告] Cookie 保存失败: {str(e)}", 店铺ID)
            try:
                await 登录.截图登录状态()
            except Exception:
                pass
            return "成功"
        else:
            await 上报("[失败] 等待短信验证码超时（120秒）", 店铺ID)
            try:
                await 登录.截图登录状态()
            except Exception:
                pass
            return "失败"

注意：import asyncio 如果文件顶部已经有了就不用重复 import。

### 2) pages/登录页.py — 可选：补一个点击验证码确认方法

如果拼多多短信验证码输入后需要再点一次确认按钮，补这个方法：

    async def 点击验证码确认(self) -> None:
        """短信验证码输入后点击确认按钮"""
        确认按钮 = self.页面.get_by_test_id("beast-core-button")
        if inspect.isawaitable(确认按钮):
            确认按钮 = await 确认按钮
        await 确认按钮.click()
        await self.随机延迟(2, 4)

说明：当前方案 A 是靠轮询 URL 跳转来判断的，不主动点确认。
如果实际测试发现人工输入验证码后需要代码帮点确认，再在轮询逻辑中加入调用。
当前先加方法但不在 Task 层调用，后续按需启用。

## 架构红线
- Task 层不写页面选择器
- 轮询中只检查 URL，不操作页面元素
- 保存 Cookie 调用现有的 登录.保存Cookie(店铺ID)，不要重写
- 保持 @自动回调("登录") 装饰器
- 保持所有 上报(...) 步骤

## 验收标准
- 检测到短信验证码后不再直接 return
- 轮询最多等待 120 秒
- 人工输入验证码后页面跳转到首页，任务返回 "成功" 并保存 Cookie
- 超时未跳转，任务返回 "失败"
- 运行 python -m pytest -c tests/pytest.ini -q 全部通过

## 不动的文件
- pages/基础页.py
- tasks/基础任务.py
- tasks/注册表.py
- browser/*
- backend/*
- frontend/*