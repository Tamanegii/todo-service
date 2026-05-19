import logging

from fastapi import Depends, FastAPI

from .auth import verify_token
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


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/messages", status_code=202, response_model=TaskResponse)
async def receive_message(
    req: MessageRequest,
    _: str = Depends(verify_token),
):
    await aggregator.add_message(req.session_id, req.text)
    return TaskResponse()
