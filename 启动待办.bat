@echo off
chcp 65001 >nul
title 置顶待办

:: 尝试多个路径查找 Python
set PYTHON_CMD=
for %%c in (
  "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%ProgramFiles%\Python313\python.exe"
  "%ProgramFiles%\Python312\python.exe"
  "python.exe"
) do (
  if exist %%c set PYTHON_CMD=%%c&goto :FOUND
)

echo [错误] 未找到 Python，请安装 Python 3.12+
echo 下载: https://www.python.org/downloads/
pause
exit /b 1

:FOUND
%PYTHON_CMD% "%~dp0todo-app.py"
pause
