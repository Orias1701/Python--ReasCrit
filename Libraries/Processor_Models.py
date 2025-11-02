# Libraries/Processor_Models.py

from pathlib import Path
from Libraries.Local_Llama_Client import LocalLlamaClient

def llm_initialize(config: dict, llama_cpp_params: dict, base_models_dir: Path):
    """
    Initialize Local Llama HTTP Client instead of loading GGUF locally.
    """
    print("🔗 Using Local Llama HTTP server...")
    
    llm_client = LocalLlamaClient("http://localhost:8080")
    
    # Return (reasoner, critic) for compatibility with pipeline
    return llm_client, llm_client
