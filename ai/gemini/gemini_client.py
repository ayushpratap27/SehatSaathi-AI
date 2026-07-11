"""
LLM client — wraps the Groq SDK for fast inference via Llama 3.3.

Previously used Google Gemini; replaced with Groq for:
  - Faster inference (Groq's custom LPU hardware)
  - Free tier availability
  - OpenAI-compatible API

Public interface is unchanged so all services (summary, explanation, chat)
work without modification.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.core.exceptions import SehatSaathiException

logger = logging.getLogger(__name__)
settings = get_settings()


# ------------------------------------------------------------------ #
# Custom exceptions (names kept for backward compatibility)
# ------------------------------------------------------------------ #

class GeminiConfigException(SehatSaathiException):
    """Raised when the LLM client cannot be initialised."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=503)


class GeminiAPIException(SehatSaathiException):
    """Raised when the LLM API returns an error."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=502)


class GeminiTimeoutException(SehatSaathiException):
    """Raised when an LLM request exceeds the configured timeout."""
    def __init__(self) -> None:
        super().__init__(
            message="LLM request timed out. Please try again.",
            status_code=504,
        )


# ------------------------------------------------------------------ #
# Result dataclass
# ------------------------------------------------------------------ #

@dataclass
class GenerationResult:
    """Structured result from one LLM generation call."""
    text: str
    model: str
    prompt_tokens: int = 0
    response_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = ""

    @property
    def tokens_used(self) -> int:
        return self.total_tokens or (self.prompt_tokens + self.response_tokens)


# ------------------------------------------------------------------ #
# LLM Client (Groq backend)
# ------------------------------------------------------------------ #

class LLMClient:
    """
    Singleton wrapper around the Groq SDK.

    Sends prompts to Llama 3.3 70B Versatile (or any configured GROQ_MODEL)
    via Groq's ultra-fast LPU inference API.

    Usage::

        result = await llm_client.generate("Explain this medical report...")
        print(result.text)
    """

    _instance: Optional["LLMClient"] = None
    _native_client: Optional[object] = None
    _ready: bool = False

    def __new__(cls) -> "LLMClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ---------------------------------------------------------------- #
    # Initialisation
    # ---------------------------------------------------------------- #

    def _ensure_ready(self) -> None:
        if self._ready:
            return
        self._init()

    def _init(self) -> None:
        """Initialise the Groq client."""
        if not settings.GROQ_API_KEY:
            raise GeminiConfigException(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com and add it to .env"
            )
        try:
            from groq import Groq  # noqa: PLC0415
            self._native_client = Groq(api_key=settings.GROQ_API_KEY)
            self._ready = True
            logger.info("LLM client ready — model: %s", settings.GROQ_MODEL)
        except ImportError as exc:
            raise GeminiConfigException(
                "groq package is not installed. Run: pip install groq"
            ) from exc

    # ---------------------------------------------------------------- #
    # Core generation
    # ---------------------------------------------------------------- #

    def _call_api(self, prompt: str) -> GenerationResult:
        """
        Synchronous Groq API call (run in thread pool by generate()).

        The system instruction is embedded in the prompt string by the
        prompt templates, so we send it as a single user message.
        """
        self._ensure_ready()
        t0 = time.perf_counter()

        completion = self._native_client.chat.completions.create(  # type: ignore[union-attr]
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        text = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens   = usage.prompt_tokens    if usage else 0
        response_tokens = usage.completion_tokens if usage else 0
        total_tokens    = usage.total_tokens      if usage else 0
        finish_reason   = completion.choices[0].finish_reason or ""

        logger.info(
            "Groq: %.0fms | tokens: %d prompt + %d response = %d total | finish=%s",
            elapsed_ms, prompt_tokens, response_tokens, total_tokens, finish_reason,
        )
        return GenerationResult(
            text=text,
            model=settings.GROQ_MODEL,
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            total_tokens=total_tokens,
            latency_ms=elapsed_ms,
            finish_reason=finish_reason,
        )

    async def generate(
        self,
        prompt: str,
        retries: int = 0,
    ) -> GenerationResult:
        """
        Send a prompt to Groq and return the generated text.

        Runs the synchronous SDK call in a thread pool so the FastAPI
        event loop stays non-blocking.

        Args:
            prompt:  Full prompt string.
            retries: Internal retry counter.

        Returns:
            :class:`GenerationResult` with text and token metadata.
        """
        max_retries = settings.GROQ_MAX_RETRIES

        try:
            result = await asyncio.wait_for(
                run_in_threadpool(self._call_api, prompt),
                timeout=float(settings.GROQ_TIMEOUT),
            )
            return result

        except asyncio.TimeoutError:
            if retries < max_retries:
                logger.warning("Groq timeout — retry %d/%d", retries + 1, max_retries)
                await asyncio.sleep(2 ** retries)
                return await self.generate(prompt, retries=retries + 1)
            raise GeminiTimeoutException()

        except GeminiConfigException:
            raise

        except Exception as exc:
            err_str = str(exc)
            # Retry on rate-limit and transient server errors
            if retries < max_retries and any(
                code in err_str for code in ("429", "503", "rate_limit")
            ):
                wait = 2 ** (retries + 1)
                logger.warning(
                    "Groq transient error (%s) — retry %d/%d in %ds",
                    exc.__class__.__name__, retries + 1, max_retries, wait,
                )
                await asyncio.sleep(wait)
                return await self.generate(prompt, retries=retries + 1)

            logger.error("Groq API error: %s", exc)
            raise GeminiAPIException(f"LLM request failed: {exc}") from exc

    # ---------------------------------------------------------------- #
    # Streaming
    # ---------------------------------------------------------------- #

    def _stream_api(self, prompt: str):
        """Synchronous Groq streaming generator."""
        self._ensure_ready()
        stream = self._native_client.chat.completions.create(  # type: ignore[union-attr]
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Async generator that yields text chunks as they arrive from Groq."""
        self._ensure_ready()
        loop = asyncio.get_running_loop()
        import concurrent.futures  # noqa: PLC0415

        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def _run():
            try:
                for chunk in self._stream_api(prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as exc:
                logger.error("Groq stream error: %s", exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item

    # ---------------------------------------------------------------- #
    # Health check
    # ---------------------------------------------------------------- #

    async def health_check(self) -> dict:
        """Verify Groq API is reachable and the key is valid."""
        if not settings.GROQ_API_KEY:
            return {
                "status": "unhealthy",
                "model": settings.GROQ_MODEL,
                "message": "GROQ_API_KEY is not configured.",
                "api_key_configured": False,
            }
        try:
            result = await self.generate("Reply with exactly the word: OK")
            return {
                "status": "healthy",
                "model": settings.GROQ_MODEL,
                "message": f"Groq API is reachable. Latency: {result.latency_ms:.0f}ms",
                "api_key_configured": True,
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "model": settings.GROQ_MODEL,
                "message": str(exc),
                "api_key_configured": True,
            }


# ------------------------------------------------------------------ #
# Module-level singleton (backward-compatible name)
# ------------------------------------------------------------------ #
GeminiClient = LLMClient   # alias kept so existing imports don't break
gemini_client = LLMClient()
