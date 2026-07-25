@echo off
chcp 65001 >nul
title 置顶待办
python "%~dp0todo-app.py"
pause
