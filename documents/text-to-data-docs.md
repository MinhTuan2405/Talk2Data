# Text-to-Data — Full Documentation

> **Stack:** Vanna 2.0 Agent API · FastAPI Bridge · Open WebUI  
> **Version:** 3.0

---

## Mục lục

- [00. Kiến trúc hệ thống](#00-kiến-trúc-hệ-thống)
- [01. Vanna 2.0 — Những thay đổi cốt lõi](#01-vanna-20--những-thay-đổi-cốt-lõi)
- [02. Yêu cầu hệ thống](#02-yêu-cầu-hệ-thống)
- [03. Tổ chức project](#03-tổ-chức-project)
- [04. Cấu hình môi trường](#04-cấu-hình-môi-trường)
- [05. Bước 1 — Khởi tạo Vanna 2.0 Agent](#05-bước-1--khởi-tạo-vanna-20-agent)
- [06. Bước 2 — FastAPI Bridge](#06-bước-2--fastapi-bridge)
- [07. Bước 3 — Seed Tool Memory](#07-bước-3--seed-tool-memory)
- [08. Bước 4 — Cấu hình Open WebUI](#08-bước-4--cấu-hình-open-webui)
- [09. Khởi chạy toàn hệ thống](#09-khởi-chạy-toàn-hệ-thống)
- [10. Kiểm thử](#10-kiểm-thử)
- [11. Docker Compose — Toàn bộ stack](#11-docker-compose--toàn-bộ-stack)
- [12. Xử lý lỗi thường gặp](#12-xử-lý-lỗi-thường-gặp)
- [13. Lộ trình phát triển](#13-lộ-trình-phát-triển)

---

## 00. Kiến trúc hệ thống

Toàn bộ ứng dụng gồm 3 tầng độc lập: **Open WebUI** (giao diện người dùng), **FastAPI Bridge** (trung gian chuyển đổi format), và **Vanna 2.0 Agent** (lõi xử lý ngôn ngữ tự nhiên → SQL → dữ liệu).

```
👤 USER
   │
   ▼  HTTP
🖥  Open WebUI (:3000)
   │
   ▼  POST /v1/chat/completions  [OpenAI format]
⚡ FastAPI Bridge (:8000)  ← tự xây
   │
   ▼  agent.chat()
🧠 Vanna 2.0 Agent
   ├──▶ ✨ LLM Service (Gemini / OpenAI / Anthropic)
   ├──▶ 🔧 ToolRegistry
   │       ├── RunSqlTool ──▶ 🗄️ Database (PostgreSQL / MySQL)
   │       ├── VisualizeDataTool
   │       └── SearchSavedCorrectToolUsesTool
   └──▶ 📚 Tool Memory (ChromaDB — persist)
              ↑ tự học từ mỗi query thành công
```

> **⚠️ Tại sao cần FastAPI Bridge?**  
> `VannaFastAPIServer` built-in của Vanna 2.0 expose endpoint SSE format riêng, không phải chuẩn OpenAI. Open WebUI chỉ kết nối được với API tương thích OpenAI (`POST /v1/chat/completions`). FastAPI Bridge là lớp trung gian **bắt buộc** phải tự xây.

---

## 01. Vanna 2.0 — Những thay đổi cốt lõi

Vanna 2.0 là **rewrite hoàn toàn**. Nếu bạn từng dùng Vanna 0.x, tất cả API cũ đều không còn tồn tại.

### So sánh API 0.x vs 2.0

| Khái niệm | Vanna 0.x — KHÔNG DÙNG | Vanna 2.0 — ĐÚNG |
|---|---|---|
| Khởi tạo | `class MyVanna(ChromaDB_VectorStore, GoogleGeminiChat)` | `Agent(llm_service, tool_registry, user_resolver, agent_memory)` |
| Sinh SQL | `vn.generate_sql(question)` | Agent tự gọi `RunSqlTool` qua LLM tool-use loop |
| Chạy SQL | `vn.run_sql(sql)` | `RunSqlTool(sql_runner=PostgresRunner(...))` |
| Training | `vn.train(ddl=...)` / `vn.train(sql=...)` | Tool Memory — `SaveTextMemoryTool`, `SaveQuestionToolArgsTool` |
| Kết nối DB | `vn.connect_to_postgres(host=..., dbname=...)` | `RunSqlTool(sql_runner=PostgresRunner(host=..., dbname=...))` |
| LLM config | `config={"model": ..., "api_key": ...}` trong mixin | `GoogleGeminiLlmService(model=..., api_key=...)` |
| Vector store | `ChromaDB_VectorStore` mixin class | `ChromaDBAgentMemory(path="./data")` |
| Auth/RBAC | Không có | `UserResolver` + `User(group_memberships)` + `ToolRegistry(access_groups)` |
| Server | Flask app tự xây hoàn toàn | `VannaFastAPIServer(agent)` + tự xây OpenAI Bridge |

### Các thành phần chính của Vanna 2.0

| Thành phần | Mô tả | Class |
|---|---|---|
| **Agent** | Orchestrator trung tâm — nhận câu hỏi, gọi LLM, quyết định tool nào dùng | `vanna.Agent` |
| **LLM Service** | Kết nối với model ngôn ngữ | `GoogleGeminiLlmService`, `OpenAILlmService`... |
| **ToolRegistry** | Danh sách công cụ Agent được phép dùng, kèm RBAC | `vanna.core.registry.ToolRegistry` |
| **RunSqlTool** | Tool chạy SQL, nhận SqlRunner cho từng loại DB | `vanna.tools.RunSqlTool` |
| **Agent Memory** | Lưu question-SQL pairs thành công để học theo thời gian | `ChromaDBAgentMemory` / `DemoAgentMemory` |
| **UserResolver** | Xác định user từ request context, gán quyền group | `vanna.core.user.UserResolver` (abstract) |

---

## 02. Yêu cầu hệ thống

### Software cần cài

- Python 3.11 trở lên (`python --version` để kiểm tra)
- Docker + Docker Compose
- Git
- Database đang chạy (PostgreSQL / MySQL / SQLite)

### Cài Vanna 2.0

```bash
# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Cài Vanna 2.0 với các integration cần thiết
# Chọn LLM: gemini | openai | anthropic | ollama
# Chọn DB:  postgres | mysql | sqlite | bigquery | snowflake
pip install 'vanna[gemini,fastapi,postgres,chromadb]'

# Các package bổ sung cho Bridge
pip install fastapi uvicorn python-dotenv pydantic
```

### API Keys cần có

- **Gemini:** Lấy tại `aistudio.google.com` → Get API key (miễn phí)
- **OpenAI (nếu dùng):** `platform.openai.com/api-keys`
- **Anthropic (nếu dùng):** `console.anthropic.com`

---

## 03. Tổ chức project

```
text-to-data/
├── app/                          # FastAPI Bridge
│   ├── main.py                   # entry point, FastAPI app + lifespan
│   ├── agent.py                  # Vanna 2.0 Agent singleton
│   ├── routes/
│   │   ├── chat.py               # POST /v1/chat/completions
│   │   └── models.py             # GET /v1/models
│   ├── services/
│   │   ├── agent_caller.py       # gọi agent.chat(), xử lý response
│   │   └── formatter.py          # UiComponent → markdown text
│   ├── middleware/
│   │   └── auth.py               # validate API key từ Open WebUI
│   └── resolvers/
│       └── user_resolver.py      # UserResolver custom implementation
│
├── seed/                          # dữ liệu khởi tạo Tool Memory
│   ├── seed_memory.py             # script chạy 1 lần khi setup
│   ├── ddl/
│   │   └── schema.sql             # CREATE TABLE statements
│   ├── docs/
│   │   └── business_rules.md      # quy tắc nghiệp vụ, giải thích cột
│   └── examples.json              # [{question, sql}, ...]
│
├── chromadb_data/                 # Tool Memory persist (thêm vào .gitignore)
├── docker-compose.yml
├── .env
├── .env.example
└── requirements.txt
```

---

## 04. Cấu hình môi trường

Tạo file `.env` ở root project. Đây là nguồn duy nhất cho toàn bộ configuration.

```env
# ═══════════════════════════════════════════
#  LLM PROVIDER
# ═══════════════════════════════════════════
# Chọn 1 trong: gemini | openai | anthropic | ollama
LLM_PROVIDER=gemini

# Gemini (Google AI Studio — miễn phí tier có sẵn)
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.0-flash

# OpenAI (nếu dùng thay Gemini)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# ═══════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASS=your_password

# ═══════════════════════════════════════════
#  TOOL MEMORY (ChromaDB)
# ═══════════════════════════════════════════
CHROMA_PATH=./chromadb_data
# Tuyệt đối phải set path để persist!
# Nếu dùng DemoAgentMemory (in-memory), data mất sau restart

# ═══════════════════════════════════════════
#  FASTAPI BRIDGE
# ═══════════════════════════════════════════
BRIDGE_HOST=0.0.0.0
BRIDGE_PORT=8000

# API keys để Open WebUI dùng khi gọi vào Bridge
ADMIN_API_KEY=admin-secret-key-here
USER_API_KEY=user-secret-key-here

# CORS — origin của Open WebUI
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Giới hạn số rows trả về (bảo vệ performance)
MAX_RESULT_ROWS=500
```

---

## 05. Bước 1 — Khởi tạo Vanna 2.0 Agent

Đây là phần cốt lõi. Agent được khởi tạo **một lần duy nhất** khi app start và dùng chung cho toàn bộ requests.

> **💡 Tại sao dùng singleton?**  
> ChromaDBAgentMemory mở connection đến ChromaDB khi khởi tạo. Nếu tạo lại mỗi request sẽ cực chậm và mất cache. Agent được khởi tạo một lần trong `lifespan` event của FastAPI.

### `app/agent.py` — Vanna Agent Singleton

```python
"""Vanna 2.0 Agent — khởi tạo một lần, dùng cho cả app."""
import os
from dotenv import load_dotenv

# ── Vanna 2.0 imports — ĐÚNG ──────────────────────────────
from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
    SaveTextMemoryTool,
)

# LLM integrations — chọn 1
from vanna.integrations.google import GoogleGeminiLlmService
# from vanna.integrations.openai import OpenAILlmService
# from vanna.integrations.anthropic import AnthropicLlmService

# Database runner — chọn DB của bạn
from vanna.integrations.postgres import PostgresRunner
# from vanna.integrations.mysql import MySQLRunner
# from vanna.integrations.sqlite import SqliteRunner

# Agent Memory backend
from vanna.integrations.chromadb import ChromaDBAgentMemory
# from vanna.integrations.local.agent_memory import DemoAgentMemory  # chỉ dev

load_dotenv()


# ─────────────────────────────────────────────────────────
#  1. LLM SERVICE
# ─────────────────────────────────────────────────────────
def build_llm_service():
    provider = os.getenv("LLM_PROVIDER", "gemini")

    if provider == "gemini":
        return GoogleGeminiLlmService(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    elif provider == "openai":
        from vanna.integrations.openai import OpenAILlmService
        return OpenAILlmService(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    else:
        raise ValueError(f"LLM_PROVIDER không hỗ trợ: {provider}")


# ─────────────────────────────────────────────────────────
#  2. DATABASE TOOL
# ─────────────────────────────────────────────────────────
def build_db_tool():
    return RunSqlTool(
        sql_runner=PostgresRunner(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
        )
    )


# ─────────────────────────────────────────────────────────
#  3. AGENT MEMORY — ChromaDB (phải persist!)
# ─────────────────────────────────────────────────────────
def build_agent_memory():
    return ChromaDBAgentMemory(
        path=os.getenv("CHROMA_PATH", "./chromadb_data")
    )


# ─────────────────────────────────────────────────────────
#  4. USER RESOLVER — validate API key, gán RBAC group
# ─────────────────────────────────────────────────────────
class ApiKeyUserResolver(UserResolver):
    """Resolver đơn giản dựa trên Bearer token.
    
    - ADMIN_API_KEY  → group 'admin'  (đọc + ghi Tool Memory)
    - USER_API_KEY   → group 'user'   (chỉ đọc / query)
    """
    async def resolve_user(self, ctx: RequestContext) -> User:
        auth = ctx.get_header("Authorization", "")
        key  = auth.replace("Bearer ", "").strip()

        admin_key = os.getenv("ADMIN_API_KEY", "")
        user_key  = os.getenv("USER_API_KEY", "")

        if key == admin_key:
            group = "admin"
            uid   = "admin"
        elif key == user_key:
            group = "user"
            uid   = "openwebui-user"
        else:
            raise PermissionError("Invalid API key")

        return User(id=uid, email=f"{uid}@app", group_memberships=[group])


# ─────────────────────────────────────────────────────────
#  5. BUILD AGENT — kết hợp tất cả
# ─────────────────────────────────────────────────────────
def create_agent() -> Agent:
    llm    = build_llm_service()
    db     = build_db_tool()
    memory = build_agent_memory()

    # ToolRegistry — đăng ký tools kèm quyền RBAC
    tools = ToolRegistry()
    tools.register_local_tool(db,                                access_groups=["admin", "user"])
    tools.register_local_tool(SaveQuestionToolArgsTool(),        access_groups=["admin"])
    tools.register_local_tool(SearchSavedCorrectToolUsesTool(),  access_groups=["admin", "user"])
    tools.register_local_tool(SaveTextMemoryTool(),              access_groups=["admin", "user"])
    tools.register_local_tool(VisualizeDataTool(),               access_groups=["admin", "user"])

    return Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=ApiKeyUserResolver(),
        agent_memory=memory,
    )


# Singleton — được tạo 1 lần khi module load
# app/main.py sẽ gọi create_agent() trong lifespan event
agent: Agent | None = None
```

---

## 06. Bước 2 — FastAPI Bridge

Bridge nhận request theo chuẩn OpenAI từ Open WebUI, chuyển cho Vanna Agent xử lý, rồi trả kết quả về đúng format OpenAI SSE.

### `app/main.py` — Entry Point

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import app.agent as agent_module
from app.routes import chat, models

load_dotenv()

@asynccontextmanager
async def lifespan(application: FastAPI):
    # STARTUP — khởi tạo Agent một lần duy nhất
    print("🚀 Khởi tạo Vanna 2.0 Agent...")
    agent_module.agent = agent_module.create_agent()
    print("✅ Agent sẵn sàng")
    yield
    # SHUTDOWN
    print("🛑 Shutting down...")


app = FastAPI(
    title="Text-to-Data Bridge",
    description="OpenAI-compatible API wrapping Vanna 2.0 Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — cho phép Open WebUI gọi vào
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routes
app.include_router(models.router)
app.include_router(chat.router)

@app.get("/health")
async def health():
    return {"status": "ok", "agent_ready": agent_module.agent is not None}
```

### `app/routes/models.py` — Model Discovery

> **ℹ️ Lưu ý:** Open WebUI gọi `GET /v1/models` để tìm các model có sẵn. Phải trả đúng schema OpenAI, nếu không Open WebUI sẽ không nhận ra model.

```python
import time
from fastapi import APIRouter

router = APIRouter()

@router.get("/v1/models")
async def list_models():
    """Open WebUI gọi endpoint này để discover models."""
    return {
        "object": "list",
        "data": [
            {
                "id": "text-to-data",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "vanna-2.0",
                "permission": [],
                "root": "text-to-data",
                "parent": None,
            }
        ],
    }
```

### `app/routes/chat.py` — Endpoint chính

```python
import json, time, uuid, asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import app.agent as agent_module
from app.services.agent_caller import call_agent

router = APIRouter()


# ── Pydantic models (OpenAI request format) ───────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "text-to-data"
    messages: list[Message]
    stream: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# ── Main endpoint ─────────────────────────────────────────
@router.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, req: Request):
    if agent_module.agent is None:
        raise HTTPException(503, detail="Agent chưa sẵn sàng")

    # Lấy câu hỏi cuối cùng của user
    user_messages = [m for m in body.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(400, detail="Không có câu hỏi từ user")
    question = user_messages[-1].content

    # Lấy API key từ header để UserResolver phân quyền
    api_key = req.headers.get("Authorization", "")

    if body.stream:
        return StreamingResponse(
            stream_response(question, api_key),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        result = await call_agent(question, api_key)
        return build_non_stream_response(result)


# ── Stream generator ──────────────────────────────────────
async def stream_response(question: str, api_key: str):
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created  = int(time.time())

    try:
        result = await call_agent(question, api_key)
        words  = result.split()

        for i, word in enumerate(words):
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": "text-to-data",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant" if i == 0 else None,
                        "content": word + (" " if i < len(words) - 1 else ""),
                    },
                    "finish_reason": None,
                }],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.008)

        # Chunk cuối — finish_reason: stop
        stop_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk",
            "created": created, "model": "text-to-data",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(stop_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    except PermissionError:
        err = {"error": {"message": "API key không hợp lệ", "type": "auth_error"}}
        yield f"data: {json.dumps(err)}\n\n"
    except Exception as e:
        err = {"error": {"message": str(e), "type": "agent_error"}}
        yield f"data: {json.dumps(err)}\n\n"
        yield "data: [DONE]\n\n"


def build_non_stream_response(result: str) -> dict:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "text-to-data",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": result},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
```

### `app/services/agent_caller.py` — Gọi Vanna Agent

```python
import os
from vanna.core.user import User
import app.agent as agent_module
from app.services.formatter import vanna_response_to_markdown


async def call_agent(question: str, authorization: str) -> str:
    """
    Gọi Vanna Agent với câu hỏi từ user.
    authorization: giá trị của header 'Authorization' từ Open WebUI.
    Trả về chuỗi markdown để stream về client.
    """
    key   = authorization.replace("Bearer ", "").strip()
    group = "admin" if key == os.getenv("ADMIN_API_KEY") else "user"
    user  = User(id=key[:8] or "anon", email="user@app", group_memberships=[group])

    # Agent tự điều phối: LLM → tools → memory → response
    response = await agent_module.agent.chat(message=question, user=user)

    return vanna_response_to_markdown(response)
```

### `app/services/formatter.py` — Parse Response Vanna 2.0

```python
"""
Vanna 2.0 trả về list UiComponent objects, không phải plain text.
Hàm này convert chúng thành markdown để gửi về Open WebUI.
"""
from typing import Any
import os


def vanna_response_to_markdown(response: Any) -> str:
    """
    response có thể là:
    - List[UiComponent] — chuẩn Vanna 2.0
    - str               — fallback text
    """
    if isinstance(response, str):
        return response

    if not isinstance(response, list):
        return str(response)

    parts = []
    for component in response:
        comp_type      = getattr(component, "type", "")
        comp_type_name = type(component).__name__

        # SQL code block
        if comp_type == "sql" or "Sql" in comp_type_name:
            sql_text = getattr(component, "sql", "") or getattr(component, "content", "")
            parts.append(f"```sql\n{sql_text}\n```")

        # DataFrame/Table → Markdown table
        elif comp_type == "table" or "DataFrame" in comp_type_name:
            df = getattr(component, "data", None) or getattr(component, "dataframe", None)
            if df is not None:
                parts.append(dataframe_to_markdown(df))

        # Text / SimpleText
        elif comp_type in ("text", "message") or "Text" in comp_type_name:
            text = getattr(component, "text", "") or getattr(component, "content", "")
            if text:
                parts.append(text)

        # Error component
        elif comp_type == "error" or "Error" in comp_type_name:
            msg = getattr(component, "message", str(component))
            parts.append(f"⚠️ **Lỗi:** {msg}")

        else:
            # Fallback
            text = getattr(component, "content", "") or getattr(component, "text", "")
            if text:
                parts.append(str(text))

    return "\n\n".join(parts) if parts else "Không có dữ liệu để hiển thị."


def dataframe_to_markdown(df) -> str:
    """Convert pandas DataFrame thành Markdown table."""
    try:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            max_rows  = int(os.getenv("MAX_RESULT_ROWS", 50))
            truncated = len(df) > max_rows
            df_show   = df.head(max_rows)

            header = " | ".join(str(c) for c in df_show.columns)
            sep    = " | ".join("---" for _ in df_show.columns)
            rows   = [" | ".join(str(v) for v in row) for _, row in df_show.iterrows()]

            table = f"| {header} |\n| {sep} |\n"
            table += "\n".join(f"| {r} |" for r in rows)
            if truncated:
                table += f"\n\n_Hiển thị {max_rows}/{len(df)} rows._"
            return table
    except Exception:
        pass
    return str(df)
```

---

## 07. Bước 3 — Seed Tool Memory

Nạp kiến thức ban đầu về schema DB và quy tắc nghiệp vụ vào Tool Memory. Chạy script này **một lần** khi setup. Sau đó Vanna tự học thêm từ mỗi query thành công.

> **⚠️ Không còn `vn.train()` nữa!**  
> Vanna 2.0 không có phương thức `vn.train(ddl=...)`. Thay vào đó dùng `SaveTextMemoryTool` và `SaveQuestionToolArgsTool` qua Agent chat interface, hoặc gọi trực tiếp vào `agent_memory` object.

### `seed/ddl/schema.sql`

```sql
-- Đặt toàn bộ DDL của database vào đây
-- Agent sẽ dùng để hiểu cấu trúc và sinh SQL đúng

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE,
    region      VARCHAR(50),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    amount      DECIMAL(12,2) NOT NULL,
    status      VARCHAR(20),  -- pending, completed, cancelled
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255),
    category    VARCHAR(100),
    price       DECIMAL(10,2),
    stock       INT DEFAULT 0
);
```

### `seed/examples.json`

```json
[
  {
    "question": "Doanh thu tháng này là bao nhiêu?",
    "sql": "SELECT SUM(amount) as revenue FROM orders WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW()) AND status = 'completed'"
  },
  {
    "question": "Top 5 khách hàng theo doanh thu",
    "sql": "SELECT c.name, SUM(o.amount) as total FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'completed' GROUP BY c.id, c.name ORDER BY total DESC LIMIT 5"
  },
  {
    "question": "Số đơn hàng theo trạng thái",
    "sql": "SELECT status, COUNT(*) as count FROM orders GROUP BY status ORDER BY count DESC"
  },
  {
    "question": "Sản phẩm nào sắp hết hàng?",
    "sql": "SELECT name, category, stock FROM products WHERE stock < 10 ORDER BY stock ASC"
  }
]
```

### `seed/seed_memory.py`

```python
"""
Script này chạy một lần để nạp kiến thức vào Tool Memory.
Chạy: python seed/seed_memory.py

Sau đó Vanna Agent sẽ tự học thêm từ mỗi query thành công.
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.agent import create_agent, build_agent_memory
from vanna.core.user import User

ADMIN = User(
    id="seed-admin",
    email="admin@seed",
    group_memberships=["admin"]
)

async def seed_schema(agent, schema_path: str):
    """Nạp DDL schema vào Tool Memory."""
    if not os.path.exists(schema_path):
        print(f"⚠️  Bỏ qua DDL — không tìm thấy: {schema_path}")
        return

    ddl = open(schema_path, encoding="utf-8").read()
    await agent.chat(
        message=f"Remember this database schema:\n\n{ddl}",
        user=ADMIN
    )
    print("✅ Schema DDL seeded")


async def seed_docs(agent, docs_dir: str):
    """Nạp business documentation."""
    if not os.path.exists(docs_dir):
        return
    for fname in os.listdir(docs_dir):
        if fname.endswith(".md"):
            content = open(os.path.join(docs_dir, fname), encoding="utf-8").read()
            await agent.chat(
                message=f"Remember this business documentation:\n\n{content}",
                user=ADMIN
            )
            print(f"✅ Doc seeded: {fname}")


async def seed_examples(agent_memory, examples_path: str):
    """Nạp question-SQL examples trực tiếp vào memory."""
    if not os.path.exists(examples_path):
        print(f"⚠️  Bỏ qua examples — không tìm thấy: {examples_path}")
        return

    examples = json.load(open(examples_path, encoding="utf-8"))
    for ex in examples:
        await agent_memory.save_question_tool_args(
            question=ex["question"],
            tool_name="run_sql",
            tool_args={"sql": ex["sql"]}
        )
    print(f"✅ {len(examples)} SQL examples seeded")


async def main():
    print("🌱 Bắt đầu seed Tool Memory...")

    agent        = create_agent()
    agent_memory = build_agent_memory()

    await seed_schema(agent,         "seed/ddl/schema.sql")
    await seed_docs(agent,           "seed/docs/")
    await seed_examples(agent_memory, "seed/examples.json")

    print("🎉 Seed hoàn tất! Tool Memory đã sẵn sàng.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 08. Bước 4 — Cấu hình Open WebUI

### Cài đặt Open WebUI

```bash
# Option 1: Docker (khuyến nghị)
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main

# Option 2: pip
pip install open-webui
open-webui serve --port 3000
```

> **ℹ️ Lưu ý Docker:** Nếu chạy Open WebUI bằng Docker, FastAPI Bridge phải accessible qua `host.docker.internal:8000` thay vì `localhost:8000`. Flag `--add-host=host.docker.internal:host-gateway` cho phép điều này.

### Kết nối vào FastAPI Bridge

**Bước 1 — Đăng nhập Open WebUI**  
Mở `http://localhost:3000`, tạo tài khoản admin lần đầu tiên.

**Bước 2 — Admin Panel → Settings → Connections**  
Vào biểu tượng người dùng góc trên phải → **Admin Panel** → tab **Settings** → **Connections**.

**Bước 3 — Thêm OpenAI API Connection**  
Trong phần **OpenAI API**, click dấu **+** hoặc chỉnh sửa entry mặc định:
- **URL:** `http://localhost:8000/v1` (hoặc `http://host.docker.internal:8000/v1` nếu dùng Docker)
- **API Key:** giá trị của `USER_API_KEY` trong `.env`

**Bước 4 — Verify**  
Open WebUI sẽ gọi `GET /v1/models`. Nếu kết nối thành công, model `text-to-data` sẽ xuất hiện.

**Bước 5 — System Prompt (tuỳ chọn)**  
Vào **Workspace → Models → text-to-data → Edit**, thêm system prompt:

> *"Bạn là trợ lý phân tích dữ liệu. Khi nhận câu hỏi, hãy phân tích dữ liệu từ database và trả lời rõ ràng với bảng kết quả và câu SQL đã dùng."*

---

## 09. Khởi chạy toàn hệ thống

### Thứ tự lần đầu setup

**1. Đảm bảo Database đang chạy**

```bash
docker run -d \
  --name postgres \
  -e POSTGRES_DB=mydb \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -p 5432:5432 \
  postgres:16
```

**2. Khởi động FastAPI Bridge**

```bash
# Từ root project
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Nên thấy output:
# 🚀 Khởi tạo Vanna 2.0 Agent...
# ✅ Agent sẵn sàng
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**3. Seed Tool Memory (chỉ lần đầu)**

```bash
python seed/seed_memory.py

# Output mong đợi:
# 🌱 Bắt đầu seed Tool Memory...
# ✅ Schema DDL seeded
# ✅ Doc seeded: business_rules.md
# ✅ 4 SQL examples seeded
# 🎉 Seed hoàn tất!
```

**4. Khởi động Open WebUI**

```bash
docker start open-webui
# Hoặc nếu chưa tạo:
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

### Các lần chạy tiếp theo

```bash
# Chỉ cần chạy Bridge (Agent load memory từ ChromaDB tự động)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Open WebUI (nếu dùng Docker, nó tự start)
docker start open-webui
```

---

## 10. Kiểm thử

### Test 1 — Health check

```bash
curl http://localhost:8000/health

# Kết quả mong đợi:
# {"status": "ok", "agent_ready": true}
```

### Test 2 — Model discovery

```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer your-user-key"

# Kết quả mong đợi:
# {"object": "list", "data": [{"id": "text-to-data", ...}]}
```

### Test 3 — Chat endpoint (không stream)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-user-key" \
  -d '{
    "model": "text-to-data",
    "messages": [{"role": "user", "content": "Có bao nhiêu khách hàng?"}],
    "stream": false
  }'
```

### Test 4 — Stream response

```bash
curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-user-key" \
  -d '{
    "model": "text-to-data",
    "messages": [{"role": "user", "content": "Doanh thu tháng này?"}],
    "stream": true
  }'

# Nên thấy các dòng:
# data: {"id": "chatcmpl-xxx", "choices": [{"delta": {"content": "..."}}]}
# data: [DONE]
```

---

## 11. Docker Compose — Toàn bộ stack

### `docker-compose.yml`

```yaml
version: "3.9"

services:

  # ── PostgreSQL ─────────────────────────────────────
  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── FastAPI Bridge ─────────────────────────────────
  bridge:
    build: .
    restart: unless-stopped
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./chromadb_data:/app/chromadb_data
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  # ── Open WebUI ─────────────────────────────────────
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    restart: unless-stopped
    ports:
      - "3000:8080"
    volumes:
      - open_webui_data:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      OPENAI_API_BASE_URL: http://bridge:8000/v1
      OPENAI_API_KEY: ${USER_API_KEY}
    depends_on:
      - bridge

volumes:
  postgres_data:
  open_webui_data:
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Lệnh chạy

```bash
# Khởi động toàn bộ stack
docker compose up -d

# Seed memory (lần đầu)
docker compose exec bridge python seed/seed_memory.py

# Xem logs
docker compose logs -f bridge
```

---

## 12. Xử lý lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| Open WebUI không thấy model "text-to-data" | Bridge chưa chạy, hoặc URL sai | Kiểm tra `GET /v1/models` trả về đúng format. Kiểm tra CORS. Nếu dùng Docker dùng `host.docker.internal:8000` |
| Agent khởi tạo xong nhưng chat trả về lỗi | DB connection fail hoặc API key LLM sai | Kiểm tra `/health` endpoint. Xem logs uvicorn. Test kết nối DB riêng |
| SQL sinh ra sai hoặc không liên quan | Tool Memory chưa được seed, hoặc thiếu schema | Chạy lại `python seed/seed_memory.py`. Đảm bảo DDL đầy đủ và chính xác |
| Tool Memory mất sau khi restart | Dùng `DemoAgentMemory` thay vì ChromaDB | Dùng `ChromaDBAgentMemory(path="./chromadb_data")` với path tuyệt đối hoặc mount volume |
| ImportError khi import Vanna 2.0 | Cài nhầm Vanna 0.x hoặc thiếu extra dependencies | Chạy `pip install 'vanna[gemini,fastapi,postgres,chromadb]'` đúng version 2.0 |
| Response rỗng hoặc lỗi trong Open WebUI | SSE format không đúng, thiếu `data: [DONE]` | Kiểm tra `stream_response` generator — phải có chunk cuối với `finish_reason: "stop"` và `data: [DONE]` |
| ChromaDB lỗi khi nhiều request đồng thời | ChromaDB không thread-safe với nhiều connection | Đảm bảo Agent là singleton. Không tạo `ChromaDBAgentMemory` mới mỗi request |

---

## 13. Lộ trình phát triển

### Phase 1 — Core `(1-2 ngày)`
**Mục tiêu:** Hệ thống hoạt động end-to-end

- [ ] Khởi tạo Vanna 2.0 Agent với Gemini + PostgreSQL
- [ ] Xây FastAPI Bridge với `/v1/models` + `/v1/chat/completions`
- [ ] Streaming SSE đúng format OpenAI
- [ ] Kết nối Open WebUI → Bridge thành công
- [ ] Seed Tool Memory với schema và examples cơ bản
- **Milestone:** Hỏi được câu đơn giản qua Open WebUI và nhận kết quả

### Phase 2 — Quality `(3-5 ngày)`
**Mục tiêu:** Nâng chất lượng SQL và UX

- [ ] Bổ sung business docs và SQL examples phong phú hơn
- [ ] Response formatter hoàn chỉnh (table, SQL, error)
- [ ] Error handling thân thiện với người dùng
- [ ] Health check endpoint chi tiết (DB ping, memory status)
- [ ] Logging structured (JSON) để dễ debug
- **Milestone:** SQL chính xác với domain-specific queries

### Phase 3 — Production `(1 tuần)`
**Mục tiêu:** Sẵn sàng production

- [ ] RBAC đầy đủ (admin có thể xem/xoá Tool Memory)
- [ ] Rate limiting per user/group
- [ ] Docker Compose với healthcheck đầy đủ
- [ ] Giới hạn SQL (chỉ SELECT, MAX rows inject)
- [ ] Monitoring cơ bản (response time, error rate)
- **Milestone:** Deploy được lên server thật

### Phase 4 — Advanced
**Mục tiêu:** Tính năng nâng cao

- [ ] Multi-database support (query nhiều DB cùng lúc)
- [ ] Chart/visualization export (PNG, CSV)
- [ ] Audit log — lưu lại mọi query người dùng thực hiện
- [ ] Admin UI để quản lý Tool Memory (view, edit, delete)
- [ ] Scheduled re-training khi schema thay đổi

---

*Text-to-Data App · Vanna 2.0 Agent API · FastAPI Bridge · Open WebUI · Full Documentation v3.0*
