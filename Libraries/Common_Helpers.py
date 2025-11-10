# Libraries/Common_Helpers.py

from collections import OrderedDict
from typing import OrderedDict as OrderedDictType
import json
import os
from pathlib import Path
import regex
from statistics import mean
from typing import Dict, Any, List

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

def _get_sort_key(key_str: str) -> int:
    try:
        num_str = key_str.split('_')[-1]
        return int(num_str)
    except (ValueError, IndexError):
        return -1     
    
from collections import OrderedDict
from typing import OrderedDict as OrderedDictType, Dict, Any, List

def stage2_sort_and_count(cleaned: OrderedDictType[str, List[Dict[str, Any]]]) -> OrderedDictType[str, OrderedDict]:
    """
    - Giữ nguyên toàn bộ rounds (bao gồm round 0).
    - Tính 'reason_*' bằng chênh lệch round 1 và round 0 (nếu tồn tại cả hai).
    - Tính 'critic_*' bằng chênh lệch giữa các round >= 1.
    """
    result: OrderedDictType[str, OrderedDict] = OrderedDict()

    for key, rounds in cleaned.items():
        if not isinstance(rounds, list):
            result[key] = OrderedDict({
                "rounds": [],
                "stats": OrderedDict({
                    "reason_success_count": 0, "reason_stable_count": 0, "reason_fail_count": 0,
                    "critic_success_count": 0, "critic_stable_count": 0, "critic_fail_count": 0
                })
            })
            continue

        # --- Sắp xếp theo thứ tự thời gian (round tăng dần) ---
        all_rounds = sorted(rounds, key=lambda x: (x.get("round", -1), x.get("average_score", 0.0)))

        # --- Chuẩn bị tập eval >=1 để tính critic_* ---
        eval_rounds = [r for r in all_rounds if r.get("round", 0) >= 1]

        # --- Tính critic_* ---
        critic_success = critic_stable = critic_fail = 0
        for i in range(1, len(eval_rounds)):
            prev = float(eval_rounds[i - 1].get("average_score", 0.0))
            curr = float(eval_rounds[i].get("average_score", 0.0))
            diff = curr - prev
            if diff >= 0.1:
                critic_success += 1
            elif 0 <= diff < 0.1:
                critic_stable += 1
            else:
                critic_fail += 1

        # --- Tính reason_* (so sánh round 1 với round 0 nếu có) ---
        reason_success = reason_stable = reason_fail = 0
        round0 = next((r for r in all_rounds if r.get("round") == 0), None)
        round1 = next((r for r in all_rounds if r.get("round") == 1), None)

        if round0 and round1:
            diff = float(round1.get("average_score", 0.0)) - float(round0.get("average_score", 0.0))
            if diff >= 0.1:
                reason_success += 1
            elif 0 <= diff < 0.1:
                reason_stable += 1
            else:
                reason_fail += 1

        # --- Ghi kết quả ---
        result[key] = OrderedDict({
            "rounds": all_rounds,
            "stats": OrderedDict({
                "reason_success_count": reason_success,
                "reason_stable_count": reason_stable,
                "reason_fail_count": reason_fail,
                "critic_success_count": critic_success,
                "critic_stable_count": critic_stable,
                "critic_fail_count": critic_fail
            })
        })

    return result


def update_json_dict(key: str, data: Any, path: Path, indent: int = 2):
    dir_path = path.parent
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    history_dict: Dict[str, Any] = {}
    if path.exists() and path.stat().st_size > 0:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                history_dict = json.load(f)
            
            if not isinstance(history_dict, dict):
                print(f"⚠️ Cảnh báo: {path} không chứa Dictionary. Sẽ ghi đè.")
                history_dict = {}
        except json.JSONDecodeError:
            history_dict = {}

    # >>> THÊM MỚI — TỰ ĐỘNG CHUẨN HÓA DỮ LIỆU
    try:
        # Nếu data là list (tức các rounds/iterations)
        if isinstance(data, list):
            from collections import OrderedDict
            # Bao lại để khớp đầu vào cho stage2_sort_and_count
            wrapped = OrderedDict({key: data})
            # Gọi hàm thống kê stage2
            data = stage2_sort_and_count(wrapped)[key]
    except Exception as e:
        print(f"⚠️ Không thể chuẩn hóa dữ liệu {key}: {e}")
    # <<< KẾT THÚC PHẦN THÊM MỚI

    history_dict[key] = data

    try:
        sorted_keys = sorted(history_dict.keys(), key=_get_sort_key)
        sorted_dict = {k: history_dict[k] for k in sorted_keys}
    except Exception as e:
        print(f"⚠️ Cảnh báo: Không thể sắp xếp JSON keys: {e}. Sẽ ghi không sắp xếp.")
        sorted_dict = history_dict

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(sorted_dict, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Lỗi khi ghi {path}: {e}")
