@echo off
cd /d "%~dp0"
set PYTHONPATH=.codex_deps;src
python -m streamlit run app.py --global.developmentMode false --server.port 8501 --server.headless true
