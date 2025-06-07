@echo off
REM Download steam.py and thankyou.html from GitHub
curl -L -o steam.py https://raw.githubusercontent.com/yourusername/yourrepo/main/steam.py
curl -L -o thankyou.html https://raw.githubusercontent.com/yourusername/yourrepo/main/thankyou.html

REM Run steam.py (assumes python is installed)
python steam.py

REM Open thankyou.html in default browser
start "" thankyou.html

pause