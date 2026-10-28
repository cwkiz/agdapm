import typer
from rich import print

from .. import save, seek


def version(list: bool = False) -> None:
    default = seek.search_defaults()
    print(f"Agdapm install: [cyan]0.0.1[/cyan]") # yes hardcoded
    if list:
        dirs = seek.fetch_install_dir(default, False)
        for idx, path in enumerate(dirs):
            print(f"Agda install [green]{idx + 1}: {path}[/green]")
    else:
        path = seek.fetch_install_dir(default, True)
        print(f"Agda install: [green]{path}[/green]")


def list_command() -> None:
    default = seek.search_defaults()
    configs = seek.read_submodule_configs(default)
    for name in ("libraries", "defaults"):
        config_file = default / name
        if name in configs:
            print(f"[cyan]{config_file}[/cyan]")
            print(configs[name])
        else:
            print(f"Agda global config not found at [red]{config_file}[/red].")


def gen() -> None:
    default = seek.search_defaults()
    typer.confirm(
        f"Are you sure you would like to (re-)generate defaults and config files into {default}?",
        abort=True,
    )
    save.generate_defaults()
    save.generate_libraries()


def init() -> None:
    default = seek.search_defaults()
    typer.confirm(
        f"Are you sure you would like to (re-)generate defaults and config files into {default}?",
        abort=True,
    )
    save.generate_defaults()
    save.generate_libraries()
    save.generate_agdapm()
