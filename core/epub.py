"""EPUB 3-export för OmaScribe-dokument."""

from __future__ import annotations

import html
import io
import os
import re
import uuid
import zipfile
from pathlib import Path

from lxml import etree
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QTextDocument, QTextFrame, QTextImageFormat

from core import richtext
from core.autocorrect import soft_hyphenate

_XHTML = "http://www.w3.org/1999/xhtml"
_XML = "http://www.w3.org/XML/1998/namespace"
_EPUB = "http://www.idpf.org/2007/ops"
_CONTAINER = "urn:oasis:names:tc:opendocument:xmlns:container"
_OPF = "http://www.idpf.org/2007/opf"
_DC = "http://purl.org/dc/elements/1.1/"


def _tag(name):
    return f"{{{_XHTML}}}{name}"


def _slug(text, used):
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
    candidate, index = base, 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _escape_text(text):
    return text.replace("\u2028", "\n")


def _render_block(block, doc, images, language="sv"):
    fmt = block.blockFormat()
    level = fmt.headingLevel()
    role = richtext.block_role(block)
    tag = f"h{min(level, 6)}" if level else ("blockquote" if role == richtext.ROLE_QUOTE else "pre" if role == richtext.ROLE_CODE else "p")
    node = etree.Element(_tag(tag))
    if role == richtext.ROLE_CODE:
        lang = richtext.lang_of(fmt)
        if lang:
            node.set("class", "language-" + re.sub(r"[^a-zA-Z0-9_+#.-]", "", lang))
    iterator = block.begin()
    while not iterator.atEnd():
        fragment = iterator.fragment()
        iterator += 1
        if not fragment.isValid():
            continue
        f = fragment.charFormat()
        text = fragment.text()
        # Mjuka bindestreck i löptext: svenskans långord är det som ger glapp i
        # en justerad spalt, och ett mjukt bindestreck syns bara om raden bryts
        # där. Aldrig i kod (pre) — den ska vara exakt som den skrevs. (R05.11)
        if tag in ("p", "blockquote"):
            text = soft_hyphenate(text, language)
        if f.isImageFormat():
            image_fmt = QTextImageFormat(f)
            name = image_fmt.name()
            resource = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(name))
            if hasattr(resource, "save"):
                key = name
                if key not in images:
                    buffer = io.BytesIO()
                    resource.save(buffer, "PNG")
                    number = sum(1 for item in images if item != "__cover__") + 1
                    images[key] = (buffer.getvalue(), "image/png", f"images/image{number}.png")
                img = etree.SubElement(node, _tag("img"))
                img.set("src", "../" + images[key][2])
                img.set("alt", image_fmt.alternateText() or "")
            continue
        if not text:
            continue
        target = node
        href = f.anchorHref()
        if href:
            target = etree.SubElement(node, _tag("a"))
            target.set("href", href)
        for active, wrapper in ((f.fontWeight() >= 600, "strong"), (f.fontItalic(), "em"), (f.fontUnderline(), "u")):
            if active:
                target = etree.SubElement(target, _tag(wrapper))
        if target is node:
            node.text = (node.text or "") + _escape_text(text)
        else:
            target.text = _escape_text(text)
    return node


def _serialize_xhtml(title, body_nodes, language="en"):
    root = etree.Element(_tag("html"), nsmap={None: _XHTML, "epub": _EPUB})
    root.set("lang", language)
    root.set(f"{{{_XML}}}lang", language)
    head = etree.SubElement(root, _tag("head"))
    etree.SubElement(head, _tag("title")).text = title
    link = etree.SubElement(head, _tag("link"))
    link.set("rel", "stylesheet")
    link.set("type", "text/css")
    link.set("href", "styles/book.css")
    body = etree.SubElement(root, _tag("body"))
    for node in body_nodes:
        body.append(node)
    return etree.tostring(root, xml_declaration=True, encoding="utf-8", doctype="<!DOCTYPE html>")


def _tables_in(frame):
    """Hämtar tabeller även från nästlade dokumentramar."""
    for child in frame.childFrames():
        if hasattr(child, "rows") and hasattr(child, "columns"):
            yield child
        yield from _tables_in(child)


def _render_table(table, document, images):
    result = etree.Element(_tag("table"))
    for row_index in range(table.rows()):
        row_node = etree.SubElement(result, _tag("tr"))
        for column_index in range(table.columns()):
            cell = table.cellAt(row_index, column_index)
            if not cell.isValid():
                continue
            cell_node = etree.SubElement(row_node, _tag("td"))
            block = cell.firstCursorPosition().block()
            end = cell.lastCursorPosition().block().position()
            while block.isValid():
                cell_node.append(_render_block(block, document, images))
                if block.position() >= end:
                    break
                block = block.next()
    return result


def _front_matter(meta: dict, title: str, language: str) -> list:
    """Titelsida och kolofon som egna XHTML-sidor (R05.4).

    Bokens första sidor är inte text man skriver — de är uppgifter man *har*:
    titeln, författaren, förlaget, ISBN och året. Att skriva dem för hand i en
    scen betyder att de ska hållas i minne och uppdateras för hand när något
    ändras; här kommer de ur projektet.
    """
    from datetime import date

    from core.i18n import _

    sidor = []
    titel_sida = etree.Element(_tag("h1"))
    titel_sida.text = title
    forfattare = etree.Element(_tag("p"))
    forfattare.set("class", "author")
    forfattare.text = str(meta.get("author") or "")
    sidor.append(("front-000-titel.xhtml", title, [titel_sida, forfattare]))

    kolofon_rader = [_("colophon_publisher", name=str(meta.get("publisher")))]
    if meta.get("identifier"):
        kolofon_rader.append(_("colophon_isbn", isbn=str(meta["identifier"])))
    kolofon_rader.append(_("colophon_year", year=str(meta.get("year") or date.today().year)))
    if meta.get("author"):
        kolofon_rader.append(_("colophon_rights", author=str(meta["author"])))
    noder = []
    rubrik = etree.Element(_tag("h2"))
    rubrik.text = _("colophon_title")
    noder.append(rubrik)
    for rad in kolofon_rader:
        stycke = etree.Element(_tag("p"))
        stycke.set("class", "colophon")
        stycke.text = rad
        noder.append(stycke)
    sidor.append(("front-001-kolofon.xhtml", _("colophon_title"), noder))
    return sidor


def export_epub(path: str, document: QTextDocument, metadata: dict, page_settings: dict | None = None) -> str:
    """Exporterar QTextDocument som en EPUB 3-bok."""
    del page_settings  # EPUB har flytande layout och använder inte utskriftens sidmått.
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    meta = metadata or {}
    title = str(meta.get("title") or "Untitled")
    language = str(meta.get("language") or "en")
    identifier = str(meta.get("identifier") or f"urn:uuid:{uuid.uuid4()}")
    image_data = {}
    used_ids = set()
    chapters = []
    current_title, current_nodes = "", []
    chapter_no = 0

    table_starts = {}
    table_ends = {}
    for table in _tables_in(document.rootFrame()):
        first = table.firstCursorPosition().block().position()
        last = table.lastCursorPosition().block().position()
        table_starts[first] = table
        table_ends[first] = last
    block = document.begin()
    while block.isValid():
        if block.position() in table_starts:
            current_nodes.append(_render_table(table_starts[block.position()], document, image_data))
            end_position = table_ends[block.position()]
            while block.isValid() and block.position() <= end_position:
                block = block.next()
            continue
        node = _render_block(block, document, image_data, language)
        if node.tag == _tag("h1"):
            if current_nodes or chapter_no:
                chapters.append((f"chapter-{chapter_no:03d}.xhtml", current_title or title, current_nodes))
            chapter_no += 1
            current_title = "".join(node.itertext()).strip() or f"Chapter {chapter_no}"
            current_nodes = []
            node.set("id", _slug(current_title, used_ids))
        elif node.tag in (_tag("h2"), _tag("h3")):
            node.set("id", _slug("".join(node.itertext()).strip(), used_ids))
        current_nodes.append(node)
        block = block.next()
    if current_nodes or not chapters:
        chapter_no += 1
        chapters.append((f"chapter-{chapter_no:03d}.xhtml", current_title or title, current_nodes))

    # Bokens första sidor läggs först, och hålls utanför innehållsförteckningen:
    # en titelsida listar sig inte själv i en innehållsförteckning.
    fran = _front_matter(meta, title, language)
    framsidor = {filnamn for filnamn, _titel, _noder in fran}
    chapters = fran + chapters

    # Ankare per H2/H3 blir lokala till respektive kapitel.
    chapter_nodes = []
    for filename, chapter_title, nodes in chapters:
        chapter_nodes.append((filename, chapter_title, nodes))

    nav = etree.Element(_tag("html"), nsmap={None: _XHTML, "epub": _EPUB})
    nav.set("lang", language)
    nav_head = etree.SubElement(nav, _tag("head"))
    etree.SubElement(nav_head, _tag("title")).text = "Contents"
    nav_body = etree.SubElement(nav, _tag("body"))
    toc = etree.SubElement(nav_body, _tag("nav"))
    toc.set(f"{{{_EPUB}}}type", "toc")
    etree.SubElement(toc, _tag("h1")).text = "Contents"
    ol = etree.SubElement(toc, _tag("ol"))
    for idx, (filename, chapter_title, nodes) in enumerate(chapter_nodes):
        if filename in framsidor:
            continue
        li = etree.SubElement(ol, _tag("li"))
        a = etree.SubElement(li, _tag("a")); a.set("href", filename + "#" + next((n.get("id") for n in nodes if n.tag == _tag("h1")), "")); a.text = chapter_title
        headings = [(int(n.tag[-1]), "".join(n.itertext()).strip(), n.get("id")) for n in nodes if n.tag in (_tag("h2"), _tag("h3"))]
        if headings:
            sub = etree.SubElement(li, _tag("ol"))
            for level, heading, anchor in headings:
                child = etree.SubElement(sub, _tag("li")); link = etree.SubElement(child, _tag("a")); link.set("href", filename + "#" + anchor); link.text = heading
    nav_bytes = etree.tostring(nav, xml_declaration=True, encoding="utf-8", doctype="<!DOCTYPE html>")

    container = etree.Element(f"{{{_CONTAINER}}}container", nsmap={None: _CONTAINER}, version="1.0")
    rootfiles = etree.SubElement(container, f"{{{_CONTAINER}}}rootfiles")
    etree.SubElement(rootfiles, f"{{{_CONTAINER}}}rootfile", {"full-path": "OEBPS/content.opf", "media-type": "application/oebps-package+xml"})
    container_bytes = etree.tostring(container, xml_declaration=True, encoding="utf-8")
    package = etree.Element(f"{{{_OPF}}}package", nsmap={None: _OPF, "dc": _DC}, version="3.0", **{"unique-identifier": "book-id"})
    md = etree.SubElement(package, f"{{{_OPF}}}metadata")
    for name, value in (("title", title), ("creator", meta.get("author")), ("language", language), ("publisher", meta.get("publisher")), ("description", meta.get("description"))):
        if value:
            etree.SubElement(md, f"{{{_DC}}}{name}").text = str(value)
    id_el = etree.SubElement(md, f"{{{_DC}}}identifier", id="book-id"); id_el.text = identifier
    for prop, val in (("accessMode", "textual"), ("accessibilityFeature", "tableOfContents"), ("accessibilityHazard", "none")):
        etree.SubElement(md, f"{{{_OPF}}}meta", property=prop).text = val
    manifest = etree.SubElement(package, f"{{{_OPF}}}manifest")
    etree.SubElement(manifest, f"{{{_OPF}}}item", id="nav", href="nav.xhtml", **{"media-type": "application/xhtml+xml", "properties": "nav"})
    etree.SubElement(manifest, f"{{{_OPF}}}item", id="css", href="styles/book.css", **{"media-type": "text/css"})
    spine = etree.SubElement(package, f"{{{_OPF}}}spine")
    for i, (filename, _, _) in enumerate(chapter_nodes):
        ident = f"chapter{i+1}"
        etree.SubElement(manifest, f"{{{_OPF}}}item", id=ident, href=filename, **{"media-type": "application/xhtml+xml"})
        etree.SubElement(spine, f"{{{_OPF}}}itemref", idref=ident)
    if meta.get("cover"):
        cover_path = Path(str(meta["cover"]))
        if cover_path.is_file():
            suffix = cover_path.suffix.lower() or ".jpg"
            content = cover_path.read_bytes()
            cover_name = "images/cover" + suffix
            mimetype = "image/png" if suffix == ".png" else "image/jpeg"
            image_data["__cover__"] = (content, mimetype, cover_name)
            etree.SubElement(manifest, f"{{{_OPF}}}item", id="cover-image", href=cover_name, **{"media-type": mimetype, "properties": "cover-image"})
    for i, (data, mime, filename) in enumerate(image_data.values()):
        etree.SubElement(manifest, f"{{{_OPF}}}item", id=f"image{i+1}", href=filename, **{"media-type": mime})
    opf_bytes = etree.tostring(package, xml_declaration=True, encoding="utf-8")
    temp = output.with_name(output.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with zipfile.ZipFile(temp, "w") as archive:
            archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            archive.writestr("META-INF/container.xml", container_bytes, compress_type=zipfile.ZIP_DEFLATED)
            archive.writestr("OEBPS/content.opf", opf_bytes, compress_type=zipfile.ZIP_DEFLATED)
            archive.writestr("OEBPS/nav.xhtml", nav_bytes, compress_type=zipfile.ZIP_DEFLATED)
            archive.writestr("OEBPS/styles/book.css", "body { font-family: serif; line-height: 1.45; }"
                " img { max-width: 100%; } table { border-collapse: collapse; }"
                " td, th { border: 1px solid; padding: .25em; }"
                # Rollerna ur core/richtext.py: samma innehåll, samma betydelse,
                # samma utseende i varje kanal (R05.3)
                " blockquote { margin: 0 0 0 1.5em; font-style: italic; }"
                " pre { white-space: pre-wrap; font-family: monospace;"
                " background: #f4f4f4; padding: .5em; border-left: 3px solid #ccc; }"
                " p.author { text-align: center; font-style: italic; margin-top: 2em; }"
                " p.colophon { font-size: .9em; }", compress_type=zipfile.ZIP_DEFLATED)
            for filename, chapter_title, nodes in chapter_nodes:
                archive.writestr("OEBPS/" + filename,
                                 _serialize_xhtml(chapter_title, nodes, language),
                                 compress_type=zipfile.ZIP_DEFLATED)
            for data, mime, name in image_data.values():
                archive.writestr("OEBPS/" + name, data, compress_type=zipfile.ZIP_DEFLATED)
        os.replace(temp, output)
    except Exception:
        try:
            temp.unlink(missing_ok=True)
        finally:
            raise
    return str(output)


def _self_test():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    doc = QTextDocument()
    doc.setHtml("<h1>First chapter</h1><p>Body</p><h2>Section</h2><table><tr><td>Cell</td></tr></table><h1>Second chapter</h1><p>End</p>")
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "sample.epub"
        export_epub(str(target), doc, {"title": "Test Book", "author": "Test Author", "language": "sv", "identifier": "ISBN-123"})
        with zipfile.ZipFile(target) as archive:
            names = archive.namelist()
            assert names[0] == "mimetype"
            assert archive.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
            assert "OEBPS/nav.xhtml" in names
            nav = archive.read("OEBPS/nav.xhtml").decode()
            assert "First chapter" in nav and "Second chapter" in nav
            chapters = [name for name in names if re.fullmatch(r"OEBPS/chapter-\d+\.xhtml", name)]
            assert len(chapters) == 2
            assert b"<table" in archive.read(chapters[0])
            # Bokens språk skall stå i kapitelroten, inte hårdkodat engelska —
            # en svensk bok märkt som engelsk får fel uppläsning och avstavning.
            from lxml import etree as _etree
            root_lang = _etree.fromstring(archive.read(chapters[0])).get("lang")
            assert root_lang == "sv", f"kapitlens lang är {root_lang!r}, inte bokens språk"
            opf = archive.read("OEBPS/content.opf").decode()
            assert "Test Book" in opf and "Test Author" in opf and "ISBN-123" in opf
            assert "accessMode" in opf and "accessibilityFeature" in opf and "accessibilityHazard" in opf
            assert archive.testzip() is None
        print("epub: 10 kontroller gröna")


if __name__ == "__main__":
    _self_test()
