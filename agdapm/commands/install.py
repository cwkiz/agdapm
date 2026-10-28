import typer
from rich import print

from .. import save, seek
from .conflicts import show_conflicts


def install(source: str) -> None:
    default = seek.search_defaults()
    repo_dir, copied = save.install_source(source)
    action = "Copied into" if copied else "Cloned into"
    print(f"{action} [green]{repo_dir}[/green]!")
    titles = save.get_library_titles(repo_dir)
    if titles:
        print("Libraries: " + ", ".join(f"[cyan]{title}[/cyan]" for title in titles))
    else:
        print("[red]No Agda library files found in the repository.[/red]")
    show_conflicts()
    typer.confirm(
        f"Are you sure you would like to re-generate defaults and config files into {default}?",
        abort=True,
    )
    save.generate_defaults()
    save.generate_libraries()
