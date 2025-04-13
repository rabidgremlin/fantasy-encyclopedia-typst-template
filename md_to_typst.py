#!/usr/bin/env python3
"""
Markdown to Typst Converter
This script reads a Markdown file, sorts content by heading level 1,
and outputs it as a valid Typst file.
"""

import sys
import os
import re
import importlib

# Import commonmark
import commonmark

def convert_md_to_typst(input_file, output_file):
    """Convert Markdown file to Typst format with sorting by h1 headings"""
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Parse markdown
    parser = commonmark.Parser()
    ast = parser.parse(markdown_text)
    
    # Extract sections by h1 headings
    sections = {}
    current_h1 = "Unsorted Content"
    current_content = []
    
    walker = ast.walker()
    event = walker.nxt()
    while event is not None:
        node, entering = event
        
        if node.t == 'heading' and node.level == 1 and entering:
            # Save previous section
            if current_content:
                if current_h1 in sections:
                    sections[current_h1].extend(current_content)
                else:
                    sections[current_h1] = current_content
                
            # Start new section
            title_node = node.first_child
            if title_node:
                current_h1 = title_node.literal
            else:
                current_h1 = f"Unnamed Section {len(sections) + 1}"
            
            current_content = []
            
            # Skip until we exit this heading
            while event and (node.t == 'heading' or entering):
                event = walker.nxt()
                if event:
                    node, entering = event
                else:
                    break
            
            if not event:
                break
            continue
        
        # For all other content, store the raw markdown
        if entering:
            raw_markdown = node_to_markdown(node)
            if raw_markdown:
                current_content.append(raw_markdown)
        
        event = walker.nxt()
    
    # Add the last section
    if current_content:
        if current_h1 in sections:
            sections[current_h1].extend(current_content)
        else:
            sections[current_h1] = current_content
    
    # Sort sections by heading name
    sorted_sections = dict(sorted(sections.items()))
    
    # Convert to Typst format
    typst_output = convert_sections_to_typst(sorted_sections)
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(typst_output)
    
    print(f"Converted {input_file} to {output_file}")
    print(f"Sorted {len(sorted_sections)} sections by heading level 1")

def node_to_markdown(node):
    """Extract markdown content from a node"""
    if node.literal:
        return node.literal
    return ""

def convert_sections_to_typst(sections):
    """Convert markdown sections to Typst format"""
    typst_output = "#import \"fantasy-encyclopedia.typ\": *\n\n"
    typst_output += "@document(title: \"Generated from Markdown\", date: \"" + get_current_date() + "\")\n\n"
    
    for heading, content in sections.items():
        if heading != "Unsorted Content":
            typst_output += f"= {heading}\n\n"
        
        for item in content:
            # Convert markdown syntax to typst
            typst_content = convert_markdown_to_typst(item)
            typst_output += typst_content + "\n"
    
    return typst_output

def convert_markdown_to_typst(markdown_text):
    """Convert Markdown syntax to Typst syntax"""
    # This is a simplified conversion - you may need to extend this
    
    # Convert headings
    markdown_text = re.sub(r'^#{2} (.+)$', r'== \1', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^#{3} (.+)$', r'=== \1', markdown_text, flags=re.MULTILINE)
    
    # Convert bold
    markdown_text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', markdown_text)
    
    # Convert italic
    markdown_text = re.sub(r'\*(.+?)\*', r'_\1_', markdown_text)
    
    # Convert links
    markdown_text = re.sub(r'\[(.+?)\]\((.+?)\)', r'#link("\2")[\1]', markdown_text)
    
    # Convert lists
    markdown_text = re.sub(r'^\* (.+)$', r'- \1', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^\d+\. (.+)$', r'+ \1', markdown_text, flags=re.MULTILINE)
    
    # Convert code blocks
    markdown_text = re.sub(r'```(.+?)```', r'```\1```', markdown_text, flags=re.DOTALL)
    
    # Convert inline code
    markdown_text = re.sub(r'`(.+?)`', r'`\1`', markdown_text)
    
    return markdown_text

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