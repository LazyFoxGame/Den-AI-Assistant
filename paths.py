import os
import sys
from pathlib import Path

def get_appdata_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if not appdata:
        appdata = os.path.expanduser("~")
    data_dir = Path(appdata) / "Den"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(os.path.abspath(__file__)).parent

def get_data_path(filename: str) -> str:
    return str(get_appdata_dir() / filename)

def get_resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(os.path.abspath(__file__)).parent
    return str(base / relative_path)