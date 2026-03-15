Task 43.1：设置页新增飞书配置区块
一、做什么
在 frontend/src/views/Settings.vue 的"验证码服务"区块后面，新增一个"飞书配置"区块，包含 5 个输入框 + 1 个测试按钮。
二、涉及文件
frontend/src/views/Settings.vue — 修改
三、修改内容
3.1 SystemConfig 接口新增字段
interface SystemConfig {
  // ... 现有字段保持不变 ...
  feishu_webhook_url?: string
  feishu_app_id?: string
  feishu_app_secret?: string
  feishu_bitable_app_token?: string
  feishu_bitable_table_id?: string
}
​
3.2 config ref 默认值新增
const config = ref<SystemConfig>({
  // ... 现有字段保持不变 ...
  feishu_webhook_url: '',
  feishu_app_id: '',
  feishu_app_secret: '',
  feishu_bitable_app_token: '',
  feishu_bitable_table_id: '',
})
​
3.3 loadConfig 新增映射
在 loadConfig 的赋值对象中追加：
feishu_webhook_url: data.feishu_webhook_url || '',
feishu_app_id: data.feishu_app_id || '',
feishu_app_secret: data.feishu_app_secret || '',
feishu_bitable_app_token: data.feishu_bitable_app_token || '',
feishu_bitable_table_id: data.feishu_bitable_table_id || '',
​
3.4 新增 testFeishuWebhook 方法
const testingFeishu = ref(false)

const testFeishuWebhook = async () => {
  testingFeishu.value = true
  try {
    await post('/api/feishu/test-webhook', {
      webhook_url: config.value.feishu_webhook_url
    })
    toast.success('飞书 Webhook 测试成功')
  } catch (error: any) {
    toast.error(error?.message || '飞书 Webhook 测试失败')
  } finally {
    testingFeishu.value = false
  }
}
​
3.5 template 中新增飞书区块
在"验证码服务" </div> 和"系统监控" <div> 之间，插入：
<div class="form-section">
  <h3>飞书配置</h3>
  <div class="form-group">
    <label>Webhook 地址</label>
    <input v-model="config.feishu_webhook_url" type="text" 
           placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
    <button type="button" class="btn-test" :disabled="testingFeishu" @click="testFeishuWebhook">
       testingFeishu ? '测试中...' : '测试 Webhook' 
    </button>
    <span class="hint">飞书群机器人的 Webhook 地址，用于发送通知</span>
  </div>

  <div class="form-group">
    <label>App ID</label>
    <input v-model="config.feishu_app_id" type="text" 
           placeholder="cli_xxxxxxxxx（多维表格回写用，不需要可留空）" />
  </div>

  <div class="form-group">
    <label>App Secret</label>
    <input v-model="config.feishu_app_secret" type="password" 
           placeholder="飞书应用密钥（不需要可留空）" />
  </div>

  <div class="form-group">
    <label>多维表格 App Token</label>
    <input v-model="config.feishu_bitable_app_token" type="text" 
           placeholder="bascnxxxxxxxxx（不需要可留空）" />
  </div>

  <div class="form-group">
    <label>多维表格 Table ID</label>
    <input v-model="config.feishu_bitable_table_id" type="text" 
           placeholder="tblxxxxxxxxx（不需要可留空）" />
  </div>
</div>
​
四、约束
只改 Settings.vue 一个文件
现有配置项不动，只追加飞书区块
保存按钮是统一的，点一次保存所有配置（已有逻辑不需要改）
飞书 5 个字段都是可选的，不加 required
App Secret 用 type="password" 遮掩显示
保持现有 CSS 风格，不需要新增样式