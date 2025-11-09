import re
import json
import random

def score_dict(_REQUIRED_SCORES) -> dict:
    return {
        k: random.choices([3, 4, 5], weights=[40, 40, 20])[0]
        for k in _REQUIRED_SCORES
    }


# Các key chuẩn
KEY_SIG = {
    "factuality": "fact",
    "clarity": "clar",
    "logical_coherence": "coher",
    "coverage": "cover",
    "utility": "util",
    "consistency": "consis",
    "feedback_text": "feedback"
}

NUM_MAP = {
    "một":1,"hai":2,"ba":3,"bốn":4,"năm":5,
    "one":1,"two":2,"three":3,"four":4,"five":5,
    "1":1,"2":2,"3":3,"4":4,"5":5
}


# -------------------------------------------------
# 1) Check subsequence key match
# -------------------------------------------------
def is_subsequence(pattern, text):
    it = iter(text.lower())
    return all(c in it for c in pattern.lower())


# -------------------------------------------------
# 2) Chuẩn hóa key JSON
# -------------------------------------------------
def normalize_key(k):
    k = k.lower().strip().replace('"','').replace("'", "")
    for clean, sig in KEY_SIG.items():
        if is_subsequence(sig, k):
            return clean
    return None


# -------------------------------------------------
# 3) Chuẩn hóa giá trị
# -------------------------------------------------
def normalize_value(v):
    v = v.strip().lower().replace('"','').replace("'", "")

    if v in NUM_MAP: 
        return NUM_MAP[v]

    m = re.match(r"^([1-5])$", v)
    if m:
        return int(m.group(1))

    return None


# -------------------------------------------------
# 4) Lấy phần JSON thô bằng đếm ngoặc
# -------------------------------------------------
def extract_json_like(text):
    stack = 0
    start = None

    for i,ch in enumerate(text):
        if ch == "{":
            if stack == 0:
                start = i
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0 and start is not None:
                return text[start:i+1]

    pos = text.lower().find("scoring")
    if pos != -1:
        tail = text[pos:]
        return "{" + tail + "}"

    return "{}"


# -------------------------------------------------
# 5) Rút gọn ký tự rác, chuẩn hóa dấu cách
# -------------------------------------------------
def collapse_symbols(s):
    s = re.sub(r'([{}[\]:,])\1+', r'\1', s)
    s = re.sub(r'[^0-9A-Za-zÀ-ỿà-ỹ{}[\]:,.\s"]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


# -------------------------------------------------
# 6) Cắt feedback theo trigger rác
# -------------------------------------------------
def cut_feedback(text):
    stops = ["\n\n", "```"]
    lower = text.lower()
    cut = len(text)

    for w in stops:
        p = lower.find(w)
        if p != -1:
            cut = min(cut, p)

    text = text[:cut].strip()
    text = text.rstrip(',.;: ')
    return text


# -------------------------------------------------
# 7) Hàm chính: sanitize & parse
# -------------------------------------------------
def sanitize_and_parse_critic(raw):
    
    chunk = extract_json_like(raw)
    chunk = collapse_symbols(chunk)

    m_fb = re.search(r'"feedback[_\s]*text"\s*:\s*"([^"]+)"', chunk, re.IGNORECASE)
    fast_feedback = m_fb.group(1) if m_fb else None
    if fast_feedback:
        fast_feedback = cut_feedback(fast_feedback)

    tokens = re.split(r'([{,}])', chunk)
    
    scoring = {}
    feedback = ""
    current_key = None
    in_feedback = False

    for tk in tokens:
        tk = tk.strip()
        if not tk:
            continue

        if ":" in tk:
            parts = tk.split(":",1)
            k = parts[0].strip().replace('"','').replace("'", "")
            v = parts[1].strip().rstrip(",")

            nk = normalize_key(k)
            if nk:
                current_key = nk

                if nk == "feedback_text":
                    in_feedback = True

                    if v.startswith('"'):
                        m = re.search(r'"([^"]+)"', chunk)
                        if m:
                            feedback = m.group(1)
                            in_feedback = False
                            current_key = None
                            continue
                        else:
                            feedback += " " + v.lstrip('"')
                            continue

                nv = normalize_value(v)
                if nk != "feedback_text" and nv is not None:
                    scoring[nk] = nv
                elif nk == "feedback_text":
                    feedback += " " + v

                continue

        if in_feedback:
            if tk not in "{}[]":
                if tk != ",":
                    feedback += " " + tk
            continue

        if current_key and current_key != "feedback_text":
            nv = normalize_value(tk)
            if nv is not None:
                scoring[current_key] = nv
                current_key = None

    feedback = cut_feedback(feedback.strip())
    if not feedback and fast_feedback:
        feedback = fast_feedback

    out = {"scoring":{}, "feedback_text":feedback}
    for k in KEY_SIG:
        if k == "feedback_text": 
            continue
        out["scoring"][k] = scoring.get(k, 3)

    return out
