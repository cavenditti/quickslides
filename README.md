# quickslides

Convert Markdown files to PDF slides presentations, using [typst](https://github.com/typst/typst) and [typeslides](https://github.com/cavenditti/typslides).

## Usage

### Command Line

If you use [uv](https://github.com/astral-sh/uv), you can run `quickslides` directly from the command line by using `uvx`:

```bash
# Basic usage
uvx quickslides your_presentation.md

# Specify output typst file
uvx quickslides your_presentation.md --no-compile -o custom_output.typ
```

Otherwise you can run install `quickslides` with your Python package manager of choice, and then run it from the command line.

### As a Library

```python
from quickslides import convert_markdown_to_typst

# Read markdown content
with open("your_presentation.md", "r") as f:
    markdown_content = f.read()

# Convert to typst
typst_content = convert_markdown_to_typst(
    markdown_content,
    title="My Presentation",
    subtitle="A great presentation",
    author="Your Name",
    info="2025-03-29"
)

# Save the output
with open("presentation.typ", "w") as f:
    f.write(typst_content)
```

## Markdown Format

- Use front matter to specify presentation metadata
- Use `#` (H1) to define sections (will create a section slide with the header text)
- Use `##` (H2) for content slides

Example:

```markdown
---
title: My Presentation
subtitle: A subtitle
author: Your Name
date: 2025-03-29
---

# Introduction

This is a section slide.

## First Content Slide

- This is bullet point 1
- This is bullet point 2

## Second Content Slide

**Bold text** and *italic text*

```

## Requirements

- Python 3.12+
- [typst](https://github.com/typst/typst)
