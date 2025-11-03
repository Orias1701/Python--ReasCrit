# Libraries/Flow_Reasoning.py
import json
import re
from typing import Any, Dict, Optional
from . import Flow_Base

_WORD_RE = re.compile(r"\b\w+\b")

def _word_count(s: str) -> int:
    return len(_WORD_RE.findall(s or ""))


class ReasoningFlow(Flow_Base.FlowBase):
    """
    Reasoning + Refinement engine.
    - Round 1: generate reasoning + summary
    - Round >1: refine reasoning + summary using critic feedback
    - Always return strict JSON (string)
    - With degrade-safe fallback
    """

    def _parse_best_json(self, raw: str) -> Dict[str, Any]:
        """
        Try JSON.parse → brace-extract → sanitize quotes → fallback empty
        """
        try:
            return self.parse_first_json(raw)
        except:
            try:
                txt = self.extract_first_json(raw)
            except:
                txt = raw

            # Try repairing: single quotes → double quotes
            txt = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)\s*:',
                         lambda m: m.group(1) + f'"{m.group(2)}":', txt)
            txt = re.sub(r":\s*'([^']*)'",
                         lambda m: ':"{}"'.format(m.group(1).replace('"', '\\"')),
                         txt)
            txt = re.sub(r",\s*'([^']*)'",
                         lambda m: ',"{}"'.format(m.group(1).replace('"', '\\"')),
                         txt)
            txt = re.sub(r",\s*([}\]])", r"\1", txt)

            try:
                return json.loads(txt)
            except:
                return {
                    "reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""},
                    "summary": ""
                }

    def _sanitize_feedback_text(self, fb: Optional[str]) -> str:
        if not fb:
            return ""
        s = fb.strip()
        # remove trailing "Written by ..."
        s = re.sub(r"(Written by.*)$", "", s).strip()
        return s

    def _ensure_fields(self, obj: Dict[str, Any]):
        if "reasoning" not in obj or not isinstance(obj["reasoning"], dict):
            obj["reasoning"] = {"topic": "", "key_ideas": "", "filtered_ideas": ""}
        for k in ["topic", "key_ideas", "filtered_ideas"]:
            if k not in obj["reasoning"]:
                obj["reasoning"][k] = ""

        if "summary" not in obj or not isinstance(obj["summary"], str):
            obj["summary"] = ""

        return obj

    def _safe_prev(self, prev_text: Optional[str]) -> Dict[str, Any]:
        if not prev_text:
            return {
                "reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""},
                "summary": ""
            }
        try:
            obj = self.parse_first_json(prev_text)
            self._ensure_fields(obj)
            return obj
        except:
            return {
                "reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""},
                "summary": ""
            }

    def run_reason_or_refine(
        self,
        reason_prompt: str,
        refine_prompt: str,
        current_reasoning: Optional[str],
        source_text: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:

        fb_clean = self._sanitize_feedback_text(feedback)

        if fb_clean:
            prompt = (
                f"{refine_prompt}"
                f"\n\n[PREVIOUS OUTPUT]\n\n"
                f"{current_reasoning}"
                "\n\n[FEEDBACK]\n\n"
                f"{fb_clean}"
                "\n\n[ORIGINAL DOCUMENT]\n\n"
                f"{source_text}"
            ).strip()
        else:
            prompt = (
                f"{reason_prompt}"
                "\n\n[ORIGINAL DOCUMENT]\n\n"
                f"{source_text}"
            ).strip()

        raw = self.call_llm(f"<|user|>\n{prompt}\n<|end|>\n<|assistant|>")
        obj = self._parse_best_json(raw)
        obj = self._ensure_fields(obj)

        # refine: allow changes but prevent degradation
        if fb_clean:
            prev = self._safe_prev(current_reasoning)
            if not obj["summary"].strip():
                obj["summary"] = prev["summary"]
            if not obj["reasoning"]["topic"]:
                obj["reasoning"] = prev["reasoning"]

        # Ensure ≤100 words
        if _word_count(obj["summary"]) > 100:
            words = _WORD_RE.findall(obj["summary"])
            obj["summary"] = " ".join(words[:100])

        return obj


# ---------------- BACKWARD COMPAT API ----------------
def run(client, reason_prompt, refine_prompt, generation_params, source_text, current_reasoning, feedback=None):
    rf = ReasoningFlow(client, request_kwargs={
        "max_tokens": generation_params.get("max_new_tokens", 768),
        "temperature": generation_params.get("temperature", 0.2),
        "top_p": generation_params.get("top_p", 0.9),
    })

    result = rf.run_reason_or_refine(reason_prompt, refine_prompt, current_reasoning, source_text, feedback)

    # ✅ Always return JSON string (fix pipeline contract)
    return json.dumps(result, ensure_ascii=False)
