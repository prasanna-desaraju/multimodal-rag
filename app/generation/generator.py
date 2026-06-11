"""Grok generator implementation.

This implementation keeps business logic provider-agnostic by implementing
the `Generator` interface and registering itself as "grok". It performs
HTTP calls to a configurable Grok endpoint with retry and timeout handling.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import time
import logging

import requests
import socket
from urllib.parse import urlparse

from .generator_interface import Generator, register_generator
from ..models.document import Document

logger = logging.getLogger(__name__)


@register_generator("grok")
class GrokGenerator(Generator):
    def __init__(self, api_key: str = None, endpoint: str = None, headers: Optional[Dict[str, str]] = None):
        self.api_key = api_key or ""
        # Default endpoint is configurable; this value is a placeholder and
        # should be overridden with the real Grok API URL via `endpoint`.
        self.endpoint = endpoint or "https://api.grok.example/v1/generate"
        self.headers = headers or {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Validate endpoint early to give clear errors when DNS/isolation issues exist.
        try:
            self._validate_endpoint(self.endpoint)
        except Exception as e:
            # Raise a clearer error so callers (UI/pipeline) can display helpful guidance.
            raise RuntimeError(
                f"Invalid or unreachable GROK endpoint '{self.endpoint}': {e}. "
                "Set a reachable GROK_ENDPOINT in your .env or environment."
            )

    def _call_provider(self, payload: Dict[str, Any], timeout: Optional[float]) -> requests.Response:
        return requests.post(self.endpoint, json=payload, headers=self.headers, timeout=timeout)

    def _validate_endpoint(self, endpoint: str) -> None:
        # Basic URL parsing and DNS resolution check to fail fast with clear message.
        parsed = urlparse(endpoint)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("endpoint must be a valid http(s) URL")

        host = parsed.hostname
        if not host:
            raise ValueError("could not parse hostname from endpoint")

        try:
            # This will raise socket.gaierror if resolution fails.
            socket.getaddrinfo(host, parsed.port or 443)
        except socket.gaierror as e:
            raise RuntimeError(f"DNS resolution failed for host '{host}': {e}") from e

    def generate(self, query: str, inserted_context: List[Document], timeout: Optional[float] = 30.0, retries: int = 3, **kwargs) -> Dict[str, Any]:
        # Build prompt by concatenating context and query. Avoid explicit
        # anti-hallucination wording per requirements; keep prompt neutral.
        context_texts = [d.content for d in inserted_context if getattr(d, "content", None)]
        context_block = "\n\n".join(context_texts)
        prompt = f"Context:\n{context_block}\n\nQuery:\n{query}\n\nAnswer:"

        payload = {"prompt": prompt, "max_tokens": kwargs.get("max_tokens", 512)}

        backoff = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(1, max(1, retries) + 1):
            try:
                resp = self._call_provider(payload, timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    # It's provider-specific; try common fields
                    text = data.get("text") or data.get("output") or ""
                    return {"text": text, "raw": data}
                # Retry on server errors
                if 500 <= resp.status_code < 600:
                    logger.warning("GrokGenerator server error %s (attempt %d/%d)", resp.status_code, attempt, retries)
                    last_exc = RuntimeError(f"Server error: {resp.status_code}")
                else:
                    # client error or unexpected response; return raw to caller
                    logger.debug("GrokGenerator received status %s: returning raw", resp.status_code)
                    try:
                        return {"text": resp.text, "raw": resp.json()}
                    except Exception:
                        return {"text": resp.text, "raw": {"status": resp.status_code}}
            except requests.Timeout as e:
                last_exc = e
                logger.warning("GrokGenerator request timed out (attempt %d/%d)", attempt, retries)
            except requests.RequestException as e:
                last_exc = e
                logger.warning("GrokGenerator request error (attempt %d/%d): %s", attempt, retries, str(e))

            # backoff before retrying
            if attempt < retries:
                time.sleep(backoff)
                backoff *= 2

        # If we reach here, all retries failed
        raise RuntimeError("GrokGenerator failed after retries") from last_exc

