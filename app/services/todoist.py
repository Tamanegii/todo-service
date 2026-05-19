import asyncio
import logging

from todoist_api_python.api import TodoistAPI

from ..config import settings
from ..models import ParsedTask

logger = logging.getLogger(__name__)

_api = TodoistAPI(settings.todoist_api_token)


async def _resolve_project_id(name_or_id: str) -> str | None:
    if name_or_id.isdigit():
        return name_or_id
    projects = await asyncio.to_thread(_api.get_projects)
    for p in projects:
        if p.name == name_or_id:
            return p.id
    return None


async def create_task(parsed: ParsedTask, project_id: str | None = None) -> dict:
    kwargs: dict = {
        "content": parsed.title,
        "due_datetime": parsed.due_date,
        "priority": parsed.priority,
    }
    if parsed.duration:
        kwargs["duration"] = parsed.duration
        kwargs["duration_unit"] = "minute"

    pid = project_id or settings.todoist_project_id
    if pid:
        resolved = await _resolve_project_id(pid)
        if resolved:
            kwargs["project_id"] = resolved

    task = await asyncio.to_thread(_api.add_task, **kwargs)
    logger.info("Todoist task created: %s (id=%s)", task.content, task.id)
    return {"task_id": task.id, "title": task.content, "url": task.url}
