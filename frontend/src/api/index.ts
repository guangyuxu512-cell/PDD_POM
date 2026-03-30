// ---------- 统一响应类型 ----------
interface ApiResponse<T = any> {
  code: number
  data: T
  msg: string
}

// ---------- 统一请求函数 ----------
async function request<T = any>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers ?? {})
  const body = options.body

  if (!(body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(url, {
    ...options,
    headers,
  })

  const json: ApiResponse<T> = await res.json()

  if (json.code === 0) {
    return json.data
  }

  // 业务错误，抛出让调用方处理
  throw new Error(json.msg || '请求失败')
}

// ---------- 封装四种请求方法 ----------
export const api = {
  get: <T = any>(url: string) =>
    request<T>(url),

  post: <T = any>(url: string, body?: any) =>
    request<T>(url, {
      method: 'POST',
      body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
    }),

  put: <T = any>(url: string, body?: any) =>
    request<T>(url, {
      method: 'PUT',
      body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
    }),

  del: <T = any>(url: string) =>
    request<T>(url, { method: 'DELETE' }),

  postForm: <T = any>(url: string, body: FormData) =>
    request<T>(url, {
      method: 'POST',
      body,
    }),
}

// ---------- 兼容旧的导出方式 ----------
export const get = api.get
export const post = api.post
export const put = api.put
export const del = api.del
export const postForm = api.postForm
