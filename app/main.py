import logging
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .auth import verify_token
from .config import settings
from .models import MessageRequest, TaskResponse
from .services.aggregator import MessageAggregator
from .services.llm_parser import parse_task
from .services.todoist import create_task

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def _process_aggregated(session_id: str, text: str) -> None:
    parsed = await parse_task(text)
    result = await create_task(parsed)
    logger.info("Task created for session %s: %s", session_id, result)


aggregator = MessageAggregator(on_complete=_process_aggregated)

app = FastAPI(title="Todo Service", version="0.1.0")

_static_dir = Path(__file__).parent / "static"


def _check_web_auth(token: str | None) -> bool:
    return token == settings.auth_token


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#1a1a2e;color:#eee;
min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{width:300px;text-align:center}
input{width:100%;padding:.75rem 1rem;border:1px solid #333;border-radius:8px;
background:#16213e;color:#eee;font-size:1rem;margin-bottom:1rem}
input:focus{outline:none;border-color:#4a6fa5}
button{width:100%;padding:.75rem;border:none;border-radius:8px;
background:#4a6fa5;color:#fff;font-size:1rem;cursor:pointer}
button:hover{background:#5a8fbf}
</style></head><body><div class="box">
<h2 style="margin-bottom:1.5rem;font-weight:400;color:#a0a0b0">登录</h2>
<form method="POST" action="/login">
<input type="password" name="token" placeholder="输入密码" autofocus>
<button type="submit">确认</button>
</form></div></body></html>"""


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    token = form.get("token", "")
    if token == settings.auth_token:
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie("todo_token", token, httponly=True, max_age=86400 * 30)
        return resp
    return RedirectResponse("/login?error=1", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def index(todo_token: str | None = Cookie(default=None)):
    if not _check_web_auth(todo_token):
        return RedirectResponse("/login")
    return HTMLResponse((_static_dir / "index.html").read_text(encoding="utf-8"))


@app.post("/api/v1/messages", status_code=202, response_model=TaskResponse)
async def receive_message(
    req: MessageRequest,
    request: Request,
    todo_token: str | None = Cookie(default=None),
):
    auth_header = request.headers.get("authorization", "")
    has_bearer = auth_header.startswith("Bearer ") and auth_header[7:] == settings.auth_token
    has_cookie = _check_web_auth(todo_token)

    if not has_bearer and not has_cookie:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    await aggregator.add_message(req.session_id, req.text)
    return TaskResponse()
