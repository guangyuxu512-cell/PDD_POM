export interface PaginatedList<T> {
  list: T[]
  total: number
  page?: number
  page_size?: number
}

export interface Shop {
  id: string
  name: string
  username?: string | null
  password?: string | null
  proxy?: string | null
  user_agent?: string | null
  profile_dir?: string | null
  cookie_path?: string | null
  status: string
  last_login?: string | null
  smtp_host?: string | null
  smtp_port?: number | null
  smtp_user?: string | null
  smtp_pass?: string | null
  smtp_protocol?: string | null
  remark?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface ShopPayload {
  name: string
  username?: string
  password?: string
  proxy?: string
  user_agent?: string
  smtp_host?: string
  smtp_port?: number
  smtp_user?: string
  smtp_pass?: string
  smtp_protocol?: string
  remark?: string
}

export interface AvailableTask {
  name: string
  description: string
}

export interface FlowStep {
  task: string
  on_fail: string
}

export interface Flow {
  id: string
  name: string
  steps: FlowStep[]
  description?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface FlowPayload {
  name: string
  steps: FlowStep[]
  description?: string
}

export interface BatchRequest {
  flow_id?: string
  task_name?: string
  shop_ids: string[]
  concurrency: number
}

export interface BatchResponse {
  batch_id: string
  total: number
  status: string
}

export interface BatchStepState {
  task: string
  on_fail: string
  status: string
  error?: string | null
  result?: string | null
}

export interface BatchShopState {
  shop_id: string
  shop_name?: string | null
  status: string
  current_task: string | null
  current_step: number
  total_steps: number
  last_error: string | null
  last_result: string | null
  task_ids: string[]
  steps: BatchStepState[]
}

export interface BatchSnapshot {
  batch_id: string
  mode: string
  flow_id?: string | null
  task_name?: string | null
  machine_id?: string
  queue_name?: string
  requested_concurrency: number
  total: number
  waiting: number
  running: number
  completed: number
  failed: number
  status: string
  stopped: boolean
  task_ids: string[]
  shops: Record<string, BatchShopState>
  created_at: string
  updated_at: string
}

export interface Schedule {
  id: string
  name: string
  flow_id: string
  shop_ids: string[]
  concurrency: number
  interval_seconds?: number | null
  cron_expr?: string | null
  overlap_policy: string
  enabled: boolean
  last_run_at?: string | null
  next_run_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface SchedulePayload {
  name: string
  flow_id: string
  shop_ids: string[]
  concurrency: number
  interval_seconds?: number | null
  cron_expr?: string | null
  overlap_policy: string
}
