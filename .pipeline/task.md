只需改一个选择器，所有用到 `table-item-header_sn` 的地方都改为排除 label：

#### `pages/售后页.py` — 全局替换选择器

**所有 JS 中的订单号选择器**，从：

```jsx
'[class*="table-item-header_sn"]'
```

改为：

```jsx
'span[class*="table-item-header_sn__"]'
```

加 `__` 后缀就能精确匹配到 `table-item-header_sn__2gbGk`，**排除** `table-item-header_sn_label__3wQue`。

受影响的方法有 3 个：

1. **`批量抓取当前页()`** — 订单号提取
2. **`翻页并抓取()`** — 翻页前后的首行订单号对比（2处）
3. **`获取第N行信息()`** — 已经是 `[class*="table-item-header_sn__"]` ✅ 不用改

具体就是把这些 JS 里的：

```jsx
row.querySelector('[class*="table-item-header_sn"]')
```

全部替换成：

```jsx
row.querySelector('span[class*="table-item-header_sn__"]')
```