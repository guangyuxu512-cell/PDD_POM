Hotfix 46A-fix：列表页抓取 JS 重写 + 数据清洗
修改 pages/售后页.py 中的 获取第N行信息 和 扫描所有待处理，用精准的 class 选择器提取：
async def 获取第N行信息(self, 行号: int) -> dict[str, str]:
    """基于真实 DOM 结构精准提取列表页第 N 行信息。"""
    await self.操作前延迟()
    结果 = await self.页面.evaluate("""
        (行号) => {
            const 清洗 = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
            
            // 找到所有 order_item
            const 所有行 = document.querySelectorAll(
                'div[class*="after-sales-table_order_item"]'
            );
            if (行号 > 所有行.length) return null;
            const 行 = 所有行[行号 - 1];
            
            // ---- 头部信息 ----
            const 订单号节点 = 行.querySelector('[class*="table-item-header_sn__"]');
            const 订单号 = 清洗(订单号节点 ? 订单号节点.textContent : '');
            
            const 申请时间节点 = 行.querySelector(
                '[class*="table-item-header_apply_time"] span'
            );
            const 申请时间 = 清洗(申请时间节点 ? 申请时间节点.textContent : '');
            
            const 剩余时间节点 = 行.querySelector('[class*="table-item-header_time__"]');
            const 剩余处理时间 = 清洗(剩余时间节点 ? 剩余时间节点.textContent : '');
            
            // ---- 内容区按列读取 ----
            const 所有列 = 行.querySelectorAll('[class*="after-sales-table_item_cell"]');
            // cell[0]=订单信息 cell[1]=金额 cell[2]=发货状态 cell[3]=售后类型
            // cell[4]=售后状态 cell[5]=售后协商 cell[6]=售后原因 cell[7]=操作
            
            const 读列 = (索引) => {
                if (索引 >= 所有列.length) return '';
                return 清洗(所有列[索引].textContent);
            };
            
            // 订单信息列 - 精准提取商品名和规格
            const 商品名节点 = 所有列[0] ? 
                所有列[0].querySelector('[class*="order-info_main"]') : null;
            const 规格节点 = 所有列[0] ? 
                所有列[0].querySelector('[class*="order-info_sub"]') : null;
            const 商品名称 = 清洗(商品名节点 ? 商品名节点.textContent : '');
            const 商品规格 = 清洗(规格节点 ? 规格节点.textContent : '');
            
            // 金额列 - 分别提取实收和退款
            const 实收节点 = 所有列[1] ? 
                所有列[1].querySelector('[class*="amount_dotted"]') : null;
            const 退款节点 = 所有列[1] ? 
                所有列[1].querySelector('[class*="amount_refund"]') : null;
            const 实收金额 = 清洗(实收节点 ? 实收节点.textContent : '');
            const 退款金额 = 清洗(退款节点 ? 退款节点.textContent : '');
            
            // 售后状态列 - 只取第一个 div 的文本（排除链接）
            const 售后状态节点 = 所有列[4] ? 所有列[4].querySelector('div') : null;
            const 售后状态 = 清洗(售后状态节点 ? 售后状态节点.textContent : '');
            
            // 操作列 - 提取所有按钮文本
            const 操作按钮 = 所有列[7] ? 
                Array.from(所有列[7].querySelectorAll('a span, button span'))
                    .map(s => 清洗(s.textContent))
                    .filter(t => t.length > 0) : [];
            
            return {
                订单号: 订单号,
                申请时间: 申请时间,
                剩余处理时间: 剩余处理时间,
                商品名称: 商品名称,
                商品规格: 商品规格,
                实收金额: 实收金额,
                退款金额: 退款金额,
                发货状态: 清洗(读列(2)),
                售后类型: 清洗(读列(3)),
                售后状态: 售后状态,
                售后协商: 清洗(读列(5)),
                售后原因: 清洗(读列(6)),
                操作按钮: 操作按钮,
            };
        }
    """, 行号)
    await self.操作后延迟()
    if 结果:
        print(f"[售后页] 第{行号}行: 订单={结果.get('订单号')}, "
              f"类型={结果.get('售后类型')}, 退款={结果.get('退款金额')}")
    return dict(结果 or {})
​
同时修改 获取售后单数量：
async def 获取售后单数量(self) -> int:
    """返回当前列表页的售后单数量。"""
    return await self.页面.evaluate("""
        () => document.querySelectorAll(
            'div[class*="after-sales-table_order_item"]'
        ).length
    """)
​
还有 售后页选择器.py 里的行选择器也要改：
售后单行 = 选择器配置(
    主选择器='div[class*="after-sales-table_order_item"]',
    备选选择器=[
        '//div[contains(@class, "after-sales-table_order_item")]',
    ],
)
​
预期清洗后写入 SQLite 的数据
订单号: 260311-138328215900728
申请时间: 2026-03-14 17:13:26
剩余处理时间: 5天8时29分52秒
商品名称: 大捞粗篱用漏瓢防烫捞面勺大号大漏漏勺油炸木纹厨房用品孔家
商品规格: x1；富贵木柄特厚升级款【12#大漏】1支
实收金额: ¥3.79
退款金额: 退款：¥3.61
发货状态: 已发货
售后类型: 退货退款
售后状态: 退货退款，待商家确认收货
售后原因: 不想要了
操作按钮: ["同意退款", "查看详情", "添加备注"]
​
干净、每个字段对应一个值、没有 HTML。
