"""
Gemini client — wraps the Google GenAI SDK for use across all Phase 5 services.

Responsibilities:
- Load API key and model settings from environment
- Initialize the Google GenAI client (lazy singleton)
- Expose async generate() and stream() methods
- Handle retries, timeouts, and API exceptions
- Log request timing and token usage
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.core.exceptions import SehatSaathiException

logger = logging.getLogger(__name__)
settings = get_settings()


# ------------------------------------------------------------------ #
# Custom exceptions
# ------------------------------------------------------------------ #

class GeminiConfigException(SehatSaathiException):
    """Raised when Gemini cannot be initialised (missing API key, etc.)."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=503)


class GeminiAPIException(SehatSaathiException):
    """Raised when the Gemini API returns an error."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=502)


class GeminiTimeoutException(SehatSaathiException):
    """Raised when a Gemini request exceeds the configured timeout."""
    def __init__(self) -> None:
        super().__init__(
            message="Gemini request timed out. Please try again.",
            status_code=504,
        )


# ------------------------------------------------------------------ #
# Result dataclass
# ------------------------------------------------------------------ #

@dataclass
class GenerationResult:
    """Structured result from a Gemini generation call."""
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
# Client
# ------------------------------------------------------------------ #

class GeminiClient:
    """
    Singleton wrapper around the Google GenAI SDK.

    Thread-safe: initialised once on first call to ``generate()``
    or ``health_check()``.

    Usage::

        result = await gemini_client.generate("Explain this report...")
        print(result.text)
    """

    _instance: Optional["GeminiClient"] = None
    _native_client: Optional[object] = None
    _ready: bool = False

    def __new__(cls) -> "GeminiClient":
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
        """Initialise the Google GenAI client."""
        if not settings.GEMINI_API_KEY:
            raise GeminiConfigException(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file: GEMINI_API_KEY=your_key_here"
            )
        try:
            from google import genai  # noqa: PLC0415
            self._native_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self._ready = True
            logger.info(
                "GeminiClient ready — model: %s, max_tokens: %d",
                settings.GEMINI_MODEL, settings.GEMINI_MAX_TOKENS,
            )
        except ImportError as exc:
            raise GeminiConfigException(
                "google-genai package is not installed. "
                "Run: pip install google-genai"
            ) from exc

    # ---------------------------------------------------------------- #
    # Core generation
    # ---------------------------------------------------------------- #

    def _build_config(self) -> dict:
        """Build the generation config dict from settings."""
        from google.genai import types  # noqa: PLC0415
        return types.GenerateContentConfig(
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=settings.GEMINI_TOP_P,
            top_k=settings.GEMINI_TOP_K,
        )

    def _call_api(self, prompt: str) -> GenerationResult:
        """
        Synchronous Gemini API call.
        Called from ``generate()`` via run_in_threadpool.
        """
        self._ensure_ready()
        t0 = time.perf_counter()

        response = self._native_client.models.generate_content(  # type: ignore[union-attr]
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=self._build_config(),
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Extract token usage metadata
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens   = getattr(usage, "prompt_token_count", 0) or 0
        response_tokens = getattr(usage, "candidates_token_count", 0) or 0
        total_tokens    = getattr(usage, "total_token_count", 0) or (
            prompt_tokens + response_tokens
        )
        finish_reason = ""
        if response.candidates:
            finish_reason = str(
                getattr(response.candidates[0], "finish_reason", "")
            )

        logger.info(
            "Gemini: %.0fms | tokens: %d prompt + %d response = %d total | finish=%s",
            elapsed_ms, prompt_tokens, response_tokens, total_tokens, finish_reason,
        )

        return GenerationResult(
            text=response.text or "",
            model=settings.GEMINI_MODEL,
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
        Send a prompt to Gemini and return the generated text.

        Runs the synchronous SDK call in a thread pool to keep
        the FastAPI event loop non-blocking.

        Args:
            prompt:  Full prompt string (system instruction + context + task).
            retries: Number of retry attempts already made (internal).

        Returns:
            :class:`GenerationResult` with text and token metadata.

        Raises:
            :class:`GeminiConfigException`: API key not set or SDK missing.
            :class:`GeminiAPIException`:    API returned an error.
            :class:`GeminiTimeoutException`: Request exceeded timeout.
        """
        max_retries = settings.GEMINI_MAX_RETRIES

        try:
            result = await asyncio.wait_for(
                run_in_threadpool(self._call_api, prompt),
                timeout=float(settings.GEMINI_TIMEOUT),
            )
            return result

        except asyncio.TimeoutError:
            if retries < max_retries:
                logger.warning("Gemini timeout — retry %d/%d", retries + 1, max_retries)
                await asyncio.sleep(2 ** retries)  # exponential back-off
                return await self.generate(prompt, retries=retries + 1)
            raise GeminiTimeoutException()

        except GeminiConfigException:
            raise

        except Exception as exc:
            err_str = str(exc)
            if retries < max_retries and (
                "429" in err_str or "rate" in err_str.lower() or "503" in err_str
            ):
                wait = 2 ** (retries + 1)
                logger.warning(
                    "Gemini transient error (%s) — retry %d/%d in %ds",
                    exc.__class__.__name__, retries + 1, max_retries, wait,
                )
                await asyncio.sleep(wait)
                return await self.generate(prompt, retries=retries + 1)

            logger.error("Gemini API error: %s", exc)
            raise GeminiAPIException(f"Gemini request failed: {exc}") from exc

    # ---------------------------------------------------------------- #
    # Streaming
    # ---------------------------------------------------------------- #

    def _stream_api(self, prompt: str):
        """Synchronous Gemini streaming generator (run in executor)."""
        self._ensure_ready()
        for chunk in self._native_client.models.generate_content_stream(  # type: ignore[union-attr]
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=self._build_config(),
        ):
            if chunk.text:
                yield chunk.text

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Async generator that yields text chunks as they arrive from Gemini.

        Suitable for Server-Sent Events (SSE) endpoints.

        Args:
            prompt: Full prompt string.

        Yields:
            Text chunk strings.
        """
        self._ensure_ready()
        loop = asyncio.get_running_loop()

        # Stream via a blocking iterator run in the executor
        import concurrent.futures  # noqa: PLC0415
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

            def _run():
                try:
                    for chunk in self._stream_api(prompt):
                        loop.call_soon_threadsafe(queue.put_nowait, chunk)
                except Exception as exc:
                    logger.error("Gemini stream error: %s", exc)
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

            executor.submit(_run)

            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item

    # ---------------------------------------------------------------- #
    # Health check
    # ---------------------------------------------------------------- #

    async def health_check(self) -> dict:
        """
        Verify that the Gemini API is reachable and the key is valid.

        Returns:
            Dict with ``status``, ``model``, and ``message`` keys.
        """
        if not settings.GEMINI_API_KEY:
            return {
                "status": "unhealthy",
                "model": settings.GEMINI_MODEL,
                "message": "GEMINI_API_KEY is not configured.",
                "api_key_configured": False,
            }
        try:
            result = await self.generate("Reply with exactly: OK")
            return {
                "status": "healthy",
                "model": settings.GEMINI_MODEL,
                "message": f"Gemini API is reachable. Latency: {result.latency_ms:.0f}ms",
                "api_key_configured": True,
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "model": settings.GEMINI_MODEL,
                "message": str(exc),
                "api_key_configured": True,
            }


# Module-level singleton
gemini_client = GeminiClient()
