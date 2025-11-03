# Libraries/Flow_Critical.py
from typing import Dict, Any
import json, re
from . import Flow_Base
from . import Json_Parser

_REQUIRED_SCORES = ["factuality","clarity","logical_coherence","coverage","utility","consistency"]
parser = Json_Parser

class CriticalFlow(Flow_Base.FlowBase):

    def run_critic(
        self,
        critic_prompt: str,
        refine_prompt: str,
        source_text: str,
        reasoning_output: str,
        prev_result: Dict[str,Any] = None
    ) -> Dict[str, Any]:

        clean_reason = reasoning_output or ""

        try:
            obj = self.parse_first_json(clean_reason)
            current_summary = obj.get("summary","")
        except:
            current_summary = ""

        prev_scores = prev_result.get("scoring") if prev_result else {}
        prev_feedback = prev_result.get("feedback_text","") if prev_result else ""

        sys_prompt = refine_prompt if prev_result else critic_prompt
        feedback_part = (f"\n\n[PREVIOUS_SCORE]\n{json.dumps(prev_scores)}"
                        f"\n\n[PREVIOUS_FEEDBACK]\n{prev_feedback}") if prev_result else ""
        prompt = (
            f"{sys_prompt}"
            f"{feedback_part}"
            f"\n\n[REASONING_JSON]\n{clean_reason}"
            f"\n\n[CURRENT_SUMMARY]\n{current_summary}"
            f"\n\n[ORIGINAL]\n{source_text}"
        ).strip()

        if not current_summary.strip():
            return {
                "scoring": {k:1 for k in _REQUIRED_SCORES},
                "feedback_text": "Summary missing."
            }

        raw = self.call_llm(f"<|user|>\n{prompt}\n<|end|>\n<|assistant|>")
        parsed = parser.sanitize_and_parse_critic(raw)

        if parsed is None:
            return {
                "error":"JSON_PARSE_FAIL",
                "raw_response": raw,
                "scoring":{k:2 for k in _REQUIRED_SCORES},
                "feedback_text":"Parser fallback: include one numeric/date detail and rewrite concisely."
            }

        result = self._repair_schema(parsed)
        return result

    def _repair_schema(self, obj: Dict[str,Any]) -> Dict[str,Any]:
        out = {"scoring":{}, "feedback_text":""}

        scoring = obj.get("scoring",{})
        if not isinstance(scoring,dict):
            scoring = {}

        for k in _REQUIRED_SCORES:
            v = scoring.get(k)
            scoring[k] = v if isinstance(v,(int,float)) else 1
        out["scoring"] = scoring

        fb = obj.get("feedback_text","").strip()
        if not fb:
            fb = "Provide one missing quantitative detail and one actionable rewrite instruction."
        else:
            fb = re.sub(r"You are .*", "", fb, flags=re.I)
        out["feedback_text"] = fb.strip()

        return out


def run(client, critic_prompt, refine_prompt, generation_params, source_text, reasoning_output, prev_result=None):

    cf = CriticalFlow(client, request_kwargs={
        "max_tokens":1536, "temperature":0, "top_p":1.0
    })
    return cf.run_critic(critic_prompt, refine_prompt, source_text, reasoning_output, prev_result)