```
## 任务：重命名中文文件名为英文 + 移除嵌入式 Python 方案，恢复 PyInstaller 打包

### 背景
1. 项目中大量 Python 文件使用中文命名，导致 PyInstaller 打包乱码崩溃
2. 为解决此问题曾引入「嵌入式 Python + 源码」方案（scripts/prepare_dist.py + dist_bundle/），
   但该方案导致打包体积超过 1GB，且仍有任务扫描失效问题，需要移除
3. 正确方案：将中文文件名改为英文 → PyInstaller 打包恢复正常工作

---

## Part 1：移除嵌入式 Python 方案

### 1.1 删除相关文件
删除以下文件（如果存在）：
- `scripts/prepare_dist.py`
- `scripts/build_all.bat`
- `dist_bundle/`（整个目录）

### 1.2 恢复 electron/main.js
将 `electron/main.js` 中生产模式的启动逻辑改回使用 PyInstaller exe：

```

const packagedBackendExe = path.join(rootDir, 'python-backend', 'backend.exe')

const packagedCeleryExe = path.join(rootDir, 'python-backend', 'celery-worker.exe')

function ensurePackagedFileExists(filePath, label) {

if (!fs.existsSync(filePath)) {

throw new Error(`${label} 不存在: ${filePath}`)

}

}

```

startBackend() 生产模式：
```

ensurePackagedFileExists(packagedBackendExe, '后端程序')

backendProcess = spawn(packagedBackendExe, [], {

cwd: rootDir,

env: createProcessEnv(),

})

```

startCelery() 生产模式：
```

ensurePackagedFileExists(packagedCeleryExe, 'Celery Worker 程序')

celeryProcess = spawn(packagedCeleryExe, [], {

cwd: rootDir,

env: createProcessEnv(),

})

```

### 1.3 恢复 electron/package.json extraResources
将 `build.extraResources` 改回：
```

"extraResources": [

{

"from": "../frontend/dist",

"to": "app/frontend/dist"

},

{

"from": "../python-backend-dist",

"to": "app/python-backend"

},

{

"from": "../.env",

"to": "app/.env"

}

]

```

---

## Part 2：将所有中文文件名重命名为英文

### 2.1 扫描所有中文命名的 .py 文件
扫描 `backend/`、`tasks/`、`browser/`、`pages/`、`selectors/`、`scripts/` 目录下所有文件名包含中文字符的 .py 文件，列出完整列表。

### 2.2 重命名规则（使用 git mv）
按以下规则重命名，其余未列出的中文文件名按「功能描述的英文下划线命名」自行判断：

**tasks/ 目录：**
- `tasks/celery应用.py` → `tasks/celery_app.py`

**backend/ 目录：**
- `backend/启动入口.py` → `backend/main.py`
- `backend/api/路由注册.py` → `backend/api/router.py`
- `backend/api/流程接口.py` → `backend/api/flow_api.py`
- `backend/api/任务接口.py` → `backend/api/task_api.py`
- `backend/api/可用任务.py` → `backend/api/available_tasks.py`
- `backend/api/任务参数接口.py` → `backend/api/task_params_api.py`
- `backend/api/执行接口.py` → `backend/api/execute_api.py`
- `backend/services/执行服务.py` → `backend/services/execute_service.py`
- 其余中文命名文件同理

**browser/ 目录：**
- `browser/任务回调.py` → `browser/task_callback.py`
- 其余中文命名文件同理

所有重命名使用 `git mv` 保留历史：
```

git mv tasks/[celery应用.py](http://celery应用.py) tasks/celery_[app.py](http://app.py)

```

### 2.3 批量替换所有 import 引用
在所有 .py 文件中全局替换旧的中文模块路径为新的英文路径：
- `from tasks.celery应用 import` → `from tasks.celery_app import`
- `import tasks.celery应用` → `import tasks.celery_app`
- `from backend.启动入口 import` → `from backend.main import`
- 其余同理，与 2.2 的重命名对应

### 2.4 更新 electron/main.js 中的字符串引用
- `'backend.启动入口:app'` → `'backend.main:app'`
- `'tasks.celery应用'` → `'tasks.celery_app'`

### 2.5 更新 entry_backend.py 和 entry_celery.py
- `entry_backend.py`：`from backend.启动入口 import app` → `from backend.main import app`
- `entry_celery.py`：`from tasks.celery应用 import celery应用` → `from tasks.celery_app import celery_app`，并更新变量名引用

### 2.6 更新 .gitignore
确认以下条目存在（如不存在则添加）：
```

dist_bundle/

python-backend-dist/

electron/dist/

*.spec

build/

**pycache**/

*.pyc

```

---

## 验收标准

1. 项目中不再有中文命名的 .py 文件：
   `python -c "import os; files=[f for r,d,fs in os.walk('.') for f in fs if any('\u4e00'<=c<='\u9fff' for c in f) and f.endswith('.py')]; print(files)"` 输出 `[]`

2. 开发模式正常：
   `cd electron && npx electron .` 能启动，前端页面正常，任务注册数 > 0

3. 语法检查通过：
   `python -m py_compile backend/main.py tasks/celery_app.py browser/task_callback.py`

4. `dist_bundle/` 目录不存在，`scripts/prepare_dist.py` 不存在

5. `electron/main.js` 中没有任何中文字符串路径引用

---

## 注意事项
- 只改文件名和 import 路径，不改代码逻辑
- 中文注释、中文变量名、中文字符串内容暂时保留不动
- 使用 git mv 而不是普通 mv
- 有不确定的中文文件名，按英文功能描述命名，并在提交信息里列出完整重命名对照表
```