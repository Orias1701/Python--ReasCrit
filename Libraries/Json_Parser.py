# -*- coding: utf-8 -*-
import re
import json

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

# Map text → number
NUM_MAP = {
    "one":1,"two":2,"three":3,"four":4,"five":5,
    "1":1,"2":2,"3":3,"4":4,"5":5
}


# -------------------------------------------------
# 1) Check subsequence key match (f-e-e-d-b-a-c-k theo thứ tự)
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

    # text number
    if v in NUM_MAP: 
        return NUM_MAP[v]

    # digit 1-5
    m = re.match(r"^([1-5])$", v)
    if m:
        return int(m.group(1))

    # không hợp lệ
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

    # fallback: vùng có scoring
    pos = text.lower().find("scoring")
    if pos != -1:
        tail = text[pos:]
        return "{" + tail + "}"

    return "{}"


# -------------------------------------------------
# 5) Rút gọn ký tự rác, chuẩn hóa dấu cách
# -------------------------------------------------
def collapse_symbols(s):
    # collapse ngoặc/dấu lại còn 1 cái
    s = re.sub(r'([{}[\]:,])\1+', r'\1', s)

    # bỏ ký tự rác giữ chỉ số, chữ, {}[]:,. và khoảng trắng
    s = re.sub(r'[^0-9A-Za-z{}[\]:,.\s"]', ' ', s)

    # collapse space
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


# -------------------------------------------------
# 6) Cắt feedback theo trigger rác
# -------------------------------------------------
def cut_feedback(text):
    stops = ["you are", "chatgpt", "assistant", "model", "```"]
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
    # bước 1: lấy vùng nghi là JSON
    chunk = extract_json_like(raw)
    # print(f"Extracted chunk: {chunk}\n\n")
    
    # bước 2: chuẩn hóa ký tự rác
    chunk = collapse_symbols(chunk)
    # print(f"Collapsed chunk: {chunk}\n\n")

    # ✅ Try extract feedback fast, but DO NOT return yet
    m_fb = re.search(r'"feedback[_\s]*text"\s*:\s*"([^"]+)"', chunk, re.IGNORECASE)
    fast_feedback = m_fb.group(1) if m_fb else None
    if fast_feedback:
        fast_feedback = cut_feedback(fast_feedback)

    # bước 3: tách token
    tokens = re.split(r'([{,}])', chunk)
    # print(f"Tokens: {tokens}\n\n")
    
    scoring = {}
    feedback = ""
    current_key = None
    in_feedback = False

    for tk in tokens:
        tk = tk.strip()
        if not tk:
            continue

        # trường hợp: key:value chung dòng
        if ":" in tk:
            parts = tk.split(":",1)
            k = parts[0].strip().replace('"','').replace("'", "")
            v = parts[1].strip().rstrip(",")

            nk = normalize_key(k)
            if nk:
                current_key = nk

                # ✅ Nếu là feedback_text → cố lấy toàn bộ chuỗi "..."
                if nk == "feedback_text":
                    in_feedback = True

                    # nếu value bắt đầu bằng quote → cố lấy full string giữa "..."
                    if v.startswith('"'):
                        m = re.search(r'"([^"]+)"', chunk)
                        if m:
                            feedback = m.group(1)
                            in_feedback = False
                            current_key = None
                            continue
                        else:
                            # nếu chưa đóng quote trong token này → thu thập tiếp
                            feedback += " " + v.lstrip('"')
                            continue

                # ✅ Nếu là số và không phải feedback
                nv = normalize_value(v)
                if nk != "feedback_text" and nv is not None:
                    scoring[nk] = nv
                elif nk == "feedback_text":
                    feedback += " " + v

                continue


        # thu thập feedback
        if in_feedback:
            # bỏ ngoặc nhưng giữ text
            if tk not in "{}[]":
                # loại dấu , đơn lẻ nhưng giữ dấu phẩy trong câu
                if tk != ",":
                    feedback += " " + tk
            continue


        # xử lý value cách dòng
        if current_key and current_key != "feedback_text":
            nv = normalize_value(tk)
            if nv is not None:
                scoring[current_key] = nv
                current_key = None

    # print(f"Scoring dict: {scoring}\n")
    # print(f"Raw feedback: {feedback}\n\n")
    
    # finalize feedback
    feedback = cut_feedback(feedback.strip())
    if not feedback and fast_feedback:
        feedback = fast_feedback


    # fill thiếu score = 3
    out = {"scoring":{}, "feedback_text":feedback}
    for k in KEY_SIG:
        if k == "feedback_text": 
            continue
        out["scoring"][k] = scoring.get(k, 3)

    return out
