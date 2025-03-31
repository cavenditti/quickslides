"""Command-line interface for MDSlides."""

import shutil
import subprocess
import tempfile
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
@click.option(
    "--compile/--no-compile",
    default=True,
    help="Compile the generated Typst file (default: True)",
)
def main(markdown_file: str, output: str | None, compile: bool) -> int:
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

    # Compile the Typst file if requested
    if compile:
        typst_cmd = shutil.which("typst")
        if not typst_cmd:
            console.print(
                "[bold yellow]Warning:[/bold yellow] typst command not found, skipping compilation"
            )
            return 0

        console.print(f"Compiling [blue]{output_path}[/blue] with typst...")
        try:
            # Create temporary structure

            with tempfile.TemporaryDirectory() as tmp_dir:
                # Create subdirectory for the .typ file
                input_dir = Path(tmp_dir) / "input"
                input_dir.mkdir()

                # Create typslides directory in the same structure
                typslides_dir = Path(tmp_dir) / "typslides"
                typslides_dir.mkdir()

                # Copy the source .typ file to the input directory
                tmp_path = input_dir / output_path.name
                shutil.copy2(output_path, tmp_path)

                # Copy all other files from the same directory as the input file
                input_file_dir = output_path.parent
                for item in input_file_dir.iterdir():
                    if item != output_path:  # Skip the .typ file we already copied
                        dest_path = input_dir / item.name
                        if item.is_file():
                            shutil.copy2(item, dest_path)
                        elif item.is_dir():
                            shutil.copytree(item, dest_path, dirs_exist_ok=True)

                # Copy the typslides directory contents
                curr_dir = Path(__file__).parent
                if (curr_dir.parent / "typslides").exists():
                    shutil.copytree(
                        curr_dir.parent / "typslides", typslides_dir, dirs_exist_ok=True
                    )

                # Determine output PDF path in current directory
                pdf_output_path = Path.cwd() / output_path.with_suffix(".pdf").name

                # Run typst in the temporary directory
                subprocess.run(
                    [
                        "typst",
                        "compile",
                        "--root",
                        ".",
                        str(tmp_path),
                        str(pdf_output_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=tmp_dir,
                )
            console.print("[bold green]Compilation successful![/bold green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Compilation failed:[/bold red] {e.stderr}")
            return 1

    return 0


if __name__ == "__main__":
    main()  # pragma: no cover
