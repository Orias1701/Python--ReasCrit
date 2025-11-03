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

def average_score(critical_output: Dict[str, Any]) -> float:
    """
    Tính điểm trung bình từ output JSON của critical model.
    """
    scoring_dict = critical_output.get("scoring")
    if not scoring_dict or not isinstance(scoring_dict, dict):
        if "error" not in critical_output:
             print("⚠️ Lỗi: Không tìm thấy key 'scoring' trong output của Critical.")
        return 0.0
    
    scores = [
        float(s) for s in scoring_dict.values() 
        if isinstance(s, (int, float, str)) and str(s).replace('.','',1).isdigit()
    ]
    return mean(scores) if scores else 0.0