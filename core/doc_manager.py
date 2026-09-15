import os
import re
from PyQt6.QtCore import Qt, QMarginsF, QRectF, QSizeF
from PyQt6.QtGui import (
    QTextDocument, QTextCursor, QPageLayout, QPageSize,
    QFont, QColor, QPainter, QPen, QAbstractTextDocumentLayout
)
from PyQt6.QtPrintSupport import QPrinter

try:
    import docx
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    docx = None

try:
    import markdown
except ImportError:
    markdown = None

from core import richtext
from core.i18n import _

# ```-block i Markdown, med valfritt språk
_FENCE_RE = re.compile(r"^```([A-Za-z0-9_+#.\-]*)[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
# Platshållaren som tillfälligt ersätter ett kodblock under HTML-konverteringen
_FENCE_PLACEHOLDER_RE = re.compile(r"^OmaScribeKodblock(\d+)Z$")

# En rad som bara består av #taggar (Obsidian-stil), inte en rubrik.
TAG_LINE_RE = re.compile(r"^(?:#[^\W_][\w\-/]*\s*)+$")

DEFAULT_PAGE_SETTINGS = {
    "page_size": "A4",                   # "A4", "Letter"
    "orientation": "portrait",           # "portrait", "landscape"
    "margin_top_mm": 20.0,
    "margin_bottom_mm": 20.0,
    "margin_left_mm": 20.0,
    "margin_right_mm": 20.0,
    "page_numbering": True,              # True / False
    "page_number_pos": "bottom-center",  # "bottom-center", "bottom-right", "bottom-alternating", "top-right", "top-alternating", "none"
    "page_number_format": "page_of_total", # "number", "page_of_total", "hyphen", "slash"
    "skip_first_page": False,            # True för att dölja på titelsida/framsida
    "header_text": "",                   # Löpande sidhuvud
    "footer_text": "",                   # Löpande sidfot
}


class DocumentManager:
    @staticmethod
    def _is_docx_file(filepath):
        try:
            with open(filepath, "rb") as f:
                return f.read(4) == b"PK\x03\x04"
        except Exception:
            return False

    @staticmethod
    def load_file(filepath, text_document: QTextDocument, colors=None):
        """Loads a file (.docx, .md, .html, .txt) into a QTextDocument preserving rich formatting."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".docx" or (not ext and DocumentManager._is_docx_file(filepath)):
            if docx is None:
                raise ImportError("python-docx is required to read .docx files.")
            doc = docx.Document(filepath)
            html_parts = []
            
            for p in doc.paragraphs:
                p_text = p.text
                if not p_text.strip() and not p.runs:
                    html_parts.append("<p><br/></p>")
                    continue

                style_name = p.style.name.lower() if p.style else ""
                tag = "p"
                if "heading 1" in style_name:
                    tag = "h1"
                elif "heading 2" in style_name:
                    tag = "h2"
                elif "heading 3" in style_name:
                    tag = "h3"
                elif "title" in style_name:
                    tag = "h1"
                elif "quote" in style_name:
                    tag = "blockquote"

                align_style = ""
                if p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                    align_style = "text-align: center;"
                elif p.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
                    align_style = "text-align: right;"
                elif p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
                    align_style = "text-align: justify;"

                runs_html = []
                for run in p.runs:
                    txt = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                    
                    span_styles = []
                    if run.font.name:
                        span_styles.append(f"font-family: '{run.font.name}';")
                    if run.font.size:
                        span_styles.append(f"font-size: {run.font.size.pt}pt;")
                    if run.font.color and run.font.color.rgb:
                        span_styles.append(f"color: #{run.font.color.rgb};")
                        
                    if run.bold:
                        txt = f"<b>{txt}</b>"
                    if run.italic:
                        txt = f"<i>{txt}</i>"
                    if run.underline:
                        txt = f"<u>{txt}</u>"
                    if run.font.strike:
                        txt = f"<s>{txt}</s>"
                        
                    if span_styles:
                        txt = f'<span style="{" ".join(span_styles)}">{txt}</span>'
                        
                    runs_html.append(txt)

                inner = "".join(runs_html) if runs_html else p_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                style_attr = f' style="{align_style}"' if align_style else ""
                html_parts.append(f"<{tag}{style_attr}>{inner}</{tag}>")

            # Load docx tables if present
            for tbl in doc.tables:
                tbl_html = ['<table border="1" cellpadding="6" style="border-collapse: collapse; margin: 12px 0;">']
                for row in tbl.rows:
                    tbl_html.append("<tr>")
                    for cell in row.cells:
                        cell_txt = cell.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        tbl_html.append(f'<td style="padding: 6px; border: 1px solid #cbd5e1;">{cell_txt}</td>')
                    tbl_html.append("</tr>")
                tbl_html.append("</table>")
                html_parts.append("".join(tbl_html))

            text_document.setHtml("".join(html_parts))

        elif ext in {".html", ".htm"}:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            text_document.setHtml(content)

        elif ext in {".md", ".markdown"}:
            with open(filepath, "r", encoding="utf-8") as f:
                md_text = f.read()

            fences = []
            def _stash(m):
                idx = len(fences)
                fences.append((m.group(1) or "", m.group(2)))
                return f"OmaScribeKodblock{idx}Z"

            stashed_md = _FENCE_RE.sub(_stash, md_text)

            clean_lines = []
            for line in stashed_md.splitlines():
                if TAG_LINE_RE.match(line):
                    line = "&#35;" + line[1:]
                clean_lines.append(line)
            stashed_md = "\n".join(clean_lines)

            if markdown:
                html_content = markdown.markdown(
                    stashed_md,
                    extensions=["extra", "tables", "nl2br", "sane_lists"]
                )
            else:
                html_content = f"<pre>{stashed_md}</pre>"

            text_document.setHtml(html_content)

            if fences:
                doc = text_document
                for idx, (lang, code) in enumerate(fences):
                    token = f"OmaScribeKodblock{idx}Z"
                    cursor = doc.find(token)
                    while not cursor.isNull():
                        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
                        if cursor.selectedText() != token:
                            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                        b_first = cursor.blockNumber()
                        cursor.beginEditBlock()
                        try:
                            cursor.removeSelectedText()
                            cursor.insertText(code.rstrip("\n"))
                            b_last = cursor.blockNumber()
                        finally:
                            cursor.endEditBlock()

                        sel = QTextCursor(doc)
                        sel.setPosition(doc.findBlockByNumber(b_first).position())
                        sel.setPosition(
                            doc.findBlockByNumber(b_last).position() + doc.findBlockByNumber(b_last).length() - 1,
                            QTextCursor.MoveMode.KeepAnchor
                        )
                        richtext.apply_role(sel, richtext.ROLE_CODE, colors or {}, lang)
                        cursor = doc.find(token)

        else:  # .txt or plain text
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            text_document.setPlainText(content)

    @staticmethod
    def print_document_to_printer(text_document: QTextDocument, printer: QPrinter, page_settings: dict | None = None):
        """Utskrift och PDF-generering med 100% formateringstrogenhet, sidnummer och sidhuvud/sidfot."""
        cfg = DEFAULT_PAGE_SETTINGS.copy()
        if page_settings:
            cfg.update(page_settings)

        # 1. Konfigurera sidlayout
        is_landscape = cfg.get("orientation") == "landscape"
        orient = QPageLayout.Orientation.Landscape if is_landscape else QPageLayout.Orientation.Portrait
        page_size_id = QPageSize.PageSizeId.Letter if cfg.get("page_size") == "Letter" else QPageSize.PageSizeId.A4
        
        margins = QMarginsF(
            float(cfg.get("margin_left_mm", 20.0)),
            float(cfg.get("margin_top_mm", 20.0)),
            float(cfg.get("margin_right_mm", 20.0)),
            float(cfg.get("margin_bottom_mm", 20.0))
        )
        page_layout = QPageLayout(QPageSize(page_size_id), orient, margins, QPageLayout.Unit.Millimeter)
        printer.setPageLayout(page_layout)

        # 2. Beräkna utskriftsmått i pixlar
        paint_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        
        # Reservera utrymme för sidhuvud och sidfot i pixlar
        has_header = bool(cfg.get("header_text")) or "top" in str(cfg.get("page_number_pos", ""))
        has_footer = bool(cfg.get("footer_text")) or ("bottom" in str(cfg.get("page_number_pos", "bottom-center")) and cfg.get("page_number_pos") != "none")
        
        # Pixels per mm vid aktuell upplösning
        dpmm = printer.resolution() / 25.4
        header_h = (8.0 * dpmm) if has_header else 0.0
        footer_h = (8.0 * dpmm) if has_footer else 0.0

        content_w = paint_rect.width()
        content_h = paint_rect.height() - header_h - footer_h

        # 3. Klona dokumentet för layout utan att röra originalet
        doc_clone = text_document.clone()
        if doc_clone is None:
            return
        doc_clone.setPageSize(QSizeF(content_w, content_h))
        page_count = max(1, doc_clone.pageCount())

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        font_hf = QFont("sans-serif", 9)
        color_hf = QColor("#64748b")

        try:
            for page_idx in range(page_count):
                if page_idx > 0:
                    printer.newPage()

                page_num = page_idx + 1
                skip_page = bool(cfg.get("skip_first_page", False)) and (page_idx == 0)

                # Formatera sidnumret
                fmt_type = cfg.get("page_number_format", "page_of_total")
                if fmt_type == "number":
                    page_str = str(page_num)
                elif fmt_type == "hyphen":
                    page_str = f"— {page_num} —"
                elif fmt_type == "slash":
                    page_str = f"{page_num} / {page_count}"
                else:  # "page_of_total"
                    page_str = _("pdf_page_n_of_total", n=page_num, total=page_count)

                num_pos = str(cfg.get("page_number_pos", "bottom-center"))
                
                # Bestäm justering för sidnumret
                if num_pos in ("bottom-alternating", "top-alternating"):
                    # Udda sidor till höger, jämna till vänster (bok/avhandlingsstandard)
                    is_right = (page_num % 2 == 1)
                    align_num = Qt.AlignmentFlag.AlignRight if is_right else Qt.AlignmentFlag.AlignLeft
                elif "right" in num_pos:
                    align_num = Qt.AlignmentFlag.AlignRight
                elif "left" in num_pos:
                    align_num = Qt.AlignmentFlag.AlignLeft
                else:
                    align_num = Qt.AlignmentFlag.AlignHCenter

                # --- 1. RITA SIDHUVUD ---
                if has_header and not skip_page:
                    painter.setFont(font_hf)
                    painter.setPen(color_hf)
                    header_rect = QRectF(0, 0, content_w, header_h)
                    
                    if cfg.get("header_text"):
                        painter.drawText(header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(cfg.get("header_text")))
                    
                    if "top" in num_pos and cfg.get("page_numbering", True):
                        painter.drawText(header_rect, align_num | Qt.AlignmentFlag.AlignTop, page_str)

                    # Tunn linje under sidhuvud
                    pen_line = QPen(QColor("#e2e8f0"), 0.75)
                    painter.setPen(pen_line)
                    painter.drawLine(0, int(header_h - (2 * dpmm)), int(content_w), int(header_h - (2 * dpmm)))

                # --- 2. RITA DOKUMENTSIDA ---
                painter.save()
                # Flytta origo till sidans innehållsyta
                painter.translate(0, header_h - (page_idx * content_h))
                
                # Klipp mot aktuell sidas del av dokumentet
                page_clip = QRectF(0, page_idx * content_h, content_w, content_h)
                painter.setClipRect(page_clip)

                ctx = QAbstractTextDocumentLayout.PaintContext()
                ctx.clip = page_clip
                ctx.cursorPosition = -1
                layout = doc_clone.documentLayout()
                if layout is not None:
                    layout.draw(painter, ctx)
                painter.restore()

                # --- 3. RITA SIDFOT ---
                if has_footer and not skip_page:
                    painter.setFont(font_hf)
                    painter.setPen(color_hf)
                    footer_y = header_h + content_h + (2 * dpmm)
                    footer_rect = QRectF(0, footer_y, content_w, footer_h)

                    # Tunn linje ovanför sidfot
                    pen_line = QPen(QColor("#e2e8f0"), 0.75)
                    painter.setPen(pen_line)
                    painter.drawLine(0, int(footer_y), int(content_w), int(footer_y))

                    if cfg.get("footer_text"):
                        painter.drawText(footer_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(cfg.get("footer_text")))

                    if "bottom" in num_pos and cfg.get("page_numbering", True):
                        painter.drawText(footer_rect, align_num | Qt.AlignmentFlag.AlignVCenter, page_str)

        finally:
            painter.end()

    @staticmethod
    def save_file(filepath, text_document: QTextDocument, colors=None, page_settings: dict = None):
        """Saves a QTextDocument to a file (.docx, .md, .html, .txt, .pdf) preserving all formatting."""
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".docx":
            if docx is None:
                raise ImportError("python-docx is required to write .docx files.")
            doc = docx.Document()
            block = text_document.begin()
            
            while block.isValid():
                fmt = block.blockFormat()
                heading_level = fmt.headingLevel()
                alignment = fmt.alignment()
                text_list = block.textList()
                
                if heading_level == 1:
                    p = doc.add_heading(level=1)
                elif heading_level == 2:
                    p = doc.add_heading(level=2)
                elif heading_level == 3:
                    p = doc.add_heading(level=3)
                elif text_list is not None:
                    p = doc.add_paragraph(style="List Bullet")
                else:
                    p = doc.add_paragraph()
                    
                if alignment & Qt.AlignmentFlag.AlignHCenter:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif alignment & Qt.AlignmentFlag.AlignRight:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif alignment & Qt.AlignmentFlag.AlignJustify:
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                elif alignment & Qt.AlignmentFlag.AlignLeft:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    if frag.isValid():
                        raw_txt = frag.text()
                        txt = raw_txt.replace('\ufffc', '')
                        if txt:
                            char_fmt = frag.charFormat()
                            run = p.add_run(txt)
                            
                            if char_fmt.fontWeight() >= 600 or char_fmt.font().bold():
                                run.bold = True
                            if char_fmt.fontItalic():
                                run.italic = True
                            if char_fmt.fontUnderline():
                                run.underline = True
                            if char_fmt.fontStrikeOut():
                                run.font.strike = True
                            try:
                                fam = char_fmt.font().family()
                                if fam and fam.lower() not in {"default", "sans-serif", "serif"}:
                                    run.font.name = fam
                            except Exception:
                                pass
                            pt_sz = char_fmt.fontPointSize()
                            if pt_sz > 0:
                                run.font.size = Pt(pt_sz)
                            fg = char_fmt.foreground().color()
                            if fg.isValid() and fg.name() != "#000000":
                                run.font.color.rgb = RGBColor(fg.red(), fg.green(), fg.blue())
                                
                    it += 1
                block = block.next()
                
            doc.save(filepath)

        elif ext == ".pdf":
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filepath)
            DocumentManager.print_document_to_printer(text_document, printer, page_settings)

        elif ext in {".html", ".htm"}:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text_document.toHtml())

        elif ext in {".md", ".markdown"}:
            md_text = DocumentManager.document_to_markdown(text_document)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_text)

        else:  # .txt or plain text
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text_document.toPlainText())

    @staticmethod
    def document_to_markdown(text_document: QTextDocument) -> str:
        """Converts a QTextDocument to rich Markdown preserving headings, bold, italic, strike, lists, quotes."""
        md_lines = []
        block = text_document.begin()
        
        while block.isValid():
            if richtext.block_role(block) == richtext.ROLE_CODE:
                lang = richtext.lang_of(block.blockFormat())
                code_lines = []
                while block.isValid() and richtext.block_role(block) == richtext.ROLE_CODE:
                    if not lang:
                        lang = richtext.lang_of(block.blockFormat())
                    code_lines.append(block.text())
                    block = block.next()
                while code_lines and not code_lines[0].strip():
                    code_lines.pop(0)
                while code_lines and not code_lines[-1].strip():
                    code_lines.pop()
                md_lines.append(f"```{lang}\n" + "\n".join(code_lines) + "\n```\n")
                continue

            fmt = block.blockFormat()
            heading_level = fmt.headingLevel()
            text_list = block.textList()
            role = richtext.block_role(block)
            is_quote = role == richtext.ROLE_QUOTE or (not role and fmt.leftMargin() >= 20)
            
            prefix = ""
            if heading_level == 1:
                prefix = "# "
            elif heading_level == 2:
                prefix = "## "
            elif heading_level == 3:
                prefix = "### "
            elif text_list is not None:
                prefix = "* "
            elif is_quote:
                prefix = "> "
                
            line_parts = []
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    txt = frag.text().replace('\ufffc', '')
                    if txt:
                        cf = frag.charFormat()
                        is_bold = (cf.fontWeight() >= 600 or cf.font().bold()) \
                            and heading_level not in (1, 2, 3)
                        is_italic = cf.fontItalic() and role != richtext.ROLE_QUOTE
                        is_strike = cf.fontStrikeOut()
                        is_underline = cf.fontUnderline()
                        
                        part = txt
                        if is_bold and is_italic:
                            part = f"***{part}***"
                        elif is_bold:
                            part = f"**{part}**"
                        elif is_italic:
                            part = f"*{part}*"
                        elif is_underline:
                            part = f"_{part}_"
                        if is_strike:
                            part = f"~~{part}~~"
                        line_parts.append(part)
                it += 1
                
            line_str = "".join(line_parts)
            if prefix and line_str:
                md_lines.append(f"{prefix}{line_str}\n")
            elif line_str:
                md_lines.append(f"{line_str}\n")
            else:
                md_lines.append("\n")
                
            block = block.next()
            
        full_md = "\n".join(md_lines)
        full_md = re.sub(r'\n{3,}', '\n\n', full_md)
        return full_md.strip() + "\n"
