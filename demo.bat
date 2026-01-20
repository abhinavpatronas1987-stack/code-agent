@echo off
title Code Agent - Demo
cd /d D:\code-agent
call .venv\Scripts\activate.bat
python scripts\run_demo.py
pause
