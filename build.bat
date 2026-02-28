@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% equ 0 (
  set PY=python
  goto :build
)
where py >nul 2>&1
if %errorlevel% equ 0 (
  set PY=py -3
  goto :build
)
echo Python не найден. Установите Python с https://www.python.org/ и запустите снова.
pause
exit /b 1

:build
echo Установка PyInstaller...
%PY% -m pip install pyinstaller --quiet
echo Сборка exe...
%PY% -m PyInstaller --onefile --noconsole --name "Kalkulyator_ZHKH" main.py
if %errorlevel% neq 0 (
  echo Ошибка сборки.
  pause
  exit /b 1
)
echo.
echo Готово: dist\Kalkulyator_ZHKH.exe
echo Скопируйте exe на любой ПК — Python не нужен.
pause
