# LLM Gateway

一个极简的、可自托管的 LLM 代理网关，提供 OpenAI 兼容 API。作为 LiteLLM 在 [2026 年 3 月供应链攻击事件](https://github.com/BerriAI/litellm/issues/9354)（v1.82.7–v1.82.8）后的可审计替代方案而构建。

**设计目标：** 代码量足够小，半天即可通读（约 2500 行应用代码）；导入时无隐藏网络调用；构建时不执行代码；零外部服务依赖。

---

## 功能特性

| 能力 | 说明 |
|---|---|
| **统一 API** | 单一 `/v1/chat/completions` 端点，兼容 OpenAI 格式 |
| **多供应商** | 支持 OpenAI、Anthropic、Ollama（及任何 OpenAI 兼容端点） |
| **流式传输** | 上游始终流式请求；客户端可选流式或缓冲响应 |
| **虚拟密钥** | 签发带作用域的 `sk-` API 密钥，可选按模型白名单限制 |
| **故障转移** | 按优先级排序的供应商列表；自动跳过冷却中的模型 |
| **健康追踪** | 被动式：连续 3 次失败 → 30 秒冷却期，无主动探测 |
| **请求日志** | SQLite 存储：时间戳、模型、token 数、延迟、状态 |
| **管理面板** | Next.js 15 界面 — 统计、密钥管理、日志浏览、模型健康状态 |

**刻意不包含的功能：** 负载均衡、费用追踪、缓存、图片生成、函数调用、多租户。

---

## 快速开始

### Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/fuguimashu/llm-gateway.git
cd llm-gateway

# 2. 创建配置文件
cp backend/config.yaml.example config.yaml
# 编辑 config.yaml — 添加你的 API 密钥和模型

# 3. 创建环境变量文件
cp .env.example .env
# 编辑 .env — 将 MASTER_KEY 设置为一个强密钥

# 4. 创建数据目录
mkdir -p data

# 5. 启动
docker compose up -d

# 后端：http://localhost:8000
# 前端：http://localhost:3000
```

打开 `http://localhost:3000`，输入你的 `MASTER_KEY`，即可开始使用。

### 本地开发

**后端**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 复制并编辑配置
cp config.yaml.example config.yaml

# 启动
MASTER_KEY=dev uvicorn app.main:app --reload
```

**前端**

```bash
cd frontend
cp .env.local.example .env.local
# 如果后端不在 http://localhost:8000，请编辑 .env.local

pnpm install   # 或 npm install
pnpm dev
```

---

## 配置

所有配置集中在 `config.yaml` 中。环境变量会覆盖 `settings` 中的对应值。

```yaml
models:
  - id: "openai/gpt-4o"        # 客户端使用的标识符
    provider: "openai"          # openai | anthropic | ollama
    model_name: "gpt-4o"        # 发送给供应商的实际模型名
    api_key: "sk-..."
    priority: 0                 # 数值越小优先级越高（用于故障转移）

  - id: "anthropic/claude-sonnet-4-6"
    provider: "anthropic"
    model_name: "claude-sonnet-4-6"
    api_key: "sk-ant-..."
    priority: 0

  - id: "ollama/llama3.2"
    provider: "ollama"
    model_name: "llama3.2"
    base_url: "http://localhost:11434"
    priority: 2

settings:
  master_key: "your-master-key"
  database_url: "sqlite:///./data/llm_gateway.db"
  health_fail_threshold: 3      # 触发冷却的连续失败次数
  health_cooldown_seconds: 30   # 冷却等待时间（秒）
  request_timeout: 120          # 上游请求超时时间（秒）
```

### 环境变量覆盖

| 变量 | 覆盖的配置项 |
|---|---|
| `MASTER_KEY` | `settings.master_key` |
| `DATABASE_URL` | `settings.database_url` |
| `CONFIG_PATH` | config.yaml 的路径（默认：`config.yaml`） |
| `NEXT_PUBLIC_API_URL` | 浏览器端看到的后端 URL |

---

## API 参考

所有端点接受 `Authorization: Bearer <key>`，其中 `<key>` 为主密钥或虚拟密钥。

### 对话补全

```
POST /v1/chat/completions
```

兼容 OpenAI 格式。`model` 字段必须匹配已配置的模型 `id`。

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

流式请求：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-4o", "messages": [{"role": "user", "content": "你好"}], "stream": true}'
```

### 模型列表

```
GET /v1/models
```

列出所有活跃模型及其健康状态，采用 OpenAI 兼容格式。

### 虚拟密钥

所有密钥管理端点需要主密钥。

```bash
# 列出密钥
GET /v1/keys

# 创建密钥（可访问所有模型）
POST /v1/keys
{"name": "我的应用"}

# 创建密钥（限制可访问的模型）
POST /v1/keys
{"name": "受限应用", "models": "openai/gpt-4o,openai/gpt-4o-mini"}

# 停用密钥
DELETE /v1/keys/{key_id}

# 重新激活密钥
POST /v1/keys/{key_id}/activate
```

### 日志

```bash
# 所有日志（分页）
GET /v1/logs?page=1&page_size=50

# 筛选
GET /v1/logs?model=openai/gpt-4o&status=error

# 健康检查
GET /health
```

---

## 与 OpenAI SDK 集成

将 SDK 指向你的网关即可，无需其他改动：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-your-virtual-key",
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "你好"}],
)
```

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:8000/v1",
  apiKey: "sk-your-virtual-key",
});
```

---

## 故障转移与健康检查

网关**被动地**追踪模型健康状态 — 仅基于实际请求结果，从不主动探测供应商。

```
请求到达
  └─ 查找匹配请求模型的候选项（按 id）
       └─ 按优先级排序（升序）
            └─ 跳过冷却中的模型
                 └─ 尝试第一个可用的
                      ├─ 成功 → 重置失败计数，返回响应
                      └─ 失败（连接/超时/5xx）→ 增加失败计数
                           ├─ 计数 < 阈值 → 尝试下一个候选
                           └─ 计数 >= 阈值 → 进入冷却期（30秒），尝试下一个
```

冷却期结束后，模型自动恢复可用。单次成功即可重置失败计数。

---

## 架构

```
客户端
  │  Bearer sk-xxx
  ▼
FastAPI  (/v1/chat/completions)
  │
  ├─ auth.py          ← 验证虚拟密钥，检查模型白名单
  ├─ proxy_service.py ← 选择供应商，故障转移循环
  │    ├─ health_checker.py  ← 内存中的失败追踪
  │    └─ logger.py          ← 异步 SQLite 写入
  │
  └─ providers/
       ├─ openai.py      ← OpenAI / Ollama / 兼容端点
       └─ anthropic.py   ← 格式转换（OpenAI ↔ Anthropic SSE）
```

**关键设计决策：**

- 上游请求**始终采用流式传输**（`httpx` 异步字节迭代），即使客户端请求非流式响应也是如此。这避免了在内存中缓冲大型响应。
- 健康检查器**纯内存实现** — 重启后重置。这是有意为之：新的启动应该给所有模型一个干净的初始状态。
- API 密钥以原文存储在 SQLite 中。生产环境中若涉及敏感密钥，建议加密数据库或通过环境变量注入密钥而非写在 config.yaml 中。

---

## 安全说明

- **主密钥**：使用长随机字符串（`openssl rand -hex 32`），它拥有全部控制权限。
- **虚拟密钥**：为每个客户端应用签发独立密钥，可单独吊销而不影响其他应用。
- **config.yaml**：包含供应商 API 密钥 — 不要纳入版本控制（已在下方 `.gitignore` 模板中）。
- **SQLite 文件**：包含请求日志和密钥元数据 — 生产环境中应限制文件权限。
- **CORS**：默认为 `*`（本地使用）。生产环境中请在 `.env` 中设置 `CORS_ORIGINS`。
- **网络暴露**：生产环境中应运行在反向代理（nginx/Caddy）之后并启用 TLS。

建议添加到 `.gitignore`：

```
.env
config.yaml
data/
*.db
```

---

## 项目结构

```
llm-gateway/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # YAML + 环境变量配置加载
│   │   ├── database.py          # SQLAlchemy + SQLite
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── routes/              # API 路由处理器
│   │   ├── services/            # 业务逻辑（认证、代理、健康检查、日志）
│   │   └── providers/           # LLM 供应商适配器
│   ├── requirements.txt
│   ├── Dockerfile
│   └── config.yaml.example
├── frontend/
│   ├── app/                     # Next.js 15 App Router 页面
│   ├── components/              # React 组件
│   ├── lib/                     # API 客户端 + 工具函数
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 依赖审计

后端仅有 8 个直接依赖 — 均为成熟的开源库，无遥测、无自动更新行为：

| 包名 | 版本 | 用途 |
|---|---|---|
| fastapi | 0.115.6 | HTTP 框架 |
| uvicorn | 0.32.1 | ASGI 服务器 |
| sqlalchemy | 2.0.36 | ORM + SQLite |
| httpx | 0.27.2 | 异步 HTTP 客户端 |
| pydantic | 2.10.3 | 数据验证 |
| pydantic-settings | 2.6.1 | 配置管理 |
| python-dotenv | 1.0.1 | .env 文件加载 |
| pyyaml | 6.0.2 | YAML 配置解析 |

审计已知漏洞：

```bash
pip install pip-audit
pip-audit -r backend/requirements.txt
```

---

## 许可证

MIT
