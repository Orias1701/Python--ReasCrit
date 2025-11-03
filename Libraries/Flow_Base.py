# Flow_Base.py
# Shared utilities for Reasoning / Critic flows.
# - Robust LLM call with retries
# - Extract FIRST top-level JSON only
# - Minimal JSON validation hooks
# - Sanitization
# - Word-count helper
import json
import re
import time
from typing import Optional, Dict, Any, List, Callable, Tuple


class FlowError(Exception):
    pass


class JSONParseError(FlowError):
    pass


class FlowBase:
    """
    Base class. Subclasses should:
      - set self.client to a callable taking (prompt, **kwargs) and returning either:
        * str response, or
        * dict with ["choices"][0]["text"] / ["choices"][0]["message"]["content"]
      - optionally override postprocess()
    """

    def __init__(self, client: Callable, retries: List[float] = None, request_kwargs: Dict[str, Any] = None):
        self.client = client
        self.retries = retries or [0, 0.5, 1.0, 2.0]
        self.request_kwargs = request_kwargs or {}

    # ---------------- PUBLIC API ----------------
    def call_llm(self, prompt: str, **overrides) -> str:
        """Call underlying LLM client with retry + simple backoff."""
        kwargs = {**self.request_kwargs, **overrides}
        last_err = None
        for delay in self.retries:
            if delay > 0:
                time.sleep(delay)
            try:
                raw = self._invoke_client(prompt, **kwargs)
                return raw or ""
            except Exception as e:
                last_err = e
        raise FlowError(f"LLM call failed after retries: {last_err}")

    def extract_first_json(self, text: str) -> str:
        """
        Extract FIRST top-level JSON object.
        More robust than naive regex by using a simple brace stack.
        """
        if not text:
            raise JSONParseError("Empty text")
        start = -1
        depth = 0
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start != -1:
                        return text[start:i+1]
        raise JSONParseError("No top-level JSON object found")

    def coerce_model_to_text(self, resp: Any) -> str:
        """
        Normalize client outputs into pure text.
        Supports:
          - str
          - dict with OpenAI-like schema
          - dict with llama.cpp-like schema
        """
        if isinstance(resp, str):
            return resp
        if isinstance(resp, dict):
            # openai-like
            try:
                return resp["choices"][0]["message"]["content"]
            except Exception:
                pass
            # text-like
            try:
                return resp["choices"][0]["text"]
            except Exception:
                pass
            # llama.cpp (some variants return "content")
            if "content" in resp and isinstance(resp["content"], str):
                return resp["content"]
        # Fallback stringify
        return str(resp)

    def sanitize_outer_text(self, s: str) -> str:
        """Remove code-fences, XML/HTML tags, and trim."""
        if not isinstance(s, str):
            return s
        s = s.strip()
        s = re.sub(r"```.*?```", "", s, flags=re.S)
        s = re.sub(r"<[^>]+>", "", s)
        return s.strip()

    def count_words(self, text: str) -> int:
        return len(re.findall(r"\b\w+\b", text or ""))

    # ---------------- HOOKS ----------------
    def postprocess(self, data: Dict[str, Any], meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """Subclasses can override to enforce freeze/repairs."""
        return data

    # ---------------- INTERNAL ----------------
    def _invoke_client(self, prompt: str, **kwargs) -> str:
        """
        Call the client and return text. We do NOT impose stop tokens here,
        let caller decide in request_kwargs if needed.
        """
        resp = self.client(prompt, **kwargs)
        text = self.coerce_model_to_text(resp)
        return self.sanitize_outer_text(text)

    def parse_first_json(self, text: str) -> Dict[str, Any]:
        blob = self.extract_first_json(text)
        try:
            return json.loads(blob)
        except Exception as e:
            raise JSONParseError(f"JSON decode error: {e}") from e

    # Utility for "repair" missing keys in a shallow dict path
    def ensure_keys(self, data: Dict[str, Any], path: List[str], defaults: Dict[str, Any]) -> None:
        """
        Ensure a dict path exists, and fill missing child keys by defaults.
        Example:
            ensure_keys(data, ["reasoning"], {"topic":"", "key_ideas":"", "filtered_ideas":""})
        """
        node = data
        for key in path:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
            node = node[key]
        for k, v in defaults.items():
            if k not in node:
                node[k] = v
