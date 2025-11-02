# Libraries/Flow_Reasoning.py
from typing import Dict, Any, Optional
import re

_ALLOWED_CHARS = r"a-zA-Z0-9\.\,\:\;\(\)\-\?\!\s"

_MD_BOLD = re.compile(r"\*\*(.*?)\*\*")
_BULLET = re.compile(r"^[\-\*\+]\s*", flags=re.M)
_CTRL = re.compile(r"[\u200B-\u200D\uFEFF]")
_NOT_ALLOWED = re.compile(fr"[^{_ALLOWED_CHARS}]", flags=re.UNICODE)

def sanitize_reasoning(text: str) -> str:
    """
    Loại bỏ markdown và ký tự có thể gây nhiễu grammar critic.
    Không đổi nội dung ngữ nghĩa, chỉ dọn định dạng.
    """
    if not isinstance(text, str):
        return text

    s = text
    s = _MD_BOLD.sub(r"\1", s)
    s = _BULLET.sub("", s) 
    s = _CTRL.sub("", s)
    s = s.replace("—", "-").replace("–", "-")
    s = _NOT_ALLOWED.sub("", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def clean(text):
    if not isinstance(text, str): return text
    text = text.replace("—","-").replace("–","-")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def run(client, reason_prompt, refine_prompt, generation_params, current_reasoning, text, feedback=None):

    if client is None:
        return None

    if feedback:
        content = (
            f"{refine_prompt}\n"
            "[PREVIOUS OUTPUT]\n"
            f"{current_reasoning}\n\n"
            "[FEEDBACK]\n"
            f"{feedback}\n\n"
            "[ORIGINAL DOCUMENT]\n"
            f"{text}\n"
        )

    else:
        content = (
            f"{reason_prompt}\n"
            "[ORIGINAL DOCUMENT]\n"
            f"{text}\n"
        )

    prompt = f"<|user|>\n{content}\n<|end|>\n<|assistant|>"

    try:
        out = client(
            prompt,
            max_tokens=generation_params.get("max_new_tokens", 512),
            temperature=generation_params.get("temperature", 0.2),
            top_p=generation_params.get("top_p", 0.9),
            stop=["<|end|>", "<|assistant|>"]
        )["choices"][0].get("text","")

        out = clean(out)
        out = sanitize_reasoning(out)
        return out

    except Exception as e:
        print(f"❌ Reason error: {e}")
        raise SystemExit(1)
