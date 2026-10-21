import asyncio
import logging
import random
from typing import Any, List
from backend.app.config import get_settings

logger = logging.getLogger(__name__)

# Global concurrency semaphore
_groq_semaphore: asyncio.Semaphore = None


def get_groq_semaphore() -> asyncio.Semaphore:
    global _groq_semaphore
    if _groq_semaphore is None:
        settings = get_settings()
        _groq_semaphore = asyncio.Semaphore(settings.GROQ_CONCURRENCY_LIMIT)
    return _groq_semaphore


import re

async def safe_llm_invoke(llm: Any, messages: List[Any], max_retries: int = 5) -> Any:
    """
    Invokes LLM within a concurrency-limiting semaphore and applies exponential
    backoff with jitter upon encountering HTTP 429 rate limit exceptions.
    Parses 'try again in Xs' from Groq error messages when available.
    """
    semaphore = get_groq_semaphore()
    base_delay = 2.0

    async with semaphore:
        for attempt in range(max_retries + 1):
            try:
                response = await llm.ainvoke(messages)
                return response
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = (
                    "429" in err_str or
                    "rate limit" in err_str or
                    "rate_limit_exceeded" in err_str or
                    "too many requests" in err_str or
                    ("tokens" in err_str and "code" in err_str)
                )
                if is_rate_limit and attempt < max_retries:
                    # Parse specific retry delay if returned by Groq (e.g. 'try again in 4m3.64s' or 'try again in 12.3s')
                    m = re.search(r"try again in (?:(\d+)m)?([\d\.]+)s", err_str)
                    if m:
                        try:
                            mins = float(m.group(1)) if m.group(1) else 0.0
                            secs = float(m.group(2)) if m.group(2) else 0.0
                            parsed_delay = (mins * 60.0) + secs
                            if parsed_delay > 60.0 or "tokens per day" in err_str or "tpd" in err_str:
                                logger.error(
                                    f"[Groq Guard] Daily token quota exceeded or excessive wait time ({parsed_delay:.1f}s). "
                                    f"Aborting retries immediately to avoid hanging. Consider switching MODEL_NAME to "
                                    f"llama-3.3-70b-versatile or llama-3.1-8b-instant."
                                )
                                raise e
                            delay = parsed_delay + random.uniform(0.5, 1.2)
                        except Exception as parse_err:
                            if "excessive wait time" in str(parse_err) or "daily token quota" in str(parse_err).lower():
                                raise e
                            delay = (base_delay * (1.8 ** attempt)) + random.uniform(0.5, 1.5)
                    else:
                        delay = max(3.0, (base_delay * (1.8 ** attempt))) + random.uniform(0.5, 1.5)

                    logger.warning(
                        f"[Groq Guard] Encountered Rate Limit (Attempt {attempt+1}/{max_retries}). "
                        f"Backing off for {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[Groq Guard] Invocation error: {e}")
                    raise e
