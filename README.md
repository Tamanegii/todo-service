# Todo Service

手机发消息，自动创建 Todoist 待办事项。

通过 HTTP API 接收手机快捷指令发来的自然语言消息，用 LLM 解析后自动在 Todoist 创建任务。

## 功能

- 自然语言解析：发"明天下午3点 开会 重要 1小时"自动创建对应待办
- 多消息聚合：30 秒内连续发的多条消息会合并后一起解析
- 双端支持：iOS Shortcuts / Android HTTP Shortcuts 均可使用
- LLM 驱动：支持任意 OpenAI 兼容 API

## 消息格式

每次发送需包含以下信息（顺序随意，可分多条发送）：

| 字段 | 必填 | 示例 |
|------|------|------|
| 时间 | 是 | 明天下午3点、下周一上午10点、6月1号 |
| 事情 | 是 | 开会、买菜、交报告 |
| 重要性 | 是 | 重要、一般、紧急、不急 |
| 持续时间 | 否 | 1小时、30分钟、2h |

示例：
```
明天下午3点 开会 重要 1小时
```

或者分多条发：
```
第1条：明天下午三点
第2条：和客户开会
第3条：比较重要 大概一个小时
```

## 部署

### 环境要求

- Python 3.11+
- 或 Docker

### 1. 克隆项目

```bash
git clone https://github.com/Tamanegii/todo-service.git
cd todo-service
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 认证密钥（自己生成，手机端也要填同样的）
# 生成方法：python -c "import secrets; print(secrets.token_urlsafe(32))"
AUTH_TOKEN=你生成的随机字符串

# LLM 配置（OpenAI 兼容 API）
LLM_BASE_URL=https://你的LLM服务地址/v1
LLM_API_KEY=你的API密钥
LLM_MODEL=模型名称

# Todoist API Token
# 获取方式：todoist.com → 设置 → 集成 → 开发者 → API token
TODOIST_API_TOKEN=你的todoist_token

# 可选：指定任务创建到哪个项目，不填则进收件箱
TODOIST_PROJECT_ID=

# 多消息聚合窗口（秒）
AGGREGATION_WINDOW_SECONDS=30
```

### 3. 启动服务

**Docker 方式（推荐）：**

```bash
docker compose up -d
```

**直接运行：**

```bash
pip install .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. HTTPS（推荐）

用 Caddy 反向代理，自动获取 SSL 证书：

```
# /etc/caddy/Caddyfile
your-domain.com {
    reverse_proxy localhost:8000
}
```

### 5. 验证

```bash
curl -X POST https://你的域名/api/v1/messages \
  -H "Authorization: Bearer 你的AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "明天下午3点 开会 重要 1小时"}'
```

返回 `{"status":"received","message":"消息已接收，正在处理"}` 即为成功。

## 手机配置

### iOS Shortcuts（快捷指令）

1. 打开"快捷指令" App → 新建快捷指令
2. 添加操作"请求输入"，输入类型选"文本"，提示语填"待办事项"
3. 添加操作"获取 URL 内容"：
   - URL：`https://你的域名/api/v1/messages`
   - 方法：POST
   - 头部：添加 `Authorization` = `Bearer 你的AUTH_TOKEN`
   - 请求体：JSON
     ```json
     {"text": "所提供的输入", "session_id": "iphone"}
     ```
4. 可选：添加"显示通知"确认已发送
5. 将快捷指令添加到主屏幕或设置 Siri 语音触发

### Android HTTP Shortcuts

1. 安装 [HTTP Shortcuts](https://play.google.com/store/apps/details?id=ch.rmy.android.http_shortcuts) App
2. 新建快捷方式：
   - 方法：POST
   - URL：`https://你的域名/api/v1/messages`
   - 请求头：`Authorization: Bearer 你的AUTH_TOKEN`
   - 请求体（JSON）：`{"text": "{input}", "session_id": "android"}`
3. 开启"执行前显示输入对话框"
4. 将快捷方式放到桌面

## 项目结构

```
todo-service/
├── app/
│   ├── main.py           # FastAPI 入口 + API 端点
│   ├── config.py         # 环境变量配置
│   ├── auth.py           # Bearer Token 认证
│   ├── models.py         # 数据模型
│   ├── prompts.py        # LLM prompt 模板
│   └── services/
│       ├── aggregator.py # 多消息聚合（滑动窗口）
│       ├── llm_parser.py # LLM 自然语言解析
│       └── todoist.py    # Todoist 任务创建
├── .env.example
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

## 工作原理

```
手机快捷指令 → POST /api/v1/messages → 聚合器（等待30秒）→ LLM 解析 → Todoist 创建任务
```

1. 手机发送 HTTP 请求到服务器
2. 服务器立即返回 202（不阻塞手机）
3. 如果 30 秒内有后续消息，合并等待
4. 窗口关闭后，将所有消息拼接送入 LLM
5. LLM 提取时间、事项、优先级、时长
6. 调用 Todoist API 创建任务

## 优先级映射

| 你说的 | Todoist 优先级 |
|--------|---------------|
| 紧急、非常重要 | P1（最高） |
| 重要 | P2 |
| 一般 | P3 |
| 不急、随便 | P4（最低） |
