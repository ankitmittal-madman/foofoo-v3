#!/usr/bin/env python3
"""Small, dependency-free Markdown renderer for the FooFoo PRD.

It supports the subset used by the document and leaves Mermaid rendering to
the browser. The generated HTML is intentionally kept beside the PDF so the
print layout can be reviewed without rebuilding the source.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path


def inline(value: str) -> str:
    code_fragments: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        code_fragments.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"@@CODE{len(code_fragments) - 1}@@"

    value = re.sub(r"`([^`]+)`", stash_code, value.strip())
    value = html.escape(value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    for index, fragment in enumerate(code_fragments):
        value = value.replace(f"@@CODE{index}@@", fragment)
    return value


def render_table(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    header = rows[0]
    body = rows[2:]
    out = ["<div class=table-wrap><table><thead><tr>"]
    out.extend(f"<th>{inline(cell)}</th>" for cell in header)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{inline(cell)}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def markdown_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    in_list: str | None = None

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>")
            in_list = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "<!-- PAGEBREAK -->":
            close_list()
            out.append('<div class="page-break"></div>')
            i += 1
            continue

        if stripped.startswith("```"):
            close_list()
            lang = stripped[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code = "\n".join(code_lines)
            if lang == "mermaid":
                out.append(f'<div class="diagram"><div class="mermaid">{html.escape(code)}</div></div>')
            else:
                out.append(f'<pre class="code {html.escape(lang)}"><code>{html.escape(code)}</code></pre>')
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[i + 1]):
            close_list()
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(render_table(table_lines))
            continue

        match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if match:
            close_list()
            level = len(match.group(1))
            title = match.group(2)
            cls = "part-title" if level == 1 and title.startswith("Part ") else ""
            out.append(f'<h{level} class="{cls}">{inline(title)}</h{level}>')
            i += 1
            continue

        if stripped.startswith("> "):
            close_list()
            out.append(f"<blockquote>{inline(stripped[2:])}</blockquote>")
            i += 1
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        numbered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if bullet or numbered:
            wanted = "ul" if bullet else "ol"
            if in_list != wanted:
                close_list()
                in_list = wanted
                out.append(f"<{wanted}>")
            out.append(f"<li>{inline((bullet or numbered).group(1))}</li>")
            i += 1
            continue

        if not stripped:
            close_list()
            i += 1
            continue

        if stripped == "---":
            close_list()
            out.append("<hr>")
            i += 1
            continue

        close_list()
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "|", "```", ">", "<!--", "- ", "* ")) or re.match(r"^\d+\.\s+", nxt):
                break
            para.append(nxt)
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    close_list()
    return "\n".join(out)


CSS = r"""
@page { size: A4; margin: 14mm 14mm 15mm; }
* { box-sizing: border-box; }
html { color: #2f302d; background: #f3eee4; }
body { margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 9.3pt; line-height: 1.38; background: white; }
main { max-width: 210mm; margin: auto; padding: 18mm 14mm; }
h1, h2, h3, h4 { color: #402d20; page-break-after: avoid; }
h1 { font-size: 26pt; line-height: 1.05; margin: 0 0 8mm; letter-spacing: -0.4px; }
h2 { font-size: 18pt; margin: 0 0 4mm; border-bottom: 2px solid #ee8d35; padding-bottom: 2mm; }
h3 { font-size: 12.5pt; margin: 4mm 0 2mm; color: #9a4d16; }
h4 { font-size: 10.5pt; margin: 3mm 0 1.5mm; }
p { margin: 0 0 3mm; orphans: 3; widows: 3; }
ul, ol { margin: 1.5mm 0 3mm 5mm; padding-left: 4mm; }
li { margin: 0.8mm 0; }
blockquote { margin: 6mm 0; padding: 5mm; border-left: 4px solid #ee8d35; background: #fff5e8; color: #5c3a22; font-size: 12pt; }
strong { color: #2b211a; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.2pt; background: #f5f1eb; padding: 0.2mm 0.7mm; border-radius: 2px; }
pre.code { white-space: pre-wrap; overflow-wrap: anywhere; background: #282622; color: #fff9ef; padding: 4mm; border-radius: 4px; font-size: 7.6pt; line-height: 1.35; page-break-inside: avoid; }
pre.code code { color: inherit; background: transparent; padding: 0; }
.table-wrap { margin: 3mm 0 4mm; }
table { width: 100%; border-collapse: collapse; font-size: 7.75pt; line-height: 1.28; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th { background: #5c3924; color: white; text-align: left; padding: 2.2mm; border: 0.3px solid #86634d; }
td { vertical-align: top; padding: 2mm; border: 0.3px solid #d8c9b9; }
tbody tr:nth-child(even) { background: #fbf7f1; }
a { color: #a65317; text-decoration: none; }
hr { border: 0; border-top: 1px solid #d7c7b4; margin: 6mm 0; }
.page-break { break-before: page; page-break-before: always; height: 0; }
.diagram { margin: 4mm 0; padding: 3mm; border: 1px solid #ead5bf; border-radius: 5px; background: #fffbf6; page-break-inside: avoid; text-align: center; }
.diagram svg { max-width: 100% !important; max-height: 150mm; }
.mermaid { font-size: 8pt; }
.part-title { color: #a34e13; font-size: 27pt; margin-top: 35mm; border-top: 5px solid #ee8d35; padding-top: 8mm; }
body > main > h1:first-child { font-size: 42pt; margin-top: 38mm; color: #d96b1c; }
body > main > h1:first-child + h2 { font-size: 21pt; border: 0; max-width: 150mm; }
@media print {
  html, body { background: white; }
  main { padding: 0; max-width: none; }
}
"""


def main() -> None:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else "FooFoo_Comprehensive_PRD_and_Bibles.md")
    target = Path(sys.argv[2] if len(sys.argv) > 2 else source.with_suffix(".html"))
    body = markdown_to_html(source.read_text(encoding="utf-8"))
    document = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>FooFoo Comprehensive PRD and Intelligence Bibles</title>
<style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
</head><body><main>{body}</main>
<script>
mermaid.initialize({{startOnLoad:true, theme:'base', securityLevel:'loose',
 themeVariables:{{primaryColor:'#fff0df',primaryTextColor:'#3e2c20',primaryBorderColor:'#dd7a2d',lineColor:'#a65a24',secondaryColor:'#f4eadf',tertiaryColor:'#fffaf4',fontFamily:'Arial'}}}});
</script></body></html>"""
    target.write_text(document, encoding="utf-8")
    print(target.resolve())


if __name__ == "__main__":
    main()
