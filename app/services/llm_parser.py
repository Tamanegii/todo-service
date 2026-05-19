import json
import logging

from openai import AsyncOpenAI

from ..config import settings
from ..models import ParsedTask
from ..prompts import build_system_prompt

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


async def parse_task(text: str) -> ParsedTask:
    response = await _client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    data = json.loads(content)
    logger.info("LLM parsed: %s", data)
    return ParsedTask(**data)
