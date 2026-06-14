@echo off
cd /d "%~dp0"
set PYTHONPATH=.codex_deps;src
python -m uvicorn api:app --host 127.0.0.1 --port 8000
