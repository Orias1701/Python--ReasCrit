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

sudo apt update && sudo apt upgrade -y
```

---



### 2) Chạy llama_run.py
