#!/usr/bin/env python3
"""
Markdown to Typst Converter
This script reads a Markdown file, sorts content by heading level 1,
and outputs it as a valid Typst file.
"""
import json
import sys
import os
import re
import commonmark
from commonmark.node import Node

def convert_md_to_typst(input_file, output_file):
    """Convert Markdown file to Typst format with sorting by h1 headings"""
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Parse markdown
    parser = commonmark.Parser()
    ast = parser.parse(markdown_text)

    print("Parsed AST:")
    json = commonmark.dumpJSON(ast)
    print(json)
    print("***")
    
    # Extract sections by h1 headings
    sections = {}
    current_h1 = "Unsorted Content"
    current_section = []
    
    # Create renderer to capture content
    renderer = commonmark.HtmlRenderer()
    
    # Function to collect section content as raw markdown
    def collect_section_content(node, section_start, section_end):
        if node.sourcepos and node.sourcepos[0][0] >= section_start and node.sourcepos[1][0] <= section_end:
            line_start = node.sourcepos[0][0]
            line_end = node.sourcepos[1][0]
            col_start = node.sourcepos[0][1]
            col_end = node.sourcepos[1][1]
            
            # Extract the lines from the original markdown
            section_lines = markdown_text.split('\n')[line_start-1:line_end]
            if len(section_lines) == 1:
                # Single line
                return section_lines[0][col_start-1:col_end]
            else:
                # Multiple lines
                section_lines[0] = section_lines[0][col_start-1:]
                section_lines[-1] = section_lines[-1][:col_end]
                return '\n'.join(section_lines)
        return ""
    
    # Find all H1 headings
    h1_nodes = []
    current_node = ast.first_child
    while current_node:
        if current_node.t == 'heading' and current_node.level == 1:
            h1_nodes.append(current_node)
        current_node = current_node.nxt

    # Extract sections based on H1 nodes
    for i, h1_node in enumerate(h1_nodes):
        # Extract heading text
        heading_text = ""
        child = h1_node.first_child
        while child:
            if child.literal:
                heading_text += child.literal
            child = child.nxt
        
        # Determine section boundaries
        section_start = h1_node.sourcepos[0][0]  # Line number of heading start
        if i < len(h1_nodes) - 1:
            section_end = h1_nodes[i+1].sourcepos[0][0] - 1  # Line before next heading
        else:
            # For the last section, get to the end of file
            section_end = markdown_text.count('\n') + 1
        
        # Extract the original markdown text for this section
        section_lines = markdown_text.split('\n')[section_start-1:section_end]
        section_content = '\n'.join(section_lines)
        
        # Store the section
        sections[heading_text] = section_content
    
    # Handle content before the first H1, if any
    if h1_nodes and h1_nodes[0].sourcepos[0][0] > 1:
        first_h1_line = h1_nodes[0].sourcepos[0][0]
        unsorted_content = '\n'.join(markdown_text.split('\n')[:first_h1_line-1])
        if unsorted_content.strip():
            sections["Unsorted Content"] = unsorted_content
    elif not h1_nodes:
        sections["Unsorted Content"] = markdown_text
    
    # Sort sections by heading name
    sorted_sections = dict(sorted(sections.items()))
    
    # Create Typst output
    typst_output = "#import \"fantasy-encyclopedia.typ\": *\n\n"
    typst_output += "@document(title: \"Generated from Markdown\", date: \"" + get_current_date() + "\")\n\n"
    
    # Add sections to output, converting H1 headings to Typst format
    for heading, content in sorted_sections.items():
        if heading == "Unsorted Content":
            typst_output += content + "\n\n"
        else:
            # Convert Markdown H1 heading to Typst H1 heading
            content = re.sub(r'^# (.+?)$', r'= \1', content, flags=re.MULTILINE, count=1)
            typst_output += content + "\n\n"
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(typst_output)
    
    print(f"Converted {input_file} to {output_file}")
    print(f"Sorted {len(sorted_sections)} sections by heading level 1")

def get_current_date():
    """Return the current date in ISO format"""
    from datetime import date
    return date.today().isoformat()

def main():
    if len(sys.argv) != 3:
        print("Usage: python md_to_typst.py input.md output.typ")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    
    convert_md_to_typst(input_file, output_file)

if __name__ == "__main__":
    main()