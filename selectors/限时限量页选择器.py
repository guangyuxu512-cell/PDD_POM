from selectors.选择器配置 import 选择器配置


class 限时限量页选择器:
    """限时限量页元素选择器。"""

    展开更多设置按钮 = 选择器配置(
        主选择器="a[data-tracking-viewid='expand_more_settings']",
        
        备选选择器=[
            "a:has-text('更多设置')",

            "a[data-testid='beast-core-button-link']:has-text('更多设置')"
        ]
    )
    自动创建活动勾选项 = 选择器配置(
        主选择器="div[data-tracking-impr-viewid='auto_create']",
        
        备选选择器=[
            # 🥈 亚军方案：精准文字匹配
            "span:has-text('活动结束后自动创建')",
            
            # 🥉 季军方案：模糊匹配 (防止文案微调)
            "div:has-text('自动创建，提升下单')"
        ]
    )
    选择商品按钮 = 选择器配置(
        主选择器="button[data-tracking-viewid='el_event_merchandise']",
        
        备选选择器=[
            # 🥈 亚军方案：精准文字匹配
            "button:has-text('选择商品')",
            
            # 🥉 季军方案：组合拳 (类型 + 文字)
            "button[type='button']:has-text('选择商品')"
        ]
    )
    选择商品弹窗_搜索输入框 = 选择器配置(
        主选择器="input[placeholder='商品ID/商品名称']",
        备选选择器=["input[placeholder*='商品ID']"]
    )
    选择商品弹窗_查询按钮 = 选择器配置(
        主选择器="div[data-testid='beast-core-input-suffix'] :text('查询')",
        备选选择器=[
            # 备选：找到输入框的邻居
            "div.IPT_suffixWrapper_5-154-0:has-text('查询')", 
            # 暴力找弹窗里的查询字样
            ".modal-body :text('查询')" 
        ]
    )
    选择商品弹窗_第一行勾选框 = 选择器配置(
        主选择器="tr[data-testid='beast-core-table-body-tr'] >> nth=0 >> div[data-testid='beast-core-checkbox-checkIcon']",
        
        备选选择器=[
            # 🥈 亚军方案：回退到点 Label (如果 div 点不到)
            "tr[data-testid='beast-core-table-body-tr'] >> nth=0 >> label[data-testid='beast-core-checkbox']",
            
            # 🥉 季军方案：暴力坐标点击 (force click Input)
            "tr[data-testid='beast-core-table-body-tr'] >> nth=0 >> input[type='checkbox']"
        ]
    )
    选择商品弹窗_确认选择按钮 = 选择器配置(
        主选择器="button:has-text('确认选择')",
        
        备选选择器=[
            # 🥈 亚军方案：利用 span 标签定位
            # 逻辑：找 span 内容是"确认选择"，然后反查它的父级 button
            "span:text-is('确认选择') >> xpath=..",
            
            # 🥉 季军方案：组合 generic testid + 文字
            "button[data-testid='beast-core-button']:has-text('确认选择')"
        ]
    )
    创建按钮 = 选择器配置(
        主选择器="button[data-tracking-viewid='create_button_shared']",
        备选选择器=["button:has-text('创建')"]
    )
    创建成功提示 = 选择器配置(
        主选择器="button[data-tracking-viewid='el_continue_create_promotion']",
        
        备选选择器=[
            # 🥈 亚军方案：简单粗暴找文字
            "div:has-text('创建成功')",
            # 🥉 季军方案：找那个绿色的大勾图标
            "svg[data-testid='beast-core-icon-check-circle_filled']"
        ]
    )

    @staticmethod
    def 商品行折扣输入框(商品ID: str) -> 选择器配置:
        标准商品ID = str(商品ID).strip()
        return 选择器配置(
            主选择器=(
                f'//tr[.//div[text()="ID: {标准商品ID}"]]'
                '//input[@data-testid="beast-core-inputNumber-htmlInput"]'
            ),
            备选选择器=[
                (
                    f'//tr[.//div[contains(text(), "{标准商品ID}")]]'
                    '//input[@data-testid="beast-core-inputNumber-htmlInput"]'
                )
            ],
        )
