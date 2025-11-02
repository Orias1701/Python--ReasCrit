# Libraries/Flow_Critical.py
from typing import Dict, Any
from Libraries import Common_Helpers as helpers
import re, sys

from Libraries.exceptions import PipelineAbortSample

def clean_reasoning_block(text: str) -> str:
    if not isinstance(text, str): return ""
    text = re.sub(r"[\u0000-\u001F\u007F-\u009F]", "", text)
    text = re.sub(r"[^\w\s\.,;:\-\(\)!?/'\"]", "", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_all_json(text: str):
    blocks = []
    start = None
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                blocks.append(text[start:i+1])
                start = None
    return blocks

def try_parse_json_blocks(raw: str):
    """Try parse all JSON blocks, return last valid."""
    blocks = extract_all_json(raw)
    valid = None
    for block in blocks:
        try:
            valid = helpers.json_parse(block)
        except:
            continue
    return valid

def fail_exit(msg, raw=None):
    print(f"\n❌ SAMPLE SKIPPED — {msg}")
    if raw:
        print("\n--- RAW OUTPUT ---\n", raw)
    raise PipelineAbortSample(msg)

def run(client: Any, critic_prompt: str, source_text: str, reasoning_output: str) -> Dict[str, Any]:

    if client is None: fail_exit("CRITIC_CLIENT missing")
    clean_reason = clean_reasoning_block(reasoning_output or "")

    prompt = f"""
{critic_prompt}

[REASONING]
{clean_reason}

[ORIGINAL]
{source_text}
""".strip()

    full_prompt = f"<|user|>\n{prompt}\n<|end|>\n<|assistant|>"

    # -------- First Attempt --------
    try:
        res = client(
            full_prompt,
            max_tokens=800,
            temperature=0,
            top_p=1.0,
            json_mode=True
        )
    except Exception as e:
        fail_exit(f"Runtime LLM error: {e}")

    raw = (res["choices"][0].get("text","") or "").strip()
    parsed = try_parse_json_blocks(raw)

    if parsed is not None:
        return parsed

    # If we reach here → model gave broken JSON. Retry forcing JSON ONLY.
    print("⚠️ Retrying JSON extraction once...")

    retry_prompt = f"<|user|>\nReturn ONLY JSON valid:\n{prompt}\n<|end|>\n<|assistant|>"

    try:
        res2 = client(
            retry_prompt,
            max_tokens=800,
            temperature=0,
            top_p=1.0,
            json_mode=True
        )
        raw2 = (res2["choices"][0].get("text","") or "").strip()
        parsed2 = try_parse_json_blocks(raw2)

        if parsed2 is not None:
            return parsed2
        else:
            fail_exit(...)

    except Exception as e:
        fail_exit(f"Retry LLM error: {e}", raw)
