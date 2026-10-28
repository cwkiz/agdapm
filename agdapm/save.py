from pathlib import Path
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from . import seek


default_dir = seek.search_defaults()
defaults = default_dir / "defaults"
libraries = default_dir / "libraries"
conflict_selections_file = seek.agdapm_defaults() / "conflict-selections.json"

def get_installed_agda_files():
    files = seek.get_agda_files(default_dir)
    agdapm_dir = seek.agdapm_defaults()
    if agdapm_dir.is_dir():
        files.extend(seek.get_agda_files(agdapm_dir))
    return files

def get_conflict_selections() -> dict[str, list[str]]:
    if not conflict_selections_file.is_file():
        return {}
    selections = json.loads(conflict_selections_file.read_text(encoding="utf-8"))
    if not isinstance(selections, dict) or any(
        not isinstance(title, str)
        or not isinstance(paths, list)
        or not paths
        or any(not isinstance(path, str) for path in paths)
        for title, paths in selections.items()
    ):
        raise ValueError(f"invalid conflict selections file: {conflict_selections_file}")
    return selections

def save_conflict_selections(selections: dict[str, list[str]]) -> None:
    conflict_selections_file.parent.mkdir(parents=True, exist_ok=True)
    conflict_selections_file.write_text(
        json.dumps(selections, indent=2) + "\n",
        encoding="utf-8",
    )

def get_configured_agda_files() -> list[Path]:
    files = get_installed_agda_files()
    files_by_title: dict[str, list[Path]] = {}
    for file in files:
        files_by_title.setdefault(get_library_title(file), []).append(file)

    selections = get_conflict_selections()
    selected_paths: dict[str, set[str]] = {}
    for title, candidates in files_by_title.items():
        if len(candidates) < 2 or title not in selections:
            continue
        available = {str(file.resolve()) for file in candidates}
        selected = set(selections[title])
        missing = selected - available
        if missing:
            raise ValueError(
                f"saved conflict selection for '{title}' references missing library files: "
                f"{', '.join(sorted(missing))}; run 'conflicts --fix' to choose again"
            )
        selected_paths[title] = selected

    return [
        file
        for file in files
        if get_library_title(file) not in selected_paths
        or str(file.resolve()) in selected_paths[get_library_title(file)]
    ]

def generate_defaults():
    files = get_configured_agda_files()
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
    files = get_configured_agda_files()
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

def get_library_conflicts() -> dict[str, list[Path]]:
    libraries_by_title: dict[str, list[Path]] = {}
    for file in get_installed_agda_files():
        title = get_library_title(file)
        libraries_by_title.setdefault(title, []).append(file)
    return {
        title: sorted(files)
        for title, files in sorted(libraries_by_title.items())
        if len(files) > 1
    }

def find_agda_modules(module_or_path: str) -> list[Path]:
    managed_dir = seek.agdapm_defaults().resolve()
    requested_path = Path(module_or_path).expanduser()
    is_path = (
        requested_path.exists()
        or requested_path.suffix.lower() == ".agda"
        or "\\" in module_or_path
        or "/" in module_or_path
    )
    if is_path:
        module_file = requested_path.resolve()
        if module_file.suffix.lower() != ".agda":
            raise ValueError(f"module path must point to an .agda file: {module_or_path}")
        if not module_file.is_file():
            raise FileNotFoundError(f"Agda module not found: {module_file}")
        try:
            module_file.relative_to(managed_dir)
        except ValueError:
            raise ValueError("only modules inside Agdapm's managed directory can be removed") from None
        return [module_file]

    module_parts = module_or_path.split(".")
    if any(not part or part in {".", ".."} for part in module_parts):
        raise ValueError(f"invalid Agda module name: {module_or_path}")
    if not managed_dir.is_dir():
        return []

    matches = []
    for file in managed_dir.rglob("*.agda"):
        relative_parts = file.relative_to(managed_dir).with_suffix("").parts
        if len(relative_parts) >= len(module_parts) and relative_parts[-len(module_parts):] == tuple(module_parts):
            matches.append(file.resolve())
    return sorted(matches)

def remove_agda_module(module_file: Path) -> Path:
    managed_dir = seek.agdapm_defaults().resolve()
    module_file = module_file.resolve()
    if module_file.suffix.lower() != ".agda" or not module_file.is_file():
        raise FileNotFoundError(f"Agda module not found: {module_file}")
    try:
        module_file.relative_to(managed_dir)
    except ValueError:
        raise ValueError("only modules inside Agdapm's managed directory can be removed") from None

    module_file.unlink()
    return module_file

def remove_agda_module_directory(module_file: Path) -> Path:
    managed_dir = seek.agdapm_defaults().resolve()
    module_file = module_file.resolve()
    if module_file.suffix.lower() != ".agda" or not module_file.is_file():
        raise FileNotFoundError(f"Agda module not found: {module_file}")
    try:
        module_file.relative_to(managed_dir)
    except ValueError:
        raise ValueError("only modules inside Agdapm's managed directory can be removed") from None

    directory = module_file.parent
    if directory == managed_dir:
        raise ValueError("refusing to remove the Agdapm managed directory")
    shutil.rmtree(directory)
    return directory

def remove_agda_install_directory(install_dir: Path) -> Path:
    managed_dir = seek.agdapm_defaults().resolve()
    install_dir = install_dir.resolve()
    if not install_dir.is_dir():
        raise NotADirectoryError(f"Agdapm install directory not found: {install_dir}")
    try:
        relative = install_dir.relative_to(managed_dir)
    except ValueError:
        raise ValueError("only Agdapm-managed install directories can be removed") from None
    if len(relative.parts) != 1:
        raise ValueError(
            "remove the top-level Agdapm install directory, not a nested directory"
        )

    shutil.rmtree(install_dir)
    return install_dir

def prune_conflict_selections() -> None:
    selections = get_conflict_selections()
    available = {str(file.resolve()) for file in get_installed_agda_files()}
    updated = {
        title: [path for path in paths if path in available]
        for title, paths in selections.items()
    }
    updated = {title: paths for title, paths in updated.items() if paths}
    if updated != selections:
        save_conflict_selections(updated)

def resolve_library_conflicts(selections: dict[str, list[Path]]) -> None:
    saved = get_conflict_selections()
    saved.update({
        title: [str(file.resolve()) for file in files]
        for title, files in selections.items()
    })
    save_conflict_selections(saved)
