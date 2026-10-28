from pathlib import Path

import typer
from rich import print

from .. import save


def conflicts(
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Settle conflicts by selecting a library path to override ambiguous modules.",
    ),
) -> None:
    if fix:
        fix_conflicts()
    else:
        show_conflicts()


def show_conflicts() -> None:
    found = save.get_library_conflicts()
    if not found:
        print("No duplicate Agda library names found. Congratulations, you win!")
        return
    selections = save.get_conflict_selections()
    print("[yellow]Duplicate Agda library names found:[/yellow]")
    for title, files in found.items():
        print(f"[cyan]{title}[/cyan]")
        for file in files:
            print(f"  {file}")
        active = set(selections.get(title, []))
        available = {str(file.resolve()) for file in files}
        if active and active.issubset(available):
            print("[green]Active in Agda config:[/green] " + "; ".join(sorted(active)))


def fix_conflicts() -> None:
    found = save.get_library_conflicts()
    if not found:
        print("No duplicate Agda library names found. Congratulations, you win!")
        return

    candidates: dict[str, tuple[str, Path]] = {}
    for title, files in found.items():
        print(f"[cyan]{title}[/cyan]")
        for file in files:
            print(f"  {file}")
            candidates[str(file.resolve())] = (title, file)

    while True:
        answer = typer.prompt(
            "Choose one path in order to settle duplicate, separated by semicolons (;)"
        )
        requested = [part.strip() for part in answer.split(";") if part.strip()]
        selections: dict[str, Path] = {}
        invalid = []
        multiple = []
        for path in requested:
            resolved = str(Path(path).expanduser().resolve())
            candidate = candidates.get(resolved)
            if candidate is None:
                invalid.append(path)
                continue
            title, file = candidate
            if title in selections and selections[title] != file:
                multiple.append(title)
            else:
                selections[title] = file

        if invalid:
            print("[red]Unknown path(s): " + "; ".join(invalid) + "[/red]")
        elif multiple:
            print(
                "[red]Choose only one path for each duplicate name: "
                + ", ".join(sorted(set(multiple)))
                + "[/red]"
            )
        elif set(selections) != set(found):
            missing = sorted(set(found) - set(selections))
            print("[red]Choose one path for each: " + ", ".join(missing) + "[/red]")
        else:
            break

    resolved_selections = {
        title: [file]
        for title, file in selections.items()
    }
    save.resolve_library_conflicts(resolved_selections)
    save.generate_defaults()
    save.generate_libraries()
    print("Agda configuration regenerated")
    for title, file in selections.items():
        print(f"[green]Keeping for {title}:[/green] {file}")
