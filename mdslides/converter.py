"""Markdown to Typst conversion utilities."""

import re

# Markdown to Typst conversion mappings
CONVERSIONS = [
    # Headers are handled separately
    # Code blocks
    (re.compile(r"```(\w*)\n(.*?)\n```", re.DOTALL), r"```\1\n\2\n```"),
    # Inline code
    (re.compile(r"`([^`]+)`"), r"`\1`"),
    # Italic text
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)"), r"_\1_"),
    (re.compile(r"(?<!_)_([^_]+)_(?!_)"), r"_\1_"),
    # Bold text
    (re.compile(r"\*\*([^*]+)\*\*"), r"*\1*"),
    (re.compile(r"__([^_]+)__"), r"*\1*"),
    # Links
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), r'#link("\2")[\1]'),
    # Images
    (re.compile(r"!\[([^\]]*)\]\(([^)]+)\)"), r"#image(\2, caption: \"\1\")"),
    # Lists
    (re.compile(r"^\s*[-*+]\s+(.*?)$", re.MULTILINE), r"- \1"),
    (re.compile(r"^\s*(\d+)[.)]\s+(.*?)$", re.MULTILINE), r"+ \2"),
    # Blockquotes
    (re.compile(r"^\s*>\s+(.*?)$", re.MULTILINE), r"#quote[\1]"),
    # Horizontal rule
    (re.compile(r"^\s*[-*_]{3,}\s*$", re.MULTILINE), r"#line(length: 100%)"),
    # Tables - complex, minimal support
    (re.compile(r"\|([^|]+)\|([^|]+)\|"), r"#table(columns: 2)[\1][\2]"),
]


def convert_text(text: str) -> str:
    """Apply all markdown to typst conversions to the text in a single pass."""
    # Create a list of conversion patterns in a specific order to avoid interference
    result = text
    for pattern, replacement in CONVERSIONS:
        result = re.sub(pattern, replacement, result)
    return result


def indent_lines(text: str, indent: str = "  ") -> str:
    """Indent lines of text with the specified indent."""
    return "\n".join(f"{indent}{line}" if line else line for line in text.splitlines())


def convert_markdown_to_typst(
    markdown_content: str,
) -> str:
    """
    Convert markdown content to typst slides.

    Args:
        markdown_content: The markdown content to convert
        title: The presentation title
        subtitle: The presentation subtitle
        author: The presentation author
        info: Additional presentation info

    Returns:
        The typst document as a string
    """
    # Parse front matter if present
    front_matter: dict[str, str] = {}
    front_matter_match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n", markdown_content, re.DOTALL
    )

    if front_matter_match:
        front_matter_content = front_matter_match.group(1)
        # Parse simple key-value pairs
        for line in front_matter_content.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                front_matter[key.strip().lower()] = value.strip()

        # Remove front matter from content
        markdown_content = markdown_content[front_matter_match.end() :]

    # Generate the typst document
    typst_content = generate_typst_document(front_matter, markdown_content)

    return typst_content


def generate_typst_header(front_matter: dict[str, str]) -> str:
    """
    Generate a complete typst document from markdown content.

    Args:
        markdown_content: The markdown content to convert
        title: The presentation title
        subtitle: The presentation subtitle
        author: The presentation author
        info: Additional presentation info

    Returns:
        The complete typst document as a string
    """

    # Extract presentation info
    title = front_matter.get("title", "")
    subtitle = front_matter.get("subtitle", "")
    author = front_matter.get("author", "")
    info = front_matter.get("date", "") or front_matter.get("info", "")
    logo = front_matter.get("logo", "img/logo.svg")
    logo_alt = front_matter.get("logo-alt", "img/alt.svg")
    logo_comp = f'image("{logo}", width: 13.75em, height: 13.5em)'
    logo_alt_comp = f'image("{logo_alt}", width: 50em, height: 50em)'

    website_url = front_matter.get("website-url", "")
    email = front_matter.get("email", "")

    # Fill in document header
    return f"""#import "../typslides/lib.typ": *

// Project configuration
#show: typslides.with(
  logo: {logo_comp},
  logo-alt: {logo_alt_comp},
  website-url: "{website_url}",
  email: "{email}",
  ratio: "16-9",
)

#front-slide(
  title: "{title}",
  subtitle: "{subtitle}",
  authors: "{author}",
  info: "{info}",
)

#table-of-contents()

"""


def generate_typst_document(
    front_matter: dict[str, str],
    markdown_content: str,
) -> str:
    """
    Generate a complete typst document from markdown content.

    Args:
        markdown_content: The markdown content to convert
        title: The presentation title
        subtitle: The presentation subtitle
        author: The presentation author
        info: Additional presentation info

    Returns:
        The complete typst document as a string
    """
    # Typst document header
    header = generate_typst_header(front_matter)

    # Process slides
    slides = process_slides(markdown_content)

    # Join all slides with the header
    return header + "\n".join(slides)


def process_slides(markdown_content: str) -> list[str]:
    """
    Process markdown content and split it into slides.

    Args:
        markdown_content: The markdown content to process

    Returns:
        List of typst slides
    """
    # Regex patterns for headings
    h1_pattern = r"^#\s+"
    h2_pattern = r"^##\s+"
    h1_re = re.compile(h1_pattern)
    h2_re = re.compile(h2_pattern)

    # Split content into slides
    lines = markdown_content.split("\n")
    slides: list[list[str]] = []
    current_slide: list[str] = []

    for line in lines:
        # Check if this is a heading that starts a new slide
        if h1_re.match(line) or h2_re.match(line):
            if current_slide:
                slides.append(current_slide)
                current_slide = []
        current_slide.append(line)

    # Add the last slide if there's content
    if current_slide:
        slides.append(current_slide)

    # Convert each slide to typst
    typst_slides: list[str] = []

    for slide_lines in slides:
        slide_content = "\n".join(slide_lines)
        typst_slide = convert_slide(slide_content)
        typst_slides.append(typst_slide)

    return typst_slides


def convert_slide(slide_content: str) -> str:
    """
    Convert a single markdown slide to typst.

    Args:
        slide_content: The markdown slide content

    Returns:
        The typst representation of the slide
    """
    # Check if slide starts with a heading
    lines = slide_content.splitlines()
    if not lines:
        return ""

    first_line = lines[0]

    # Get slide title and remove the heading marker
    title_match = re.match(r"^(#+)\s+(.*?)$", first_line)
    if not title_match:
        # No heading, convert as regular content
        return convert_text(slide_content)

    heading_level = len(title_match.group(1))
    slide_title = title_match.group(2)

    # Remove the title line from content
    body_content = "\n".join(lines[1:])

    # Convert the body content
    typst_body = convert_text(body_content)
    typst_body = indent_lines(typst_body)

    # For H1, create a section and possibly a slide
    if heading_level == 1:
        typst_content = f"#section[{slide_title}]"

        if body_content.strip():
            typst_content += f'\n\n#slide(title: "{slide_title}")[\n{typst_body}\n]'

        return typst_content

    # For H2 or other headings, create a regular slide
    return f'#slide(title: "{slide_title}")[\n{typst_body}\n]'
