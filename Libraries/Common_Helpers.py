# Libraries/Common_Helpers.py

import json
import regex
from statistics import mean
from typing import Dict, Any

def json_parse(text: str) -> Dict[str, Any]:
    """
    Parse một chuỗi JSON sạch.
    """
    text = text.strip()
    try:
        # Chỉ cần parse trực tiếp.
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Không parse được JSON (lỗi cú pháp): {e}\n{text}")

WEIGHTS = {
    "factuality": 0.30,
    "coverage": 0.20,
    "logical_coherence": 0.15,
    "clarity": 0.15,
    "consistency": 0.10,
    "utility": 0.10
}

def average_score(critical_output: Dict[str, Any]) -> float:
    """
    Tính điểm trung bình. Ưu tiên công thức trọng số.
    Nếu thiếu dữ liệu hoặc không parse được -> fallback sang mean().
    """
    scoring = critical_output.get("scoring")

    if not scoring or not isinstance(scoring, dict):
        if "error" not in critical_output:
            print("⚠️ Lỗi: output không có 'scoring'. Trả về 0.0")
        return 0.0

    # --- 1) thử tính theo trọng số ---
    try:
        weighted_sum = 0.0
        valid = True

        for metric, weight in WEIGHTS.items():
            if metric not in scoring:
                valid = False
                break
            val = scoring[metric]

            # convert -> float
            try:
                val = float(val)
            except:
                valid = False
                break

            weighted_sum += val * weight

        if valid:
            return round(weighted_sum, 4)

    except Exception as e:
        print(f"⚠️ Lỗi khi tính theo trọng số: {e}")

    # --- 2) fallback: dùng mean() như cách cũ ---
    fallback_values = []
    for v in scoring.values():
        try:
            fallback_values.append(float(v))
        except:
            continue

    if fallback_values:
        return round(mean(fallback_values), 4)

    print("⚠️ Không lấy được số hợp lệ từ scoring. Trả về 0.0")
    return 0.0