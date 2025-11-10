# Libraries/Processor_Datasets.py

from pathlib import Path
from typing import Optional, Dict, Any
from datasets import load_dataset, load_from_disk, Dataset

# ==============================

def load_from_disk_internal(local_path: Path) -> Optional[Dataset]:
    """
    Tải dataset từ đường dẫn cục bộ. Trả về None nếu lỗi.
    """
    try:
        return load_from_disk(str(local_path))
    except Exception:
        return None

def download_and_save_internal(dataset_config: Dict[str, Any], local_path: Path) -> Optional[Dataset]:
    """
    Tải dataset từ Hugging Face và lưu vào đường dẫn. Trả về None nếu lỗi.
    """
    try:
        dataset_split = dataset_config.get("split", "train")
        dataset = load_dataset(dataset_config['name'], split=dataset_split)
        dataset.save_to_disk(str(local_path))
        return dataset
    except Exception:
        return None

def analyze_dataset_internal(dataset: Dataset) -> Dict[str, Any]:
    """
    Phân tích dataset và trả về một dict chứa thông tin.
    (Đã đơn giản hóa)
    """
    if not dataset:
        return {"error": "Dataset rỗng"}
    
    try:
        # Chỉ xác nhận các trường bạn quan tâm
        features = str(dataset.features)
        has_article = "article" in dataset.features
        has_summary = "summary" in dataset.features
        
        return {
            "count": len(dataset),
            "features": features,
            "has_article": has_article,
            "has_summary": has_summary
        }
    except Exception as e:
        return {"error": f"Lỗi khi phân tích dataset: {e}"}

def get_content_by_index_internal(dataset: Dataset, index: int) -> Optional[str]:
    """
    Lấy 'article' từ dataset tại index cụ thể.
    Trả về None nếu lỗi hoặc không có 'article'.
    """
    if dataset is None:
        return None
    try:
        # Kiểm tra index có hợp lệ không
        if index < 0 or index >= len(dataset):
            return None 
        
        sample = dataset[index]
        content = sample.get("article") # Chỉ lấy 'article'
        
        if not content:
            return None # Mẫu bị rỗng

        return content
    except Exception:
        return None