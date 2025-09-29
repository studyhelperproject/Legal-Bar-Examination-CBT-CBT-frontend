@echo off
REM 司法試験CBTシミュレーター起動スクリプト (Windows)

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM 仮想環境をアクティベート
call venv\Scripts\activate.bat

REM アプリケーションを起動
python main.py

pause
