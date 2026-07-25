@echo off
chcp 65001 >nul
title 置顶待办

:: ── 自动查找 Python ──
set PYTHON_CMD=

:: 1) PATH 中的 python (最优先)
where python >nul 2>&1 && set PYTHON_CMD=python&goto :FOUND

:: 2) 注册表查找 (用户安装)
for %%v in (3.14 3.13 3.12 3.11 3.10) do (
  for /f "tokens=2*" %%A in (
    'reg query "HKCU\SOFTWARE\Python\PythonCore\%%v\InstallPath" /ve 2^>nul ^| findstr /i "REG_SZ"'
  ) do if exist "%%B\python.exe" set PYTHON_CMD="%%B\python.exe"&goto :FOUND
)

:: 3) 注册表查找 (系统安装)
for %%v in (3.14 3.13 3.12 3.11 3.10) do (
  for /f "tokens=2*" %%A in (
    'reg query "HKLM\SOFTWARE\Python\PythonCore\%%v\InstallPath" /ve 2^>nul ^| findstr /i "REG_SZ"'
  ) do if exist "%%B\python.exe" set PYTHON_CMD="%%B\python.exe"&goto :FOUND
)

:: 4) 常见安装路径
for %%p in (
  "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%ProgramFiles%\Python313\python.exe"
  "%ProgramFiles%\Python312\python.exe"
) do if exist %%p set PYTHON_CMD=%%p&goto :FOUND

echo [错误] 未找到 Python 3.10+
echo 请从 https://www.python.org/downloads/ 下载安装
echo 安装时勾选 "Add Python to PATH"
pause
exit /b 1

:FOUND
%PYTHON_CMD% "%~dp0todo-app.py"
pause
