from cx_Freeze import setup, Executable

setup(
    name="SteamApp",
    version="1.0",
    description="Steam app with thankyou.html",
    executables=[Executable("steam.py")],
    include_files=["thankyou.html"],
)