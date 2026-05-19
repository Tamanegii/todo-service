import asyncio
import logging

from todoist_api_python.api import TodoistAPI

from ..config import settings
from ..models import ParsedTask

logger = logging.getLogger(__name__)

_api = TodoistAPI(settings.todoist_api_token)


async def create_task(parsed: ParsedTask) -> dict:
    kwargs: dict = {
        "content": parsed.title,
        "due_datetime": parsed.due_date,
        "priority": parsed.priority,
    }
    if parsed.duration:
        kwargs["duration"] = parsed.duration
        kwargs["duration_unit"] = "minute"
    if settings.todoist_project_id:
        kwargs["project_id"] = settings.todoist_project_id

    task = await asyncio.to_thread(_api.add_task, **kwargs)
    logger.info("Todoist task created: %s (id=%s)", task.content, task.id)
    return {"task_id": task.id, "title": task.content, "url": task.url}
