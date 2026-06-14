@echo off
cd /d "%~dp0"
set PYTHONPATH=.codex_deps;src
set MPLCONFIGDIR=.tmp\matplotlib
python -m unittest discover -s tests -v
