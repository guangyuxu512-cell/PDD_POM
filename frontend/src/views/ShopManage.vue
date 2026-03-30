<script setup lang="ts">
import { onMounted, ref } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import Modal from '../components/Modal.vue'
import ShopCard from '../components/ShopCard.vue'
import {
  checkShopStatus,
  createShop,
  deleteShop,
  listShops,
  openShopBrowser,
  testShopEmailConnection,
  updateShop,
} from '../api/shops'
import type { Shop, ShopPayload } from '../api/types'
import { toast } from '../utils/toast'

interface ShopFormModel {
  name: string
  username: string
  password: string
  proxy: string
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_pass: string
  smtp_protocol: string
}

const shops = ref<Shop[]>([])
const showModal = ref(false)
const showDeleteConfirm = ref(false)
const isSaving = ref(false)
const editingShop = ref<Shop | null>(null)
const deletingShopId = ref<string | null>(null)

const formData = ref<ShopFormModel>({
  name: '',
  username: '',
  password: '',
  proxy: '',
  smtp_host: '',
  smtp_port: 993,
  smtp_user: '',
  smtp_pass: '',
  smtp_protocol: 'imap',
})

function createEmptyForm(): ShopFormModel {
  return {
    name: '',
    username: '',
    password: '',
    proxy: '',
    smtp_host: '',
    smtp_port: 993,
    smtp_user: '',
    smtp_pass: '',
    smtp_protocol: 'imap',
  }
}

async function loadShops() {
  try {
    const result = await listShops()
    shops.value = result.list
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载店铺失败'
    toast.error(message)
  }
}

function openAddModal() {
  editingShop.value = null
  formData.value = createEmptyForm()
  showModal.value = true
}

function openEditModal(shop: Shop) {
  editingShop.value = shop
  formData.value = {
    name: shop.name ?? '',
    username: shop.username ?? '',
    password: '',
    proxy: shop.proxy ?? '',
    smtp_host: shop.smtp_host ?? '',
    smtp_port: shop.smtp_port ?? 993,
    smtp_user: shop.smtp_user ?? '',
    smtp_pass: '',
    smtp_protocol: shop.smtp_protocol ?? 'imap',
  }
  showModal.value = true
}

function buildPayload(): ShopPayload {
  const payload: ShopPayload = {
    name: formData.value.name.trim(),
  }

  if (formData.value.username.trim()) {
    payload.username = formData.value.username.trim()
  }

  if (formData.value.proxy.trim()) {
    payload.proxy = formData.value.proxy.trim()
  }

  if (formData.value.password.trim()) {
    payload.password = formData.value.password.trim()
  }

  if (formData.value.smtp_host.trim()) {
    payload.smtp_host = formData.value.smtp_host.trim()
  }

  if (formData.value.smtp_port) {
    payload.smtp_port = formData.value.smtp_port
  }

  if (formData.value.smtp_user.trim()) {
    payload.smtp_user = formData.value.smtp_user.trim()
  }

  if (formData.value.smtp_pass.trim()) {
    payload.smtp_pass = formData.value.smtp_pass.trim()
  }

  if (formData.value.smtp_protocol.trim()) {
    payload.smtp_protocol = formData.value.smtp_protocol.trim()
  }

  return payload
}

async function handleSave() {
  if (!formData.value.name.trim()) {
    toast.warning('请输入店铺名称')
    return
  }

  isSaving.value = true

  try {
    const payload = buildPayload()

    if (editingShop.value) {
      await updateShop(editingShop.value.id, payload)
      toast.success('店铺已更新')
    } else {
      await createShop(payload)
      toast.success('店铺已创建')
    }

    showModal.value = false
    await loadShops()
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存店铺失败'
    toast.error(message)
  } finally {
    isSaving.value = false
  }
}

function openDeleteConfirm(shopId: string) {
  deletingShopId.value = shopId
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!deletingShopId.value) {
    return
  }

  try {
    await deleteShop(deletingShopId.value)
    toast.success('店铺已删除')
    showDeleteConfirm.value = false
    deletingShopId.value = null
    await loadShops()
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除店铺失败'
    toast.error(message)
  }
}

async function handleOpenBrowser(shopId: string) {
  try {
    await openShopBrowser(shopId)
    toast.success('登录任务已启动')
    await loadShops()
  } catch (error) {
    const message = error instanceof Error ? error.message : '打开浏览器失败'
    toast.error(message)
  }
}

async function handleCheckStatus(shopId: string) {
  try {
    await checkShopStatus(shopId)
    toast.success('状态检查完成')
    await loadShops()
  } catch (error) {
    const message = error instanceof Error ? error.message : '检查状态失败'
    toast.error(message)
  }
}

async function testEmail() {
  if (!editingShop.value) {
    toast.warning('请先保存店铺后再测试连接')
    return
  }

  try {
    await testShopEmailConnection(editingShop.value.id)
    toast.success('邮箱连接成功')
  } catch (error) {
    const message = error instanceof Error ? error.message : '邮箱连接失败'
    toast.error(message)
  }
}

onMounted(() => {
  void loadShops()
})
</script>

<template>
  <div class="shop-manage">
    <div class="header">
      <h1>店铺管理</h1>
      <button class="btn btn-primary" @click="openAddModal">新增店铺</button>
    </div>

    <div v-if="shops.length === 0" class="empty-state">
      <p>暂无数据</p>
    </div>
    <div v-else class="shops-grid">
      <ShopCard
        v-for="shop in shops"
        :key="shop.id"
        :shop="shop"
        @open-browser="handleOpenBrowser"
        @edit="openEditModal"
        @check-status="handleCheckStatus"
        @delete="openDeleteConfirm"
      />
    </div>

    <Modal :show="showModal" :title="editingShop ? '编辑店铺' : '添加店铺'" width="700px" @close="showModal = false">
      <form class="shop-form" @submit.prevent="handleSave">
        <div class="form-section">
          <h4>基本信息</h4>
          <div class="form-row">
            <div class="form-group">
              <label>店铺名称</label>
              <input v-model="formData.name" type="text" required />
            </div>
            <div class="form-group">
              <label>账号</label>
              <input v-model="formData.username" type="text" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>密码</label>
              <input
                v-model="formData.password"
                type="password"
                :placeholder="editingShop ? '留空则不修改' : ''"
              />
            </div>
            <div class="form-group">
              <label>代理</label>
              <input v-model="formData.proxy" type="text" placeholder="127.0.0.1:7890" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h4>邮箱配置</h4>
          <div class="form-row">
            <div class="form-group">
              <label>协议</label>
              <select v-model="formData.smtp_protocol">
                <option value="imap">IMAP</option>
                <option value="smtp">SMTP</option>
              </select>
            </div>
            <div class="form-group">
              <label>服务器</label>
              <input v-model="formData.smtp_host" type="text" placeholder="imap.qq.com" />
            </div>
            <div class="form-group">
              <label>端口</label>
              <input v-model.number="formData.smtp_port" type="number" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>邮箱账号</label>
              <input v-model="formData.smtp_user" type="email" />
            </div>
            <div class="form-group">
              <label>授权码</label>
              <input
                v-model="formData.smtp_pass"
                type="password"
                :placeholder="editingShop ? '留空则不修改' : ''"
              />
            </div>
          </div>
          <div class="test-connection-wrapper">
            <button type="button" class="btn btn-secondary" @click="testEmail">测试连接</button>
          </div>
        </div>
      </form>

      <template #footer>
        <button class="btn btn-secondary" @click="showModal = false">取消</button>
        <button class="btn btn-primary" :disabled="isSaving" @click="handleSave">
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
      </template>
    </Modal>

    <ConfirmDialog
      :show="showDeleteConfirm"
      title="确认删除"
      message="确定要删除这个店铺吗？此操作不可恢复。"
      type="danger"
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>

<style scoped>
.shop-manage {
  color: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h1 {
  font-size: 28px;
  margin: 0;
  color: #1a1a2e;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #0f3460;
  color: #e0e0e0;
}

.btn-secondary:hover {
  background: #1a4d7a;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: #a0a0a0;
  background: #16213e;
  border-radius: 12px;
  border: 1px solid #0f3460;
}

.shops-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

@media (min-width: 1600px) {
  .shops-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 1400px) {
  .shops-grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }
}

@media (max-width: 768px) {
  .shops-grid {
    grid-template-columns: 1fr;
  }
}

.shop-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #e0e0e0;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: #a0a0a0;
}

.form-group input,
.form-group select {
  padding: 10px;
  background: #0f3460;
  border: 1px solid #1a4d7a;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
}

.test-connection-wrapper {
  margin-top: 8px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }
}
</style>
