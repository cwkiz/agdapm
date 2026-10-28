from pathlib import Path
import os
import re

def search_defaults():
    if os.name == "posix":
        path = Path("~/.agda").expanduser()
    elif os.name == "nt":
        APPDATA = os.getenv('APPDATA')
        if APPDATA is None:
            raise Exception("No APPDATA env.")
        else:
            path = Path(APPDATA) / "agda"

    if path.exists() and path.is_dir():
        return path
    else:
        raise Exception("Agda default path does not exist.")

def agdapm_defaults():
    if os.name == "posix":
        path = Path("~/.agdapm").expanduser()
    elif os.name == "nt":
        APPDATA = os.getenv('APPDATA')
        if APPDATA is None:
            raise Exception("No APPDATA env.")
        else:
            path = Path(APPDATA) / "agdapm"
    else:
        raise OSError(f"Unsupported operating system: {os.name}")
    return path




def fetch_install_dir(path, latest: bool):
    paths = sorted(
        path.iterdir(),
        key=lambda x: tuple(map(int, re.findall(r"\d+", x.name))),
        reverse=True
    )
    if latest:
        return paths[0]
    else:  
        return paths

def read_submodule_configs(path: Path) -> dict[str, str]:
    configs = {}
    for name in ("libraries", "defaults"):
        config_file = path / name
        if config_file.is_file():
            configs[name] = config_file.read_text(encoding="utf-8")
    return configs

def get_agda_files(path: Path):
    return [file for file in path.rglob('*.agda-lib') if file.is_file() and file.suffix]