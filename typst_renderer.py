"""
Typst renderer for mistletoe.
Produces Typst-compatible markup from a Markdown AST.
"""
import re
from itertools import chain
from typing import Iterable, Sequence

from mistletoe import block_token, span_token, token
from mistletoe.base_renderer import BaseRenderer
from mistletoe.markdown_renderer import BlankLine, LinkReferenceDefinitionBlock, LinkReferenceDefinition, Fragment


class TypstRenderer(BaseRenderer):
    """
    Typst renderer.

    Renders a Markdown AST into Typst markup.
    Inline images and links are emitted as Typst functions.
    Other elements use Markdown-like syntax accepted by Typst.
    """

    _whitespace = re.compile(r"\s+")

    def __init__(
        self,
        *extras,
        max_line_length: int = 72,
        normalize_whitespace=False
    ):
        # remove footnotes, as in MarkdownRenderer
        block_token.remove_token(block_token.Footnote)
        super().__init__(
            block_token.HtmlBlock,
            span_token.HtmlSpan,
            BlankLine,
            LinkReferenceDefinitionBlock,
            *extras,
        )
        # override some mappings
        self.render_map["SetextHeading"] = self.render_setext_heading
        self.render_map["CodeFence"] = self.render_fenced_code_block
        self.render_map["LinkReferenceDefinition"] = self.render_link_reference_definition
        # Typst-specific: override inline image and link
        self.render_map["Image"] = self.render_image
        self.render_map["Link"] = self.render_link

        self.max_line_length = max_line_length
        self.normalize_whitespace = normalize_whitespace
        # mapping for inline footnotes: number -> text
        self.footnotes = {}

    def slugify(self, text: str) -> str:
        """
        Create a slug from heading text: lowercase, remove non-word chars, spaces to hyphens.
        """
        s = text.lower()
        # replace non-alphanumeric characters with hyphen
        s = re.sub(r'[^\w]+', '-', s)
        # trim leading/trailing hyphens
        return s.strip('-')

    def render(self, token: token.Token) -> str:
        if isinstance(token, block_token.BlockToken):
            lines = self.render_map[token.__class__.__name__](
                token, max_line_length=self.max_line_length
            )
        else:
            lines = self.span_to_lines([token], max_line_length=self.max_line_length)
        # combine lines and adjust spacing
        text = "".join(line + "\n" for line in lines)
        # collapse extra blank line after heading anchor lines
        text = re.sub(r'(?m)^(<[^>]+>)\n\n', r'\1\n', text)
        return text

    # inline renderers
    def render_raw_text(self, token: span_token.RawText) -> Iterable[Fragment]:
        # handle inline footnote references and normal text
        text = token.content
        # split out any footnote references "[^n]"
        parts = re.split(r'(\[\^\d+\])', text)
        for part in parts:
            if not part:
                continue
            m = re.match(r'\[\^(?P<num>\d+)\]', part)
            if m:
                num = m.group('num')
                # insert Typst footnote macro
                foot = self.footnotes.get(num, '')
                yield Fragment(f'#footnote[{foot}]', wordwrap=True)
            else:
                # replace straight apostrophes with typographic curly apostrophes
                text = part.replace("'", "’")
                yield Fragment(text, wordwrap=True)

    def render_strong(self, token: span_token.Strong) -> Iterable[Fragment]:
        return self.embed_span(
            Fragment("#strong["),
            token.children,
            Fragment("]")
        )

    def render_emphasis(self, token: span_token.Emphasis) -> Iterable[Fragment]:
        return self.embed_span(
            Fragment("#emph["),
            token.children,
            Fragment("]")
        )

    def render_inline_code(self, token: span_token.InlineCode) -> Iterable[Fragment]:
        return self.embed_span(
            Fragment(token.delimiter + token.padding),
            token.children,
            Fragment(token.padding + token.delimiter)
        )

    def render_strikethrough(self, token: span_token.Strikethrough) -> Iterable[Fragment]:
        return self.embed_span(
            Fragment("#strike["),
            token.children,
            Fragment("]")
        )

    def render_image(self, token: span_token.Image) -> Iterable[Fragment]:
        # Typst: image("src", alt: "alt text")
        alt_text = "".join(f.text for f in self.make_fragments(token.children)).strip()
        src = token.src.replace('"', '\\"')
        if alt_text:
            alt = alt_text.replace('"', '\\"')
            yield Fragment(f'#image("{src}", alt: "{alt}")')
        else:
            yield Fragment(f'#image("{src}")')

    def render_link(self, token: span_token.Link) -> Iterable[Fragment]:
        # Typst inline link macro: #link("target")[text];
        text = "".join(f.text for f in self.make_fragments(token.children))
        url = token.target.replace('"', '\\"')
        # terminate macro with semicolon; raw text (e.g., period) follows
        yield Fragment(f'#link("{url}")[{text}];', wordwrap=False)

    def render_auto_link(self, token: span_token.AutoLink) -> Iterable[Fragment]:
        yield Fragment("<" + token.children[0].content + ">")

    def render_escape_sequence(self, token: span_token.EscapeSequence) -> Iterable[Fragment]:
        yield Fragment("\\" + token.children[0].content)

    def render_line_break(self, token: span_token.LineBreak) -> Iterable[Fragment]:
        yield Fragment(
            token.content + "\n", wordwrap=token.soft, hard_line_break=not token.soft
        )

    def render_html_span(self, token: span_token.HtmlSpan) -> Iterable[Fragment]:
        yield Fragment(token.content)

    def render_link_reference_definition(self, token: LinkReferenceDefinition) -> Iterable[Fragment]:
        # skip link reference definitions in Typst output
        return []

    # block renderers
    def render_document(
        self, token: block_token.Document, max_line_length: int
    ) -> Iterable[str]:
        # extract footnote definitions and build mapping, skip def blocks and following blank lines
        filtered_children = []
        children = token.children
        i = 0
        while i < len(children):
            child = children[i]
            # detect footnote definition paragraph: "[^n]: text"
            if isinstance(child, block_token.Paragraph) and len(child.children) == 1:
                span = child.children[0]
                if isinstance(span, span_token.RawText):
                    m = re.match(r'^\[\^(?P<num>\d+)\]:\s*(?P<txt>.*)', span.content)
                    if m:
                        # store footnote text
                        self.footnotes[m.group('num')] = m.group('txt')
                        # if definition follows a table, remove preceding blank line
                        if i > 1 and isinstance(children[i-2], block_token.Table):
                            # remove blankline before definition if present in filtered_children
                            if filtered_children and isinstance(filtered_children[-1], BlankLine):
                                filtered_children.pop()
                        # skip this definition
                        i += 1
                        # skip following blank line if present
                        if i < len(children) and isinstance(children[i], BlankLine):
                            i += 1
                        continue
            filtered_children.append(child)
            i += 1
        # render remaining blocks
        return self.blocks_to_lines(filtered_children, max_line_length=max_line_length)

    def render_heading(
        self, token: block_token.Heading, max_line_length: int
    ) -> Iterable[str]:
        marker = "=" * token.level
        # extract raw text and optional inline footnote number
        raw = token.children[0].content if token.children and isinstance(token.children[0], span_token.RawText) else ""
        m = re.match(r"(?P<txt>.*?)(?:\[\^(?P<num>\d+)\])?$", raw)
        text = m.group('txt') if m else raw
        num = m.group('num') if m and m.group('num') else None
        # build heading line with optional inline footnote
        if num:
            # insert footnote macro inline
            foot = self.footnotes.get(num, '')
            heading_line = f"{marker} {text}#footnote[{foot}]"
        else:
            heading_line = f"{marker} {text}"
        # create slug and append footnote number if present
        slug = self.slugify(text)
        if num:
            slug += num
        # heading and anchor lines
        return [heading_line, f"<{slug}>"]

    def render_setext_heading(
        self, token: block_token.SetextHeading, max_line_length: int
    ) -> Iterable[str]:
        yield from self.span_to_lines(token.children, max_line_length=max_line_length)
        yield token.underline

    def render_quote(
        self, token: block_token.Quote, max_line_length: int
    ) -> Iterable[str]:
        # Typst block quote macro
        # render inner blocks without indentation
        lines = self.blocks_to_lines(token.children, max_line_length=max_line_length)
        return [
            '#quote(block: true)[',
            *lines,
            ']',
        ]

    def render_paragraph(
        self, token: block_token.Paragraph, max_line_length: int
    ) -> Iterable[str]:
        return self.span_to_lines(token.children, max_line_length=max_line_length)

    def render_block_code(
        self, token: block_token.BlockCode, max_line_length: int
    ) -> Iterable[str]:
        lines = token.content.rstrip("\n").split("\n")
        return self.prefix_lines(lines, "    ")

    def render_fenced_code_block(
        self, token: block_token.BlockCode, max_line_length: int
    ) -> Iterable[str]:
        indent = " " * token.indentation
        yield indent + token.delimiter + token.info_string
        yield from self.prefix_lines(
            token.content[:-1].split("\n"), indent
        )
        yield indent + token.delimiter

    def render_list(
        self, token: block_token.List, max_line_length: int
    ) -> Iterable[str]:
        return self.blocks_to_lines(token.children, max_line_length=max_line_length)

    def render_list_item(
        self, token: block_token.ListItem, max_line_length: int
    ) -> Iterable[str]:
        # unify list markers: unordered lists use '-', ordered lists use '+'
        orig = token.leader
        if orig.endswith('.') and orig[:-1].isdigit():
            marker = '+'
        else:
            marker = '-'
        # marker plus a space
        prepend = len(marker) + 1
        indentation = 0
        max_child_len = (max_line_length - prepend if max_line_length else None)
        lines = self.blocks_to_lines(token.children, max_line_length=max_child_len)
        first_prefix = ' ' * indentation + f"{marker} "
        child_prefix = ' ' * prepend
        return self.prefix_lines(
            list(lines) or [''],
            first_prefix,
            child_prefix,
        )

    def render_table(
        self, token: block_token.Table, max_line_length: int
    ) -> Iterable[str]:
        # Typst figure and table macro rendering
        # extract header and row texts
        header = [
            next(self.span_to_lines(col.children, max_line_length=None), "")
            for col in token.header.children
        ]
        rows = [
            [
                next(self.span_to_lines(col.children, max_line_length=None), "")
                for col in row.children
            ]
            for row in token.children
        ]
        indent1 = '  '
        indent2 = '    '
        lines = []
        lines.append('#figure(')
        lines.append(f"{indent1}align(center)[#table(")
        lines.append(f"{indent2}columns: {len(header)},")
        align_tuple = ','.join(['auto'] * len(header)) + ','
        lines.append(f"{indent2}align: ({align_tuple}),")
        # header row
        header_args = ', '.join(f"[{h}]" for h in header) + ','
        lines.append(f"{indent2}table.header({header_args}),")
        lines.append(f"{indent2}table.hline(),")
        # data rows
        for row in rows:
            row_args = ', '.join(f"[{cell}]" for cell in row)
            lines.append(f"{indent2}{row_args},")
        lines.append(f"{indent1})]")
        lines.append(f"{indent1}, kind: table")
        lines.append(f"{indent1})")
        # blank line after table for spacing before next block
        lines.append("")
        return lines

    def render_thematic_break(
        self, token: block_token.ThematicBreak, max_line_length: int
    ) -> Iterable[str]:
        # horizontal rule
        return ["---"]

    def render_html_block(
        self, token: block_token.HtmlBlock, max_line_length: int
    ) -> Iterable[str]:
        return token.content.split("\n")

    def render_link_reference_definition_block(
        self, token: LinkReferenceDefinitionBlock, max_line_length: int
    ) -> Iterable[str]:
        return []

    def render_blank_line(
        self, token: BlankLine, max_line_length: int
    ) -> Iterable[str]:
        return [""]

    # helper methods (copied from MarkdownRenderer)
    def embed_span(
        self,
        leader: Fragment,
        tokens: Iterable[span_token.SpanToken],
        trailer: Fragment = None,
    ) -> Iterable[Fragment]:
        yield leader
        yield from self.make_fragments(tokens)
        yield trailer or leader

    def blocks_to_lines(
        self, tokens: Iterable[block_token.BlockToken], max_line_length: int
    ) -> Iterable[str]:
        for t in tokens:
            yield from self.render_map[t.__class__.__name__](
                t, max_line_length=max_line_length
            )

    def span_to_lines(
        self, tokens: Iterable[span_token.SpanToken], max_line_length: int
    ) -> Iterable[str]:
        fragments = self.make_fragments(tokens)
        return self.fragments_to_lines(fragments, max_line_length=max_line_length)

    def make_fragments(
        self, tokens: Iterable[span_token.SpanToken]
    ) -> Iterable[Fragment]:
        return chain.from_iterable(
            [self.render_map[token.__class__.__name__](token) for token in tokens]
        )

    @classmethod
    def fragments_to_lines(
        cls, fragments: Iterable[Fragment], max_line_length: int = None
    ) -> Iterable[str]:
        current_line = ""
        if not max_line_length:
            for fragment in fragments:
                if "\n" in fragment.text:
                    parts = fragment.text.split("\n")
                    yield current_line + parts[0]
                    for inner in parts[1:-1]:
                        yield inner
                    current_line = parts[-1]
                else:
                    current_line += fragment.text
        else:
            for word in cls.make_words(fragments):
                if word == "\n":
                    yield current_line
                    current_line = ""
                    continue
                if not current_line:
                    current_line = word
                    continue
                test = current_line + " " + word
                if len(test) <= max_line_length:
                    current_line = test
                else:
                    yield current_line
                    current_line = word
        if current_line:
            yield current_line

    @classmethod
    def make_words(cls, fragments: Iterable[Fragment]) -> Iterable[str]:
        word = ""
        for fragment in fragments:
            if getattr(fragment, "wordwrap", False):
                first = True
                for part in cls._whitespace.split(fragment.text):
                    if first:
                        word += part
                        first = False
                    else:
                        if word:
                            yield word
                        word = part
            elif getattr(fragment, "hard_line_break", False):
                yield from (word + fragment.text[:-1], "\n")
                word = ""
            else:
                word += fragment.text
        if word:
            yield word

    @classmethod
    def prefix_lines(
        cls,
        lines: Iterable[str],
        first_line_prefix: str,
        following_line_prefix: str = None,
    ) -> Iterable[str]:
        following_line_prefix = following_line_prefix or first_line_prefix
        first = True
        for line in lines:
            if first:
                prefixed = first_line_prefix + line
                first = False
            else:
                prefixed = following_line_prefix + line
            yield prefixed if not prefixed.isspace() else ""

    def table_row_to_text(self, row) -> Sequence[str]:
        return [
            next(self.span_to_lines(col.children, max_line_length=None), "")
            for col in row.children
        ]

    @classmethod
    def calculate_table_column_widths(cls, col_text) -> Sequence[int]:
        MIN_WIDTH = 3
        widths = []
        for row in col_text:
            while len(widths) < len(row):
                widths.append(MIN_WIDTH)
            for i, text in enumerate(row):
                widths[i] = max(widths[i], len(text))
        return widths

    @classmethod
    def table_separator_line_to_text(cls, col_widths, col_align) -> Sequence[str]:
        sep = []
        for i, w in enumerate(col_widths):
            align = col_align[i] if i < len(col_align) else None
            s = ":" if align == 0 else "-"
            s += "-" * (w - 2)
            s += ":" if align == 0 or align == 1 else "-"
            sep.append(s)
        return sep

    @classmethod
    def table_row_to_line(cls, col_text, col_widths, col_align) -> str:
        padded = []
        for i, w in enumerate(col_widths):
            txt = col_text[i] if i < len(col_text) else ""
            align = col_align[i] if i < len(col_align) else None
            if align is None:
                padded.append(f"{txt:<{w}}")
            elif align == 0:
                padded.append(f"{txt:^{w}}")
            else:
                padded.append(f"{txt:>{w}}")
        return "".join(("| ", " | ".join(padded), " |"))