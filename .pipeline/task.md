文件：frontend/src/views/FlowManage.vue

目标：把流程管理页从大卡片布局改为紧凑信息密度。

─── 修改 1：统计栏压缩 ───

删除 <template> 中以下整段：

  <section class="summary-grid">
    <article class="summary-card">
      <span class="summary-label">流程数</span>
      <strong> totalFlows </strong>
      <span class="summary-note">已保存模板</span>
    </article>
    <article class="summary-card">
      <span class="summary-label">步骤总数</span>
      <strong> totalSteps </strong>
      <span class="summary-note">来自全部流程</span>
    </article>
    <article class="summary-card">
      <span class="summary-label">可用任务</span>
      <strong> tasks.length </strong>
      <span class="summary-note">自动读取后端注册表</span>
    </article>
  </section>

替换为一行内联统计文本：

  <p class="inline-stats">
    共 <strong> totalFlows </strong> 个流程 · 
    <strong> totalSteps </strong> 个步骤 · 
    <strong> tasks.length </strong> 个可用任务
  </p>

删除 <style> 中 .summary-grid、.summary-card、.summary-label、.summary-card strong、.summary-note 相关样式。

新增样式：
  .inline-stats {
    color: #64748b;
    font-size: 14px;
    margin: 0;
  }
  .inline-stats strong {
    color: #1e293b;
    font-weight: 700;
  }

─── 修改 2：模板列表改为表格 ───

删除 <template> 中以下整段（从 <div v-else class="flow-grid"> 到对应的 </div>）：

  <div v-else class="flow-grid">
    <article v-for="flow in flows" :key="flow.id" class="flow-card">
      ...整个 flow-card...
    </article>
  </div>

替换为 HTML 表格：

  <table v-else class="flow-table">
    <thead>
      <tr>
        <th style="width:48px">#</th>
        <th style="width:140px">流程名称</th>
        <th>描述</th>
        <th style="width:64px">步骤</th>
        <th>步骤摘要</th>
        <th style="width:140px">操作</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(flow, index) in flows" :key="flow.id">
        <td class="cell-center"> index + 1 </td>
        <td>
          <a class="flow-name-link" @click="openEditModal(flow)"> flow.name </a>
        </td>
        <td class="cell-desc"> flow.description || '—' </td>
        <td class="cell-center">
          <span class="step-badge"> flow.steps.length </span>
        </td>
        <td class="cell-summary">
           flow.steps.map(s => s.task).join(' → ') 
        </td>
        <td class="cell-center">
          <button class="ghost-button btn-sm" @click="openEditModal(flow)">编辑</button>
          <button class="danger-button btn-sm" @click="askDelete(flow)">删除</button>
        </td>
      </tr>
    </tbody>
  </table>

删除 <style> 中 .flow-grid、.flow-card、.flow-card-header、.step-count、
.step-list-preview、.step-preview-main、.step-task、.step-policy、
.step-feature、.flow-actions 相关样式。

新增样式：
  .flow-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  .flow-table th {
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid #e2e8f0;
    color: #475569;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    white-space: nowrap;
  }
  .flow-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
    vertical-align: middle;
  }
  .flow-table tbody tr:hover {
    background: #f8fafc;
  }
  .cell-center {
    text-align: center;
  }
  .cell-desc {
    color: #94a3b8;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .cell-summary {
    color: #64748b;
    font-size: 13px;
  }
  .flow-name-link {
    color: #1d4ed8;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
  }
  .flow-name-link:hover {
    text-decoration: underline;
  }
  .step-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    background: rgba(59,130,246,0.12);
    color: #1d4ed8;
    font-size: 12px;
    font-weight: 700;
  }
  .btn-sm {
    padding: 6px 12px;
    font-size: 13px;
  }

验收：
- 页面顶部统计栏变成一行文字
- 模板列表是表格行，每行高度约 44px
- 10 个流程可在一屏内显示
- 点击流程名称可打开编辑弹窗
- 编辑/删除按钮功能正常