@echo off
chcp 65001 >nul
echo Скачивание Python 3.12...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%TEMP%\python-installer.exe' -UseBasicParsing"
if %errorlevel% neq 0 (
  echo Ошибка загрузки. Скачайте вручную: https://www.python.org/downloads/
  pause
  exit /b 1
)
echo Запуск установки (отметьте "Add Python to PATH" если окно мастера откроется)...
start /wait "" "%TEMP%\python-installer.exe" /passive PrependPath=1
echo.
echo Готово. Закройте это окно и откройте НОВОЕ окно командной строки, затем запустите build.bat
pause
