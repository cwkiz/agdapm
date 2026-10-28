from pathlib import Path

import typer
from rich import print

from .. import save, seek


def remove(
    module: str,
    rf: bool = typer.Option(
        False,
        "--rf",
        help="Recursively remove the containing module directory or managed install.",
    ),
) -> None:
    requested_path = Path(module).expanduser()
    if requested_path.is_dir():
        _remove_install(requested_path, rf)
        return

    matches = save.find_agda_modules(module)
    if not matches:
        raise typer.BadParameter(f"No managed Agda module found for '{module}'.")

    if len(matches) > 1:
        print(f"[yellow]Multiple modules match '{module}':[/yellow]")
        for path in matches:
            print(f"  {path}")
        selected = typer.prompt("Enter the exact path to remove")
        selected_path = Path(selected).expanduser().resolve()
        if selected_path not in matches:
            raise typer.BadParameter("Select one of the listed module paths.")
        matches = [selected_path]

    module_file = matches[0]
    if rf:
        target = module_file.parent
        if target == seek.agdapm_defaults().resolve():
            raise typer.BadParameter("Refusing to remove the Agdapm managed directory.")
        print(
            f"[red]--rf will recursively remove [yellow]{target}[/yellow], "
            "including all files and modules in it.[/red]"
        )
    else:
        target = module_file
        print(f"Removing Agda source file [yellow]{target}[/yellow].")
    typer.confirm("Continue?", abort=True)
    if rf:
        save.remove_agda_module_directory(module_file)
    else:
        save.remove_agda_module(module_file)
    _regenerate_configs()
    print(f"Removed [green]{target}[/green] and regenerated Agda configs.")


def _remove_install(path: Path, recursive: bool) -> None:
    if not recursive:
        raise typer.BadParameter("removing a complete install requires --rf")
    managed_dir = seek.agdapm_defaults().resolve()
    target = path.resolve()
    try:
        relative = target.relative_to(managed_dir)
    except ValueError:
        raise typer.BadParameter(
            "only Agdapm-managed install directories can be removed"
        ) from None
    if len(relative.parts) != 1:
        raise typer.BadParameter("why remove the top-level Agdapm install directory")
    print(
        f"[red]--rf will recursively remove the entire install "
        f"[yellow]{target}[/yellow], including all files and modules in it.[/red]"
    )
    typer.confirm("Continue?", abort=True)
    save.remove_agda_install_directory(target)
    _regenerate_configs()
    print(f"Removed install [green]{target}[/green] and regenerated Agda configs.")


def _regenerate_configs() -> None:
    save.prune_conflict_selections()
    save.generate_defaults()
    save.generate_libraries()
