<script setup lang="ts">
import { onMounted, ref } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import Modal from '../components/Modal.vue'
import StatusBadge from '../components/StatusBadge.vue'
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
const inputClass =
  'w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'

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
  <div class="space-y-6">
    <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <div class="space-y-1">
        <h1 class="text-2xl font-semibold text-gray-900">店铺管理</h1>
        <p class="text-sm text-brand-500">管理店铺账号、代理与邮箱连接配置。</p>
      </div>

      <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="button"
          class="rounded-md bg-brand-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
          @click="openAddModal"
        >
          新增店铺
        </button>
      </div>
    </div>

    <div v-if="shops.length === 0" class="rounded-md border border-brand-300/50 bg-white px-6 py-14 text-center shadow-sm">
      <p class="text-sm text-brand-500">暂无店铺数据。</p>
    </div>

    <div v-else class="overflow-x-auto rounded-md border border-brand-300/50 bg-white shadow-sm">
      <table class="w-full min-w-[900px] table-fixed divide-y divide-brand-300/30">
        <thead class="bg-brand-700/10">
          <tr class="text-xs font-medium uppercase tracking-wider text-brand-700">
            <th class="w-16 px-4 py-3 text-center">状态</th>
            <th class="w-44 px-4 py-3 text-center">店铺名称</th>
            <th class="w-28 px-4 py-3 text-center">账号</th>
            <th class="w-36 px-4 py-3 text-center">邮箱</th>
            <th class="w-24 px-4 py-3 text-center">协议</th>
            <th class="w-36 px-4 py-3 text-center">代理</th>
            <th class="w-36 px-4 py-3 text-center">最近登录</th>
            <th class="w-36 px-4 py-3 text-center">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-brand-300/20 text-sm text-gray-900">
          <tr
            v-for="shop in shops"
            :key="shop.id"
            class="transition hover:bg-brand-100/50"
          >
            <td class="px-4 py-3 text-center">
              <StatusBadge :status="shop.status" type="shop" />
            </td>
            <td class="px-4 py-3 text-center">
              <p class="truncate text-sm font-medium text-gray-900">{{ shop.name }}</p>
              <p class="truncate font-mono text-[11px] text-brand-500">{{ shop.id }}</p>
            </td>
            <td class="truncate px-4 py-3 text-center font-mono text-xs text-brand-500">
              {{ shop.username || '-' }}
            </td>
            <td class="truncate px-4 py-3 text-center text-xs">
              {{ shop.smtp_user || '未配置' }}
            </td>
            <td class="px-4 py-3 text-center font-mono text-xs uppercase text-brand-500">
              {{ shop.smtp_protocol || '-' }}
            </td>
            <td class="truncate px-4 py-3 text-center text-xs text-brand-500">
              {{ shop.proxy || '无代理' }}
            </td>
            <td class="px-4 py-3 text-center font-mono text-xs text-brand-500">
              {{ shop.last_login ? new Date(shop.last_login).toLocaleString('zh-CN') : '暂无记录' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-center">
              <div class="inline-flex gap-3">
                <button
                  type="button"
                  class="text-xs font-medium text-brand-500 transition hover:text-brand-900"
                  @click="handleOpenBrowser(shop.id)"
                >打开</button>
                <button
                  type="button"
                  class="text-xs font-medium text-brand-500 transition hover:text-brand-900"
                  @click="openEditModal(shop)"
                >编辑</button>
                <button
                  type="button"
                  class="text-xs font-medium text-brand-500 transition hover:text-brand-900"
                  @click="handleCheckStatus(shop.id)"
                >检查</button>
                <button
                  type="button"
                  class="text-xs font-medium text-rose-500 transition hover:text-rose-700"
                  @click="openDeleteConfirm(shop.id)"
                >删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :show="showModal" :title="editingShop ? '编辑店铺' : '新增店铺'" width="720px" @close="showModal = false">
      <form class="space-y-6" @submit.prevent="handleSave">
        <section class="space-y-4">
          <div class="space-y-1">
            <h2 class="text-sm font-medium text-gray-900">基本信息</h2>
            <p class="text-xs text-brand-500">维护店铺名称、账号和代理配置。</p>
          </div>

          <div class="grid gap-4 md:grid-cols-1">
            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">店铺名称</label>
              <input v-model="formData.name" :class="inputClass" type="text" required />
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">账号</label>
              <input v-model="formData.username" :class="inputClass" type="text" />
            </div>

            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">密码</label>
              <input
                v-model="formData.password"
                :class="inputClass"
                type="password"
                :placeholder="editingShop ? '••••••••（留空则不修改）' : '••••••••'"
              />
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">代理</label>
            <input v-model="formData.proxy" :class="inputClass" type="text" placeholder="127.0.0.1:7890" />
          </div>
        </section>

        <section class="space-y-4 border-t border-brand-300/30 pt-6">
          <div class="space-y-1">
            <h2 class="text-sm font-medium text-gray-900">邮箱配置</h2>
            <p class="text-xs text-brand-500">保存收件协议、服务器和授权信息。</p>
          </div>

          <div class="grid gap-4 md:grid-cols-3">
            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">协议</label>
              <select v-model="formData.smtp_protocol" :class="inputClass">
                <option value="imap">IMAP</option>
                <option value="smtp">SMTP</option>
              </select>
            </div>

            <div class="space-y-2 md:col-span-2">
              <label class="text-xs font-medium text-brand-700">服务器</label>
              <input v-model="formData.smtp_host" :class="inputClass" type="text" placeholder="imap.qq.com" />
            </div>

            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">端口</label>
              <input v-model.number="formData.smtp_port" :class="inputClass" type="number" />
            </div>

            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">邮箱账号</label>
              <input v-model="formData.smtp_user" :class="inputClass" type="email" />
            </div>

            <div class="space-y-2">
              <label class="text-xs font-medium text-brand-700">授权码</label>
              <input
                v-model="formData.smtp_pass"
                :class="inputClass"
                type="password"
                :placeholder="editingShop ? '••••••••（留空则不修改）' : '••••••••'"
              />
            </div>
          </div>

          <div>
            <button
              type="button"
              class="rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900"
              @click="testEmail"
            >
              测试连接
            </button>
          </div>
        </section>
      </form>

      <template #footer>
        <button
          type="button"
          class="rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900"
          @click="showModal = false"
        >
          取消
        </button>
        <button
          type="button"
          class="rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-gray-400"
          :disabled="isSaving"
          @click="handleSave"
        >
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
      </template>
    </Modal>

    <ConfirmDialog
      :show="showDeleteConfirm"
      title="删除店铺"
      message="确定要删除这个店铺吗？此操作不可恢复。"
      type="danger"
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>
