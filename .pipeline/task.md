Codex 任务 1：注册抖音和淘宝平台
任务目标： 新增抖音和淘宝两个平台注册，让前端下拉框能切换三个平台。
需要新增的文件：
platforms/douyin/__init__.py
platforms/douyin/platform.py
platforms/taobao/__init__.py
platforms/taobao/platform.py
需要修改的文件：
platforms/__init__.py
具体实现：
platforms/douyin/__init__.py：
"""抖音平台包。"""
import platforms.douyin.platform  # noqa: F401
​
platforms/douyin/platform.py：
"""抖音平台定义。"""
from __future__ import annotations
from platforms.base.base_platform import BasePlatform, register_platform

@register_platform("douyin")
class DouyinPlatform(BasePlatform):
    """抖音电商平台。"""

    @property
    def platform_id(self) -> str:
        return "douyin"

    @property
    def display_name(self) -> str:
        return "抖音"

    @property
    def icon(self) -> str:
        return "🎵"

    @property
    def login_url(self) -> str:
        return "https://fxg.jinritemai.com/login/common"

    def get_available_tasks(self) -> list[str]:
        return []  # 暂无任务，后续扩展
​
platforms/taobao/__init__.py：
"""淘宝平台包。"""
import platforms.taobao.platform  # noqa: F401
​
platforms/taobao/platform.py：
"""淘宝平台定义。"""
from __future__ import annotations
from platforms.base.base_platform import BasePlatform, register_platform

@register_platform("taobao")
class TaoBaoPlatform(BasePlatform):
    """淘宝电商平台。"""

    @property
    def platform_id(self) -> str:
        return "taobao"

    @property
    def display_name(self) -> str:
        return "淘宝"

    @property
    def icon(self) -> str:
        return "🟧"

    @property
    def login_url(self) -> str:
        return "https://myseller.taobao.com/"

    def get_available_tasks(self) -> list[str]:
        return []  # 暂无任务，后续扩展
​
修改 platforms/__init__.py：
import platforms.pdd     # noqa: F401
import platforms.douyin   # noqa: F401
import platforms.taobao   # noqa: F401
​
验收方式：
启动后端，GET /api/platforms 返回 3 个平台：拼多多、抖音、淘宝
前端顶部平台切换下拉框出现 3 个选项
切换平台后店铺列表自动按平台过滤
Codex 任务 2：新增店铺弹窗加平台选择 + 修复弹窗底色
任务目标：
新增店铺弹窗的"基本信息"区域顶部增加"所属平台"下拉选择框
修改弹窗整体底色，从深蓝色改为深灰/暗色（不要蓝色调）
需要修改的文件：
frontend/src/views/ShopManage.vue
frontend/src/components/Modal.vue（弹窗底色）
具体实现：
2a. ShopManage.vue — 加平台选择
在 <script setup> 中新增：
const formPlatform = ref(platformStore.currentPlatform)
​
修改 openAddModal()：
function openAddModal() {
  editingShop.value = null
  formData.value = createEmptyForm()
  formPlatform.value = platformStore.currentPlatform  // ← 新增
  showModal.value = true
}
​
修改 openEditModal()：
function openEditModal(shop: Shop) {
  editingShop.value = shop
  formPlatform.value = shop.platform || 'pdd'  // ← 新增
  formData.value = { ... }  // 原有逻辑不变
  showModal.value = true
}
​
修改 handleSave() 中新建分支：
// 把原来的：
payload.platform = platformStore.currentPlatform
// 改为：
payload.platform = formPlatform.value
​
在 template 的"基本信息" <h4> 后面、店铺名称行前面，加一行：
<div class="form-row">
  <div class="form-group">
    <label>所属平台</label>
    <select v-model="formPlatform" :disabled="!!editingShop">
      <option
        v-for="p in platformStore.platforms"
        :key="p.id"
        :value="p.id"
      >
         p.icon   p.name 
      </option>
    </select>
  </div>
</div>
​
编辑模式下 disabled，不允许更改已有店铺的平台。
2b. Modal.vue — 修复弹窗底色
找到弹窗 .modal-content（或类似的弹窗容器样式），将蓝色系背景色改为深灰色系：
/* 原来（蓝色系）：*/
background: #16213e;   /* 或 #0a1929 之类的蓝色 */
border: 1px solid #0f3460;

/* 改为（深灰色系）：*/
background: #1e1e2e;
border: 1px solid #2e2e3e;
​
同时修改弹窗内所有蓝色调的输入框背景和边框：
/* ShopManage.vue scoped styles 里的 form 输入框 */
/* 原来：*/
.form-group input,
.form-group select {
  background: #0f3460;
  border: 1px solid #1a4d7a;
}
.form-group input:focus,
.form-group select:focus {
  border-color: #3b82f6;
}

/* 改为：*/
.form-group input,
.form-group select {
  background: #2a2a3a;
  border: 1px solid #3a3a4a;
}
.form-group input:focus,
.form-group select:focus {
  border-color: #6366f1;  /* 紫色聚焦，区别于蓝色 */
}
​
section 标题颜色也一起改：
.form-section h4 {
  color: #d0d0d0;  /* 原来 #e0e0e0 也行，主要是不要蓝色调 */
}
​
也检查 Modal.vue 里的遮罩层、header、footer 背景色，所有 #16213e / #0f3460 / #1a4d7a 类的蓝色调统一替换为灰色调：
#16213e → #1e1e2e
#0f3460 → #2a2a3a
#1a4d7a → #3a3a4a
验收方式：
新增店铺弹窗第一行显示"所属平台"下拉框，默认跟随全局切换器
编辑店铺时，平台下拉框禁用（灰色不可点）
弹窗整体底色为深灰，没有明显的蓝色调
输入框背景为深灰，不是深蓝
Codex 任务 3：所有密码输入框加 * 占位符
任务目标： 弹窗里所有密码类型的输入框（密码、授权码），在新增模式下显示 ******** 占位提示，编辑模式下显示"留空则不修改"。
需要修改的文件：
frontend/src/views/ShopManage.vue
具体实现：
找到以下两个密码输入框，修改 placeholder：
店铺密码输入框：
<!-- 原来：-->
<input
  v-model="formData.password"
  type="password"
  :placeholder="editingShop ? '留空则不修改' : ''"
/>

<!-- 改为：-->
<input
  v-model="formData.password"
  type="password"
  :placeholder="editingShop ? '••••••••（留空则不修改）' : '••••••••'"
/>
​
邮箱授权码输入框：
<!-- 原来：-->
<input
  v-model="formData.smtp_pass"
  type="password"
  :placeholder="editingShop ? '留空则不修改' : ''"
/>

<!-- 改为：-->
<input
  v-model="formData.smtp_pass"
  type="password"
  :placeholder="editingShop ? '••••••••（留空则不修改）' : '••••••••'"
/>
​
注意： 使用 ••••••••（Unicode 项目符号 \u2022），不要用普通的 *，这样视觉上更像真实密码遮罩。
验收方式：
新增店铺模式：密码和授权码输入框显示 •••••••• 灰色占位符
编辑店铺模式：密码和授权码输入框显示 ••••••••（留空则不修改）
输入内容后占位符消失，输入的文字显示为密码圆点