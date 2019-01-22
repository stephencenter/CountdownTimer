from cx_Freeze import setup, Executable

setup(
    name = "Countdown Timer",
    version = "1",
    description = "Countdown to a specific date",
    executables = [Executable("countdown.py", base="win32gui", icon="countdown.ico")]
)