import typer

from .commands import conflicts, gen, init, install, list_command, remove, version

app = typer.Typer(
    help="Tentative package manager for the Agda theorem prover.",
    add_completion=False,
    pretty_exceptions_enable=False,
)

app.command()(version)
app.command(name="list")(list_command)
app.command()(gen)
app.command()(init)
app.command()(install)
app.command()(conflicts)
app.command()(remove)


def main() -> None:
    app()
