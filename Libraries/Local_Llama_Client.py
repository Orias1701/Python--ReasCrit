"""
Local Llama HTTP Client Wrapper

Sử dụng để giao tiếp với Llama.cpp server qua REST API.
Không phụ thuộc llama_cpp package nội bộ.
"""

import requests
import time
import json
from typing import Optional, List, Any, Dict

class LocalLlamaClient:
    def __init__(self, 
                 host: str = "http://localhost:8080", 
                 timeout: int = 270,  # Timeout cho request (dài)
                 retry: int = 3, 
                 wait_timeout: int = 300): # Timeout cho việc chờ server (5 phút)
        
        self.host = host.rstrip("/")
        self.timeout = timeout 
        self.health_timeout = 5 # Timeout cho health check (ngắn)
        self.retry = retry
        
        # Ngay khi client được tạo, nó sẽ chờ cho đến khi server sẵn sàng.
        self.wait_for_server_ready(wait_timeout) 

    def wait_for_server_ready(self, wait_timeout: int):
        """
        Hỏi thăm (poll) endpoint /health cho đến khi server "ready"
        hoặc hết thời gian chờ (wait_timeout).
        """
        start_time = time.time()
        url = f"{self.host}/health"
        
        print(f"⏳ Đang kiểm tra Llama server tại {self.host}...")
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > wait_timeout:
                print(f"❌ Server không sẵn sàng sau {wait_timeout} giây.")
                raise TimeoutError(f"Server tại {self.host} không sẵn sàng sau {wait_timeout}s.")

            try:
                res = requests.get(url, timeout=self.health_timeout)
                data = res.json()
                status = data.get("status")

                # --- SỬA LỖI Ở ĐÂY ---
                # Server 'llama.cpp' trả về "ok" khi sẵn sàng, không phải "ready".
                if status == "ok":
                # ---------------------
                    print(f"✅ Server đã tải model và sẵn sàng (status: {status}).")
                    break # Thoát khỏi vòng lặp, server đã sẵn sàng
                else:
                    # Bất kỳ status nào khác: "loading", "busy", None, v.v.
                    print(f"⏳ Server đang bận (status: {status}). Thử lại sau 5s...")

            except requests.exceptions.ConnectionError:
                # Server (Docker) chưa kịp chạy
                print(f"⏳ Đang chờ kết nối đến server tại {self.host}... Thử lại sau 5s...")
            
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                # Các lỗi request khác (như timeout, 404, or invalid JSON)
                print(f"⚠️ Lỗi health check: {e}. Thử lại sau 5s...")

            time.sleep(5) # Chờ 5 giây trước khi hỏi thăm lại

    # ... (Phần còn lại của file _post và __call__ giữ nguyên như cũ) ...

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Gửi yêu cầu POST và xử lý retry."""
        url = f"{self.host}{endpoint}"

        for attempt in range(self.retry):
            try:
                res = requests.post(url, json=payload, timeout=self.timeout) 

                if res.status_code == 200:
                    return res.json()

                print(f"[LLAMA API WARNING] HTTP {res.status_code}: {res.text}")
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"[LLAMA API ERROR] {str(e)}")
                time.sleep(1)

        return {"error": "LLAMA_REQUEST_FAILED"}

    def __call__(self,
                 prompt: str,
                 max_tokens: int = 512,
                 temperature: float = 0.7,
                 top_p: float = 0.9,
                 stop: Optional[List[str]] = None,
                 grammar: Optional[str] = None,
                 json_mode: bool = False) -> Dict[str, Any]:
        
        payload = {
            "prompt": prompt,
            "stream": False,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

        if stop:
            payload["stop"] = stop
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        elif grammar:
            payload["grammar"] = grammar
            
        data = self._post("/completion", payload)

        if "error" in data:
            return {"choices": [{"text": f"[LLAMA_ERROR] {data['error']}"}]}
        
        return {
            "choices": [
                {
                    "text": data.get("content", "")
                }
            ]
        }