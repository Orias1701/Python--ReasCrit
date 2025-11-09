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
    Phiên bản robust — parse thủ công hoàn toàn (không dùng parse_first_json).
    """

    def _parse_best_json(self, raw: str) -> Dict[str, Any]:
        """
        Dò JSON thủ công, khôi phục và load an toàn, cho phép JSON chỉ có 'summary'.
        """
        if not raw or not isinstance(raw, str):
            return {"reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""}, "summary": ""}

        text = raw.strip()
        text = re.sub(r"[\u0000-\u001F]+", " ", text)
        text = text.replace("’", "'").replace("“", '"').replace("”", '"')
        text = text.replace("\\'", "'").replace('\\"', '"')

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        text = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)\s*:',
                      lambda m: m.group(1) + f'"{m.group(2)}":', text)

        text = re.sub(r":\s*'([^']*)'", lambda m: ':"{}"'.format(m.group(1).replace('"', '\\"')), text)
        text = re.sub(r"'\s*,", lambda m: '",', text)
        text = re.sub(r",\s*([}\]])", r"\1", text)

        try:
            obj = json.loads(text)
        except Exception:
            summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', text)
            summary = summary_match.group(1).strip() if summary_match else ""
            obj = {"reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""}, "summary": summary}

        if isinstance(obj, dict) and "summary" in obj and "reasoning" not in obj:
            obj["reasoning"] = {"topic": "", "key_ideas": "", "filtered_ideas": ""}

        return self._ensure_fields(obj)

    def _sanitize_feedback_text(self, fb: Optional[str]) -> str:
        if not fb:
            return ""
        s = fb.strip()
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
            return {"reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""}, "summary": ""}
        try:
            obj = json.loads(prev_text)
            self._ensure_fields(obj)
            return obj
        except:
            return {"reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""}, "summary": ""}

    def run_reason_or_refine(
        self,
        reason_prompt: str,
        refine_prompt: str,
        current_reasoning: Optional[str],
        source_text: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:

        fb_clean = self._sanitize_feedback_text(feedback)
        system_prompt = refine_prompt if fb_clean else reason_prompt
        sub_prompt = (
            f"\n\nTóm tắt trước đó:\n\n{current_reasoning}"
            f"\n\nPhản hồi:\n\n{fb_clean}"
        ).strip() if fb_clean else ""
        
        prompt = f"{system_prompt}{sub_prompt}\n\nVăn bản gốc:\n\n{source_text}".strip()

        # 🔁 Gọi LLM và parse thủ công — retry tối đa 3 lần
        attempt = 0
        obj = None
        while attempt < 3:
            attempt += 1
            raw = self.call_llm(f"<|user|>\n{prompt}\n<|end|>\n<|assistant|>")
            obj = self._parse_best_json(raw)
            if isinstance(obj, dict) and obj.get("summary", "").strip():
                break
            print(f"⚠️ Lần {attempt}: parse thất bại, thử lại...")

        if not obj or not obj.get("summary", "").strip():
            print("❌ Quá 3 lần vẫn lỗi → dùng mặc định.")
            obj = {"reasoning": {"topic": "", "key_ideas": "", "filtered_ideas": ""}, "summary": ""}

        if fb_clean:
            prev = self._safe_prev(current_reasoning)
            if not obj["summary"].strip():
                obj["summary"] = prev["summary"]
            if not obj["reasoning"]["topic"]:
                obj["reasoning"] = prev["reasoning"]

        if _word_count(obj["summary"]) > 100:
            words = _WORD_RE.findall(obj["summary"])
            obj["summary"] = " ".join(words[:100])

        return obj


# ---------------- BACKWARD COMPAT API ----------------
def run(client, reason_prompt, refine_prompt, generation_params, source_text, current_reasoning, feedback=None):
    rf = ReasoningFlow(client, request_kwargs={
        "max_tokens": generation_params['max_new_tokens'],
        "temperature": generation_params['temperature'],
        "top_p": generation_params['top_p'],
    })
    result = rf.run_reason_or_refine(reason_prompt, refine_prompt, current_reasoning, source_text, feedback)
    return json.dumps(result, ensure_ascii=False)
