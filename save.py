from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
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

def install_local_source(source: str) -> Path:
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"source does not exist: {source_path}")
    if source_path.is_dir():
        repo_name = source_path.name
    elif source_path.is_file() and source_path.suffix.lower() == ".zip":
        repo_name = source_path.stem
    else:
        raise ValueError(f"source must be a directory or ZIP file: {source_path}")

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", repo_name):
        raise ValueError(f"not a valid install name: {repo_name}")

    agdapm_dir = generate_agdapm()
    managed_dir = agdapm_dir.resolve()
    try:
        source_path.relative_to(managed_dir)
    except ValueError:
        pass
    else:
        raise ValueError("source cannot be inside the Agdapm install directory")
    if source_path.is_dir():
        try:
            managed_dir.relative_to(source_path)
        except ValueError:
            pass
        else:
            raise ValueError("source cannot contain the Agdapm install directory")

    repo_dir = agdapm_dir / repo_name
    if repo_dir.exists():
        raise FileExistsError(f"directory already exists: {repo_dir}")

    with tempfile.TemporaryDirectory(dir=agdapm_dir) as temporary_dir:
        staged_dir = Path(temporary_dir) / repo_name
        if source_path.is_dir():
            shutil.copytree(source_path, staged_dir)
        else:
            with zipfile.ZipFile(source_path) as archive:
                staged_dir.mkdir()
                for member in archive.infolist():
                    target = (staged_dir / member.filename).resolve()
                    try:
                        target.relative_to(staged_dir.resolve())
                    except ValueError:
                        raise ValueError(
                            f"ZIP contains a path outside the install directory: {member.filename}"
                        ) from None
                archive.extractall(staged_dir)
        staged_dir.rename(repo_dir)
    return repo_dir

def install_source(source: str) -> tuple[Path, bool]:
    source_path = Path(source).expanduser()
    if source_path.exists():
        return install_local_source(source), True
    return download_into_agdapm(source), False

def get_library_titles(path: Path) -> list[str]:
    return [get_library_title(file) for file in seek.get_agda_files(path)]