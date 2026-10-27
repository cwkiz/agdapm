import typer
from typing import Annotated
from rich import print
import seek
import save
app = typer.Typer(help="Tentative package manager for the Agda theorem prover.", add_completion=False, pretty_exceptions_enable=False)

default = seek.search_defaults()

@app.command()
def version(list: bool = False):
    print(f"Agdapm install: [cyan]0.0.1[/cyan]")
    if list:
        dirs = seek.fetch_install_dir(default, False)
        for idx, p in enumerate(dirs):
            print(f"Agda install [green]{idx+1}: {p}[/green]")
    else: 
        dir = seek.fetch_install_dir(default, True)
        print(f"Agda install: [green]{dir}[/green]")

@app.command()
def list():
    configs = seek.read_submodule_configs(default)
    for name in ("libraries", "defaults"):
        config_file = default / name
        if name in configs:
            print(f"[cyan]{config_file}[/cyan]")
            print(configs[name])
        else:
            print(f"Agda global config not found at [red]{config_file}[/red].")

@app.command()
def gen():
    delete = typer.confirm(f"Are you sure you would like to (re-)generate defaults and config files into {default}?", abort=True)
    save.generate_defaults()
    save.generate_libraries()

@app.command()
def init():
    delete = typer.confirm(f"Are you sure you would like to (re-)generate defaults and config files into {default}?", abort=True)
    save.generate_defaults()
    save.generate_libraries()
    save.generate_agdapm()

@app.command()
def install(git: str):
    repo_dir = save.download_into_agdapm(git)
    print(f"Cloned into [green]{repo_dir}[/green]!")
    titles = save.get_library_titles(repo_dir)
    if titles:
        print("Libraries: " + ", ".join(f"[cyan]{title}[/cyan]" for title in titles))
    else:
        print("[red]No Agda library files found in the repository.[/red]")
    typer.confirm(f"Are you sure you would like to re-generate defaults and config files into {default}?", abort=True)
    save.generate_defaults()
    save.generate_libraries()
if __name__ == "__main__":
    app()