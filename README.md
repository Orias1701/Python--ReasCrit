# SUMMARIZER -- USING -- REASONING - CRITICAL

## Project Structure

```
SUMMARIZER
│
├── Assets/
│ ├── ex.exceptions.json
│ ├── ex.markers.json
│ └── ex.status.json
│
├── Config/
└── ModelLoader.py
```

## conda create -f cuda.yml

## GPU LLM Setup (Windows + WSL2 + Docker + CUDA + Llama.cpp)

### 1) Cài WSL2 - Ubuntu - Docker

```
wsl --install

dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

wsl --set-default-version 2
wsl --update

wsl --install -d Ubuntu
wsl --set-default Ubuntu

$installer = "DockerDesktopInstaller.exe"
Invoke-WebRequest -UseBasicParsing "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $installer

Start-Process -FilePath $installer -ArgumentList "install --quiet" -Wait
& "C:\Program Files\Docker\Docker\Docker Desktop.exe"

docker --version
docker-compose version

wsl --shutdown

sudo apt update && sudo apt upgrade -y
```

---

### 5) Cài NVIDIA Container Toolkit (trong Ubuntu)

sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker || sudo service docker restart

---

### 6) Test GPU trong Docker

<pre class="overflow-visible!" data-start="951" data-end="1036"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker run --</span><span>rm</span><span> --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
</span></span></code></div></div></pre>

✅ Nếu thấy bảng GPU → OK.

---

### 7) Tạo workspace

<pre class="overflow-visible!" data-start="1091" data-end="1138"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>mkdir</span><span> -p ~/llama-gpu
</span><span>cd</span><span> ~/llama-gpu
</span></span></code></div></div></pre>

---

### 8) Tạo Dockerfile

**`Dockerfile`**

<pre class="overflow-visible!" data-start="1184" data-end="1642"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-Dockerfile"><span>FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev git build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip setuptools wheel \
 && pip3 install \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    llama-cpp-python==0.3.2 \
    huggingface_hub datasets tqdm requests pandas
</span></code></div></div></pre>

---

### 9) Build Docker image

<pre class="overflow-visible!" data-start="1675" data-end="1714"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker build -t llama-gpu .
</span></span></code></div></div></pre>

---

### 10) Tạo thư mục chứa model

<pre class="overflow-visible!" data-start="1752" data-end="1791"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>mkdir</span><span> -p ~/llama-gpu/models
</span></span></code></div></div></pre>

*(Tự tải `.gguf` vào thư mục này sau)*

---

### 11) Chạy container GPU

<pre class="overflow-visible!" data-start="1865" data-end="1959"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker run -it --gpus all \
 -v /home/</span><span>$USER</span><span>/llama-gpu:/workspace \
 llama-gpu bash
</span></span></code></div></div></pre>

---

## ✅ Hoàn tất

Bạn đã có môi trường GPU để chạy LLM với `llama.cpp`.
