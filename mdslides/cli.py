"""Command-line interface for MDSlides."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mdslides.converter import convert_markdown_to_typst

console = Console()


@click.command("mdslides")
@click.argument(
    "markdown_file", type=click.Path(exists=True, dir_okay=False, readable=True)
)
@click.option(
    "--output",
    "-o",
    help="Output file path (default: input filename with .typ extension)",
)
def main(markdown_file: str, output: str | None) -> int:
    """
    Convert a markdown file to a Typst slides document.
    """
    console.print(
        f"[bold blue]MDSlides[/bold blue]: Processing [green]{markdown_file}[/green]"
    )

    # Validate input file exists
    md_path = Path(markdown_file)
    if not md_path.exists():
        console.print(
            f"[bold red]Error:[/bold red] File '{markdown_file}' not found", style="red"
        )
        return 1

    # Set output path
    if not output:
        output_path = md_path.with_suffix(".typ")
    else:
        output_path = Path(output)

    # Read markdown content
    with open(md_path, encoding="utf-8") as file:
        content = file.read()

    # Process the content with a progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Converting markdown to typst...", total=1)

        # Convert markdown to typst
        typst_content = convert_markdown_to_typst(content)

        progress.update(task, advance=1)

    # Write output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(typst_content)

    console.print(
        "[bold green]Success![/bold green] "
        f"Output written to [blue]{output_path}[/blue]"
    )
    return 0


if __name__ == "__main__":
    main()  # pragma: no cover

