import json
import os, subprocess, time, sys
from pathlib import Path

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

CONFIG = BASE/"Config"/"config.json"
with open(CONFIG, "r", encoding="utf-8") as f:
    cfg = json.load(f)


# CONFIG ======================================================
MODEL_DIR = f"{BASE}/{cfg['paths']['local_model_dir']}/{cfg['models']['reasoning_model']['publisher']}/{cfg['models']['reasoning_model']['model_type']}"
MODEL_FILE = cfg['models']['reasoning_model']['hf_filename']
PORT = "8080"
CONTAINER_NAME = "local-llama-gpu"
IMAGE = "ghcr.io/ggerganov/llama.cpp:server-cuda"
# ============================================================

# Resolve model path
model_path = Path(MODEL_DIR) / MODEL_FILE

if not model_path.exists():
    print(f"❌ Model not found: {model_path}")
    sys.exit(1)

print(f"✅ Model found: {model_path}")

# Ensure Docker Desktop is running
def is_docker_running():
    try:
        out = subprocess.check_output("docker info", shell=True, stderr=subprocess.STDOUT)
        return b"Server Version" in out
    except:
        return False

def start_docker_desktop():
    print("🚀 Starting Docker Desktop...")
    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if not Path(docker_path).exists():
        print("❌ Docker Desktop not found. Update path!")
        sys.exit(1)
    subprocess.Popen(f'"{docker_path}"')
    time.sleep(5)

# Start Docker if needed
if not is_docker_running():
    start_docker_desktop()
    while not is_docker_running():
        print("⏳ Waiting for Docker to start...")
        time.sleep(3)

print("✅ Docker is ready")

# Kill previous container if exists
print("🛑 Removing previous container (if any)")
os.system(f"docker rm -f {CONTAINER_NAME} >nul 2>&1")

# Start llama server
cmd = f'docker run --gpus all --name {CONTAINER_NAME} -p {PORT}:8080 -v "{MODEL_DIR}:/models" {IMAGE} --model /models/{MODEL_FILE} --ctx-size 4096'

print("🚀 Starting Llama server...")
print(cmd)

subprocess.Popen(cmd, shell=True)

time.sleep(3)
print(f"""
✅ Llama server started!
URL: http://localhost:{PORT}
Model: {MODEL_FILE}
Press Ctrl+C to stop.
""")
