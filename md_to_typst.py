#!/usr/bin/env python3
"""
Markdown to Typst Converter using mistletoe
"""
import sys
import os
from datetime import date


from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph, BlockCode, List, ListItem, Quote
from mistletoe.span_token import RawText, Emphasis, Strong, InlineCode, LineBreak, Link


def convert_md_to_typst(input_file, output_file):
    """Convert Markdown file to Typst format, sorting content by H1 headings"""
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse Markdown to AST
    ast = Document(md_content)

    # TODO: hook for further processing of the AST before rendering to Typst

    # Split AST children into sections by H1 headings
    sections = []
    unsorted = []
    current_title = None
    current_nodes = []

    for node in ast.children:
        if isinstance(node, Heading) and node.level == 1:
            if current_title is not None:
                sections.append((current_title, current_nodes))
            else:
                if unsorted:
                    sections.append(("Unsorted Content", unsorted))
            current_title = ''.join(
                child.content for child in node.children if hasattr(child, 'content'))
            current_nodes = [node]
        else:
            if current_title is not None:
                current_nodes.append(node)
            else:
                unsorted.append(node)

    if current_title is not None:
        sections.append((current_title, current_nodes))
    elif unsorted:
        sections.append(("Unsorted Content", unsorted))

    # Sort sections by title, keeping unsorted section first
    unsorted_sections = [s for s in sections if s[0] == "Unsorted Content"]
    sorted_sections = sorted(
        [s for s in sections if s[0] != "Unsorted Content"],
        key=lambda x: x[0])
    final_sections = unsorted_sections + sorted_sections

    # Begin Typst output
    typst_output = ''
    typst_output += """#import "@preview/in-dexter:0.7.0": *
#let index-main(..args) = index(fmt: strong, ..args)


#import "fantasy-encyclopedia.typ": fantasy-encyclopedia
#show: fantasy-encyclopedia.with(
  title: [
    #v(-90pt)On the #linebreak() Nature of #linebreak() Bremwith
  ]
)
"""

    # Render each section
    for title, nodes in final_sections:
        typst_output += render_nodes(nodes)

    typst_output +="""\n#pagebreak()
= Index
#columns(2)[
  #make-index(title: none)
  ]"""    

    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(typst_output)

    print(f"Converted {input_file} to {output_file}")
    print(f"Sorted {len(sorted_sections)} sections by H1 headings.")


def render_nodes(nodes):
    """Render a list of AST nodes to Typst format"""
    output = ''
    for node in nodes:
        output += render_node(node)
    return output


def render_node(node):
    """Render a single AST node based on its type"""
    if isinstance(node, Heading):
        text = ''.join(render_inline(child) for child in node.children)
        return f"{'=' * node.level} {text} #index-main(\"{text}\")\n\n"
    if isinstance(node, Paragraph):
        content = ''.join(render_inline(child) for child in node.children)
        return f"{content}\n\n"
    if isinstance(node, BlockCode):
        info = node.language or ''
        code = node.children[0].content if node.children else ''
        return f"```{info}\n{code}```\n\n"
    if isinstance(node, List):
        items = []
        for idx, item in enumerate(node.children, start=1):
            prefix = f"{idx}. " if getattr(node, 'start', None) is not None else '- '
            item_text = ''.join(
                render_node(child).strip() for child in item.children)
            items.append(f"{prefix}{item_text}")
        return '\n'.join(items) + '\n\n'
    if isinstance(node, Quote):
        quote = ''.join(render_node(child) for child in node.children)
        return f"quote {{ {quote.strip()} }}\n\n"
    if hasattr(node, 'children'):
        return ''.join(render_node(child) for child in node.children)
    return ''


def render_inline(token):
    """Render inline-level tokens"""
    if isinstance(token, RawText):
        return token.content
    if isinstance(token, Emphasis):
        return f"/{''.join(render_inline(child) for child in token.children)}/"
    if isinstance(token, Strong):
        return f"*{''.join(render_inline(child) for child in token.children)}*"
    if isinstance(token, InlineCode):
        content = token.children[0].content if token.children else token.content
        return f"`{content}`"
    if isinstance(token, LineBreak):
        return '\n'
    if isinstance(token, Link):
        return ''.join(render_inline(child) for child in token.children)
    if hasattr(token, 'children'):
        return ''.join(render_inline(child) for child in token.children)
    return ''


def main():
    if len(sys.argv) != 3:
        print("Usage: python md_to_typst.py input.md output.typ")
        sys.exit(1)
    input_file, output_file = sys.argv[1], sys.argv[2]
    if not os.path.isfile(input_file):
        print(f"Error: input file '{input_file}' does not exist")
        sys.exit(1)
    convert_md_to_typst(input_file, output_file)

if __name__ == "__main__":
    main()
