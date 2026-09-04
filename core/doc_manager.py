import os
import re
from PyQt6.QtGui import QTextDocument, QTextCursor
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtCore import QMarginsF

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

class DocumentManager:
    @staticmethod
    def load_file(filepath, text_document: QTextDocument):
        """Loads a file (.docx, .md, .html, .txt) into a QTextDocument."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".docx":
            if docx is None:
                raise ImportError("python-docx is required to read .docx files.")
            doc = docx.Document(filepath)
            html_parts = []
            for p in doc.paragraphs:
                p_text = p.text
                if not p_text.strip():
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

                runs_html = []
                for run in p.runs:
                    txt = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    if run.bold:
                        txt = f"<b>{txt}</b>"
                    if run.italic:
                        txt = f"<i>{txt}</i>"
                    if run.underline:
                        txt = f"<u>{txt}</u>"
                    runs_html.append(txt)

                inner = "".join(runs_html) if runs_html else p_text
                html_parts.append(f"<{tag}>{inner}</{tag}>")

            text_document.setHtml("\n".join(html_parts))

        elif ext in {".md", ".markdown"}:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_md = f.read()
            if markdown:
                html = markdown.markdown(raw_md, extensions=["tables", "fenced_code"])
                text_document.setHtml(html)
            else:
                text_document.setPlainText(raw_md)

        elif ext in {".html", ".htm"}:
            with open(filepath, "r", encoding="utf-8") as f:
                html = f.read()
            text_document.setHtml(html)

        else:  # .txt or fallback
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            text_document.setPlainText(text)

    @staticmethod
    def save_file(filepath, text_document: QTextDocument):
        """Saves a QTextDocument to the specified format (.docx, .pdf, .md, .html, .txt)."""
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".docx":
            if docx is None:
                raise ImportError("python-docx is required to write .docx files.")
            doc = docx.Document()
            
            # Walk document blocks
            block = text_document.begin()
            while block.isValid():
                text = block.text()
                if text:
                    # Simple heading detection
                    fmt = block.blockFormat()
                    heading_level = fmt.headingLevel()
                    if heading_level == 1:
                        doc.add_heading(text, level=1)
                    elif heading_level == 2:
                        doc.add_heading(text, level=2)
                    elif heading_level == 3:
                        doc.add_heading(text, level=3)
                    else:
                        doc.add_paragraph(text)
                else:
                    doc.add_paragraph("")
                block = block.next()
            doc.save(filepath)

        elif ext == ".pdf":
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filepath)
            
            # A4 page layout with 20mm standard margins
            page_layout = QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Portrait,
                QMarginsF(20, 20, 20, 20),
                QPageLayout.Unit.Millimeter
            )
            printer.setPageLayout(page_layout)
            text_document.print(printer)

        elif ext in {".html", ".htm"}:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text_document.toHtml())

        elif ext in {".md", ".markdown"}:
            # Convert HTML to simplified Markdown
            raw_html = text_document.toHtml()
            md_text = DocumentManager.html_to_markdown(raw_html)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_text)

        else:  # .txt or plain text
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text_document.toPlainText())

    @staticmethod
    def html_to_markdown(html_content):
        """Converts basic Qt HTML formatting to readable Markdown."""
        text = html_content
        # Remove HTML head/style
        text = re.sub(r'<head>.*?</head>', '', text, flags=re.DOTALL)
        # Headings
        text = re.sub(r'<h1>(.*?)</h1>', r'# \1\n\n', text)
        text = re.sub(r'<h2>(.*?)</h2>', r'## \1\n\n', text)
        text = re.sub(r'<h3>(.*?)</h3>', r'### \1\n\n', text)
        # Bold & Italic
        text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
        text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)
        text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
        text = re.sub(r'<u>(.*?)</u>', r'_\1_', text)
        # Paragraphs & line breaks
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text)
        text = re.sub(r'<br\s*/?>', r'\n', text)
        # Lists
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'* \1\n', text)
        # Clean remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        # Fix multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip() + "\n"
