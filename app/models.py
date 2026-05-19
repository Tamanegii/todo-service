from datetime import datetime

from pydantic import BaseModel


class MessageRequest(BaseModel):
    text: str
    session_id: str = "default"


class ParsedTask(BaseModel):
    title: str
    due_date: str
    priority: int
    duration: int | None = None


class TaskResponse(BaseModel):
    status: str = "received"
    message: str = "消息已接收，正在处理"


class TaskCreatedInfo(BaseModel):
    task_id: str
    title: str
    due_date: str
    priority: int
    duration: int | None = None
    created_at: datetime
