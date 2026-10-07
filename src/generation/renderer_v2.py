"""Multi-page document rendering.

Replaces the old single-canvas VisualRenderer, which silently truncated any
text that ran past one 800x1200 image (losing the very facts the benchmark
scores) and relied on macOS-only font paths. Everything here paginates.

Outputs:
- .pdf        multi-page typeset PDF (reportlab platypus)
- .docx       python-docx with headings/tables
- .scan.pdf   simulated scanned document: PIL-rendered pages with sepia,
              noise, and rotation, combined into a multi-page PDF (for the
              OCR/vision slice of the corpus)
- .md/.txt    passthrough
"""
import io
import os
import random
import re
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image as RLImage, PageBreak)

# ------------------------------------------------------------ markdown-lite

Block = Tuple[str, object]  # (kind, payload)


def parse_markdown(text: str) -> List[Block]:
    blocks: List[Block] = []
    lines = text.split("\n")
    i = 0
    para: List[str] = []

    def flush():
        if para:
            blocks.append(("p", " ".join(para).strip()))
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush()
        elif re.match(r"^#{1,6} ", line):
            flush()
            level = len(line) - len(line.lstrip("#"))
            blocks.append((f"h{min(level, 4)}", line.lstrip("#").strip()))
        elif line.strip().startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        elif re.match(r"^!\[[^\]]*\]\(([^)]+)\)", line.strip()):
            flush()
            m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", line.strip())
            blocks.append(("img", m.group(1)))
        elif re.match(r"^(\-|\*|\d+\.) ", line.strip()):
            flush()
            blocks.append(("li", re.sub(r"^(\-|\*|\d+\.) ", "", line.strip())))
        elif re.match(r"^(-{3,}|\*{3,})$", line.strip()):
            flush()
            blocks.append(("hr", None))
        else:
            para.append(line.strip())
        i += 1
    flush()
    return blocks


def _inline(text: str) -> str:
    """Markdown inline -> reportlab mini-HTML."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\[\[([^\]]+)\]\]", r"<i>\1</i>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def _plain(text: str) -> str:
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.replace("`", "")


# ------------------------------------------------------------------ PDF

def _styles(register: str):
    serif, mono = "Times-Roman", "Courier"
    body_font = mono if register == "codex" else serif
    return {
        "body": ParagraphStyle("body", fontName=body_font, fontSize=10.5, leading=15,
                               spaceAfter=7, alignment=4 if register == "chronicle" else 0),
        "h1": ParagraphStyle("h1", fontName="Times-Bold",
                             fontSize=19, leading=24, spaceBefore=16, spaceAfter=10),
        "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=15, leading=19,
                             spaceBefore=13, spaceAfter=8),
        "h3": ParagraphStyle("h3", fontName="Times-Bold", fontSize=12.5, leading=16,
                             spaceBefore=10, spaceAfter=6),
        "h4": ParagraphStyle("h4", fontName="Times-BoldItalic", fontSize=11, leading=14,
                             spaceBefore=8, spaceAfter=5),
        "li": ParagraphStyle("li", fontName=body_font, fontSize=10.5, leading=15,
                             leftIndent=16, bulletIndent=6, spaceAfter=3),
        "cell": ParagraphStyle("cell", fontName=body_font, fontSize=9, leading=12),
    }


def _blocks_to_flowables(blocks: List[Block], styles, image_root: Optional[str]):
    flow = []
    for kind, payload in blocks:
        if kind == "p":
            flow.append(Paragraph(_inline(payload), styles["body"]))
        elif kind in ("h1", "h2", "h3", "h4"):
            flow.append(Paragraph(_inline(payload), styles[kind]))
        elif kind == "li":
            flow.append(Paragraph(_inline(payload), styles["li"], bulletText="-"))
        elif kind == "hr":
            flow.append(Spacer(1, 10))
        elif kind == "table":
            rows = payload
            if not rows:
                continue
            data = [[Paragraph(_inline(c), styles["cell"]) for c in row] for row in rows]
            width = min(len(max(rows, key=len)), 6)
            t = Table(data, colWidths=[(17 * cm) / max(width, 1)] * width if width else None)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#5a4a38")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8dfc8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            flow.append(Spacer(1, 6))
            flow.append(t)
            flow.append(Spacer(1, 6))
        elif kind == "img" and image_root:
            path = os.path.normpath(os.path.join(image_root, payload))
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    ratio = img.height / img.width
                    w = 12 * cm
                    flow.append(Spacer(1, 6))
                    flow.append(RLImage(path, width=w, height=w * ratio))
                    flow.append(Spacer(1, 6))
                except Exception:
                    pass
    return flow


def render_pdf(sections: List[Tuple[str, str]], out_path: str,
               register: str = "chronicle", title: Optional[str] = None,
               image_root: Optional[str] = None):
    """sections: list of (section_title, markdown). Multiple sections = a book."""
    styles = _styles(register)
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            leftMargin=2.4 * cm, rightMargin=2.4 * cm,
                            topMargin=2.4 * cm, bottomMargin=2.4 * cm,
                            title=title or (sections[0][0] if sections else ""))
    flow = []
    if title:
        flow.append(Spacer(1, 160))
        flow.append(Paragraph(_inline(title), ParagraphStyle(
            "cover", fontName="Times-Bold", fontSize=26, leading=32, alignment=1)))
        flow.append(PageBreak())
    for idx, (sec_title, md) in enumerate(sections):
        if idx > 0:
            flow.append(PageBreak())
        blocks = parse_markdown(md)
        has_own_heading = any(k.startswith("h") for k, _ in blocks[:3])
        if sec_title and not has_own_heading:
            flow.append(Paragraph(_inline(sec_title), styles["h2"]))
        flow.extend(_blocks_to_flowables(blocks, styles, image_root))
    doc.build(flow)


# ----------------------------------------------------------------- DOCX

def render_docx(sections: List[Tuple[str, str]], out_path: str,
                title: Optional[str] = None, image_root: Optional[str] = None):
    import docx
    from docx.shared import Inches, Pt

    d = docx.Document()
    if title:
        d.add_heading(title, level=0)
    for sec_title, md in sections:
        blocks = parse_markdown(md)
        has_own_heading = any(k.startswith("h") for k, _ in blocks[:3])
        if sec_title and not has_own_heading:
            d.add_heading(sec_title, level=1)
        for kind, payload in blocks:
            if kind == "p":
                d.add_paragraph(_plain(payload))
            elif kind in ("h1", "h2", "h3", "h4"):  # not "hr", whose payload is None
                d.add_heading(_plain(payload), level=min(int(kind[1]), 4))
            elif kind == "li":
                d.add_paragraph(_plain(payload), style="List Bullet")
            elif kind == "table" and payload:
                rows = payload
                width = len(max(rows, key=len))
                t = d.add_table(rows=len(rows), cols=width)
                t.style = "Light Grid Accent 3"
                for r, row in enumerate(rows):
                    for c in range(width):
                        t.rows[r].cells[c].text = _plain(row[c]) if c < len(row) else ""
            elif kind == "img" and image_root:
                path = os.path.normpath(os.path.join(image_root, payload))
                if os.path.exists(path):
                    try:
                        d.add_picture(path, width=Inches(4.5))
                    except Exception:
                        pass
    d.save(out_path)


# ------------------------------------------------------------- scanned PDF

def _find_font(size: int) -> ImageFont.FreeTypeFont:
    for cand in [r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\times.ttf",
                 r"C:\Windows\Fonts\cour.ttf",
                 "/System/Library/Fonts/Times.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]:
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_scanned_pdf(markdown_text: str, out_path: str, seed: int = 0):
    """Simulated scan: paginated (never truncates), aged, noisy, slightly rotated."""
    rng = random.Random(seed)
    W, H = 1240, 1754  # ~A4 at 150dpi
    margin, leading = 120, 34
    font = _find_font(24)
    bold = _find_font(30)

    # Flatten markdown to plain lines and wrap them.
    import textwrap
    lines: List[Tuple[str, bool]] = []
    for kind, payload in parse_markdown(markdown_text):
        if kind in ("h1", "h2", "h3", "h4"):
            lines.append((_plain(payload).upper(), True))
            lines.append(("", False))
        elif kind == "hr":
            lines.append(("- - -", False))
            lines.append(("", False))
        elif kind == "p":
            for w in textwrap.wrap(_plain(payload), width=68):
                lines.append((w, False))
            lines.append(("", False))
        elif kind == "li":
            for j, w in enumerate(textwrap.wrap(_plain(payload), width=64)):
                lines.append((("  - " if j == 0 else "    ") + w, False))
        elif kind == "table" and payload:
            for row in payload:
                lines.append(("  " + " | ".join(_plain(c) for c in row), False))
            lines.append(("", False))

    per_page = (H - 2 * margin) // leading
    pages: List[Image.Image] = []
    for start in range(0, max(len(lines), 1), per_page):
        page = Image.new("RGB", (W, H), (238, 228, 205))
        draw = ImageDraw.Draw(page)
        y = margin
        for text, is_head in lines[start:start + per_page]:
            if text:
                draw.text((margin, y), text, font=bold if is_head else font, fill=(43, 30, 20))
            y += leading
        # Aging: blotches, edge shadow, noise, rotation.
        for _ in range(rng.randint(6, 14)):
            bx, by = rng.randint(0, W), rng.randint(0, H)
            r = rng.randint(2, 22)
            shade = rng.randint(170, 215)
            draw.ellipse([bx, by, bx + r, by + r], fill=(shade, shade - 15, shade - 45))
        page = page.rotate(rng.uniform(-1.2, 1.2), expand=False, fillcolor=(120, 108, 88))
        page = page.filter(ImageFilter.GaussianBlur(0.6))
        pages.append(page)

    pages[0].save(out_path, save_all=True, append_images=pages[1:], format="PDF",
                  resolution=150)


# --------------------------------------------------------------- dispatch

def render_document(markdown_text: str, fmt: str, out_path: str,
                    title: Optional[str] = None, register: str = "ephemera",
                    image_root: Optional[str] = None, seed: int = 0):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if fmt == ".pdf":
        render_pdf([(title or "", markdown_text)], out_path, register=register,
                   image_root=image_root)
    elif fmt == ".docx":
        render_docx([(title or "", markdown_text)], out_path, image_root=image_root)
    elif fmt == ".scan.pdf":
        render_scanned_pdf(markdown_text, out_path, seed=seed)
    else:  # .md / .txt
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
