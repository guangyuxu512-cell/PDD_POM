任务目标： 用 Tailwind + Headless UI 重写 4 个最复杂的页面。
需要重写的文件：
frontend/src/views/FlowManage.vue（26KB）
frontend/src/views/AftersaleConfig.vue（31KB）
frontend/src/views/RuleManage.vue（28KB）
frontend/src/views/ScheduleManage.vue（20KB）
设计规范： 与任务 5 完全一致。额外注意：
所有 <select> 原生下拉 → 改为 Headless UI Listbox，触发器样式与输入框一致
Tab 切换（如果有） → 用 Headless UI TabGroup
复杂表单 → 分 section 排列，每个 section 一个标题（text-sm font-medium text-gray-900），section 之间用 border-t border-gray-100 pt-4 mt-4 分隔
大表格 → 加 overflow-x-auto 水平滚动容器
空状态 → 居中 text-sm text-gray-400 + 简单 emoji
所有文件删除 <style> 块。只改 template 和 style，不改 script 业务逻辑。
验收方式：
4 个页面全部正常渲染
所有弹窗用新的 Headless UI Modal
没有任何残留的 <style scoped> 或手写 CSS
没有任何蓝色
整站风格统一，像同一个产品