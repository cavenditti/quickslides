# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "click",
#   "rich",
# ]
# ///

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import click
import rich
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

OPENING = """#import "../typslides/lib.typ": *

// Project configuration
#show: typslides.with(
  ratio: "16-9",
)

#front-slide(
  title: "{}",
  subtitle: "{}",
  authors: "{}",
  info: "{}",
)

#table-of-contents()

"""


console = Console()

H1 = "# "
H2 = "## "
H1_PATTERN = r"^#\s+"
H2_PATTERN = r"^##\s+"
H1_RE = re.compile(H1_PATTERN)
H2_RE = re.compile(H2_PATTERN)
H1_OR_H2_RE = re.compile(rf"{H1_PATTERN}|{H2_PATTERN}")
H1_OR_H2_LINE_RE = re.compile(rf"^{H1_PATTERN}.*|^{H2_PATTERN}.*")


def is_h1(line: str) -> bool:
    """Check if the line is an H1 heading."""
    return bool(H1_RE.match(line))


def is_h2(line: str) -> bool:
    """Check if the line is an H2 heading."""
    return bool(H2_RE.match(line))


def is_h1_or_h2(line: str) -> bool:
    """Check if the line is an H1 or H2 heading."""
    return bool(H1_RE.match(line)) or bool(H2_RE.match(line))


def title(text: str) -> str:
    """Extract the title from an H1 heading."""
    line = text.split("\n")[0]
    match = H1_OR_H2_RE.match(line)
    if match:
        return line[match.end() :].strip()
    return line.strip()


def remove_h1_h2(text: str) -> str:
    """Remove H1 and H2 headings from the text."""
    return H1_OR_H2_LINE_RE.sub("", text).strip("\n")


def indent_lines(text: str, indent: str = "  ") -> str:
    """Indent lines of text with the specified indent."""
    return "\n".join(f"{indent}{line}" if line else line for line in text.splitlines())


def split_into_slides(content: str, separator: str) -> list[str]:
    """Split markdown content into slides based on the separator."""
    pattern = f"^{re.escape(separator)}$"
    slides = re.split(pattern, content, flags=re.MULTILINE)
    return [slide.strip() for slide in slides if slide.strip()]


def convert_to_typst(markdown_content: str) -> str:
    """Convert markdown content to typst using pandoc."""
    with tempfile.NamedTemporaryFile(
        mode="w+", encoding="utf-8", suffix=".md", delete=False
    ) as temp_md:
        temp_md.write(markdown_content)
        temp_md_path = temp_md.name

    try:
        # Run pandoc to convert from markdown to typst
        result = subprocess.run(
            ["pandoc", temp_md_path, "-f", "markdown", "-t", "typst"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Convert and indent the output
        return indent_lines(result.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Pandoc error:[/bold red] {e.stderr}", style="red")
        return f"// Failed to convert markdown:\n{markdown_content}"
    finally:
        # Clean up the temporary file
        os.unlink(temp_md_path)


def process_slide(slide: str) -> str:
    """Process a single slide and return its typst representation."""
    slide = slide.strip()

    def make_slide(slide: str) -> str:
        """Create a single typst slide"""
        slide_title = title(s)
        return f'#slide(title: "{slide_title}")[\n{convert_to_typst(remove_h1_h2(slide))}\n]\n'

    match slide:
        case s if is_h1(s):
            slide_title = title(s)
            typst_content = f"#section[{slide_title}]"

            if len(slide.split("\n")) > 1:
                typst_content += "\n\n" + make_slide(slide)

            return typst_content

        case s if is_h2(s):
            return make_slide(slide)

        case _:
            return convert_to_typst(slide)


@click.command("mdslides")
@click.argument(
    "markdown_file", type=click.Path(exists=True, dir_okay=False, readable=True)
)
@click.option(
    "--output",
    "-o",
    help="Output file path (default: input filename with .typ extension)",
)
def main(markdown_file: str, output: Optional[str] = None):
    """Convert a markdown file to Typst slides using H1 for title slides and H2 for content slides."""
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
        output = md_path.with_suffix(".typ")
    else:
        output = Path(output)

    # Read markdown content
    with open(md_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Parse front matter if present
    front_matter = {}
    front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if front_matter_match:
        front_matter_content = front_matter_match.group(1)
        # Parse simple key-value pairs
        for line in front_matter_content.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                front_matter[key.strip().lower()] = value.strip()

        # Remove front matter from content
        content = content[front_matter_match.end() :]

    # Extract presentation info
    title = front_matter.get("title", "")
    subtitle = front_matter.get("subtitle", "")
    author = front_matter.get("author", "")
    info = front_matter.get("date", "")

    if front_matter:
        console.print(
            f"Metadata: [cyan]{', '.join(f'{k}=\'{v}\'' for k, v in front_matter.items())}[/cyan]"
        )

    # Add typst imports, opening slide and table of contents
    full_typst = OPENING.format(title, subtitle, author, info)

    # Split content based on H1 and H2 headings
    slides = []
    lines = content.split("\n")
    current_slide = []

    for line in lines:
        if is_h1_or_h2(line):  # H1 or H2 - new slide
            if current_slide:
                slides.append("\n".join(current_slide))
                current_slide = []
        current_slide.append(line)

    # Add the last slide if there's content
    if current_slide:
        slides.append("\n".join(current_slide))

    console.print(f"Found [yellow]{len(slides)}[/yellow] slides")

    # Process each slide with pandoc
    typst_slides = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Converting slides...", total=len(slides))

        for i, slide in enumerate(slides, 1):
            progress.update(task, description=f"Converting slide {i}/{len(slides)}")
            typst_content = process_slide(slide)
            typst_slides.append(typst_content)
            progress.advance(task)

    # Join all slides and write to output file
    full_typst += "\n".join(typst_slides)

    with open(output, "w", encoding="utf-8") as f:
        f.write(full_typst)

    console.print(
        f"[bold green]Success![/bold green] Output written to [blue]{output}[/blue]"
    )
    return 0


if __name__ == "__main__":
    main()
