from pathlib import Path
import re
import subprocess
import seek


default_dir = seek.search_defaults()
defaults = default_dir / "defaults"
libraries = default_dir / "libraries"

def get_installed_agda_files():
    files = seek.get_agda_files(default_dir)
    agdapm_dir = seek.agdapm_defaults()
    if agdapm_dir.is_dir():
        files.extend(seek.get_agda_files(agdapm_dir))
    return files

def generate_defaults():
    files = get_installed_agda_files()
    defaults.write_text(
        "".join(f"{get_library_title(file)}\n" for file in files),
        encoding="utf-8",
    )

def get_library_title(file: Path) -> str:
    for line in file.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "name" and value.strip():
            return value.strip()
    return file.stem

def generate_libraries():
    files = get_installed_agda_files()
    libraries.write_text(
        "".join(f"{file.resolve()}\n" for file in files),
        encoding="utf-8",
    )
    
def generate_agdapm():
    agdapm_dir = seek.agdapm_defaults()
    if agdapm_dir.exists():
        if not agdapm_dir.is_dir():
            raise FileExistsError(f"Agdapm path exists but is not a directory: {agdapm_dir}. Why?")
        print("Agdapm folder already exists.") 
        return agdapm_dir
    agdapm_dir.mkdir(parents=True)
    return agdapm_dir

def download_into_agdapm(git: str) -> Path:
    repo_name = git.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", repo_name):
        raise ValueError(f"not valid git url repo name: {git}")

    agdapm_dir = generate_agdapm()
    repo_dir = agdapm_dir / repo_name
    if repo_dir.exists():
        raise FileExistsError(f"directory already exists: {repo_dir}")

    subprocess.run(["git", "clone", git, str(repo_dir)], check=True)
    return repo_dir

def get_library_titles(path: Path) -> list[str]:
    return [get_library_title(file) for file in seek.get_agda_files(path)]