"""Tests for markdown to typst conversion."""

from mdslides.converter import convert_markdown_to_typst, convert_text


def test_convert_bold_text() -> None:
    """Test bold text conversion."""
    assert convert_text("**bold**") == "*bold*"
    assert convert_text("__bold__") == "*bold*"


def test_convert_italic_text() -> None:
    """Test italic text conversion."""
    assert convert_text("*italic*") == "_italic_"
    assert convert_text("_italic_") == "_italic_"


def test_convert_inline_code() -> None:
    """Test inline code conversion."""
    assert convert_text("`code`") == "`code`"


def test_convert_links() -> None:
    """Test link conversion."""
    assert (
        convert_text("[text](https://example.com)")
        == '#link("https://example.com")[text]'
    )


def test_convert_lists() -> None:
    """Test list conversion."""
    markdown = "- Item 1\n- Item 2"
    expected = "- Item 1\n- Item 2"
    assert convert_text(markdown) == expected


def test_full_document_conversion() -> None:
    """Test conversion of a full document."""
    markdown = """---
title: Test Presentation
subtitle: Testing MDSlides
author: Test Author
date: 2023-01-01
---

# Introduction

This is a test presentation.

## Slide One

- Bullet point
- Another bullet point

## Slide Two

**Bold text** and *italic text*
"""

    result = convert_markdown_to_typst(markdown)

    # Check that the front matter was processed correctly
    assert 'title: "Test Presentation"' in result
    assert 'subtitle: "Testing MDSlides"' in result
    assert 'authors: "Test Author"' in result
    assert 'info: "2023-01-01"' in result

    # Check that we have a section and slides
    assert "#section[Introduction]" in result
    assert '#slide(title: "Slide One")' in result
    assert '#slide(title: "Slide Two")' in result

    # Check that formatting is preserved
    assert "- Bullet point" in result
    assert "*Bold text*" in result
    assert "_italic text_" in result
