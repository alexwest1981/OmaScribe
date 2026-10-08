"""Geometry helpers for a manuscript standard page (Normseite).

The monospaced character width is modeled as 0.6 em, a common Courier-style
advance width. Hyphenation is disabled because it changes characters per line.
"""

CHARS_PER_LINE = 60
LINES_PER_PAGE = 30
MONO_CHAR_WIDTH_EM = 0.6


def _mm(value: float) -> float:
    """Round a millimeter measurement to a practical tenth of a millimeter."""
    return round(float(value) + 0.0, 1)


def page_geometry(lines: int = LINES_PER_PAGE, chars: int = CHARS_PER_LINE,
                  font_pt: float = 12.0, line_spacing: float = 2.0,
                  page_w_mm: float = 210.0, page_h_mm: float = 297.0,
                  margin_h_mm: float = 25.0, margin_v_mm: float = 20.0) -> dict:
    """Calculate text capacity and occupied dimensions in millimeters."""
    font_pt = float(font_pt)
    line_spacing = float(line_spacing)
    char_w = font_pt * MONO_CHAR_WIDTH_EM * 25.4 / 72.0
    line_h = font_pt * line_spacing * 25.4 / 72.0
    content_w = float(page_w_mm) - 2.0 * float(margin_h_mm)
    content_h = float(page_h_mm) - 2.0 * float(margin_v_mm)
    text_w = int(chars) * char_w
    text_h = int(lines) * line_h
    return {
        "page_w_mm": _mm(page_w_mm), "page_h_mm": _mm(page_h_mm),
        "content_w_mm": _mm(content_w), "content_h_mm": _mm(content_h),
        "char_w_mm": _mm(char_w), "line_h_mm": _mm(line_h),
        "chars_per_line": int(chars), "lines_per_page": int(lines),
        "chars_per_page": int(lines) * int(chars),
        "text_w_mm": _mm(text_w), "text_h_mm": _mm(text_h),
    }


def fits(geometry: dict) -> list[str]:
    """Return Swedish explanations for dimensions that exceed the text area."""
    problems = []
    chars = geometry.get("chars_per_line", 0)
    lines = geometry.get("lines_per_page", 0)
    char_w = geometry.get("char_w_mm", 0.0)
    line_h = geometry.get("line_h_mm", 0.0)
    text_w = geometry.get("text_w_mm", 0.0)
    text_h = geometry.get("text_h_mm", 0.0)
    content_w = geometry.get("content_w_mm", 0.0)
    content_h = geometry.get("content_h_mm", 0.0)
    if char_w <= 0 or line_h <= 0:
        problems.append("Teckenbredd och radhöjd måste vara större än noll.")
    if chars < 0 or lines < 0:
        problems.append("Antalet tecken och rader får inte vara negativt.")
    if text_w > content_w:
        problems.append(
            f"{chars} tecken à {char_w:.1f} mm kräver {text_w:.1f} mm; "
            f"textytan är {content_w:.1f} mm — öka sidan eller minska stilmallen."
        )
    if text_h > content_h:
        problems.append(
            f"{lines} rader à {line_h:.1f} mm kräver {text_h:.1f} mm; "
            f"textytan är {content_h:.1f} mm — öka sidan eller minska stilmallen."
        )
    return problems


def norm_page(lines: int = LINES_PER_PAGE, chars: int = CHARS_PER_LINE,
              font_pt: float = 12.0, line_spacing: float = 2.0,
              trim: str = "A4") -> dict:
    """Build page settings and calculated geometry for a standard page."""
    trim_dims = {"A4": (210.0, 297.0), "A5": (148.0, 210.0), "LETTER": (215.9, 279.4)}
    page_w, page_h = trim_dims.get(str(trim).upper(), trim_dims["A4"])
    char_w = float(font_pt) * MONO_CHAR_WIDTH_EM * 25.4 / 72.0
    # Split the remaining page width evenly after calculating the requested text width.
    margin_h = (page_w - int(chars) * char_w) / 2.0
    margin_h = max(0.0, margin_h)
    margin_v = 20.0
    geometry = page_geometry(lines, chars, font_pt, line_spacing,
                             page_w, page_h, margin_h, margin_v)
    page_size = str(trim).upper() if str(trim).upper() in trim_dims else "A4"
    return {
        "trim": page_size,
        "page_settings": {
            "page_size": page_size,
            "margin_left_mm": _mm(margin_h), "margin_right_mm": _mm(margin_h),
            "margin_top_mm": margin_v, "margin_bottom_mm": margin_v,
            "page_numbering": True, "page_number_pos": "top-right",
            "hyphenation": False,
        },
        "typography": {"font_family": "Courier New", "font_pt": float(font_pt),
                       "line_spacing": float(line_spacing)},
        "capacity": {"lines": int(lines), "chars_per_line": int(chars),
                     "chars_per_page": int(lines) * int(chars)},
        "geometry": geometry,
        "fits": fits(geometry),
    }


def _self_check() -> int:
    """Run lightweight arithmetic and API checks; return the failure count."""
    checks = 0
    errors = 0

    def check(condition: bool) -> None:
        nonlocal checks, errors
        checks += 1
        if not condition:
            errors += 1

    default = norm_page()
    geom = default["geometry"]
    expected_char = 12.0 * MONO_CHAR_WIDTH_EM * 25.4 / 72.0
    expected_line = 12.0 * 2.0 * 25.4 / 72.0
    check(abs(geom["char_w_mm"] - expected_char) <= 0.05)
    check(abs(geom["line_h_mm"] - expected_line) <= 0.05)
    check(geom["chars_per_page"] == geom["lines_per_page"] * geom["chars_per_line"])
    check(default["capacity"]["chars_per_page"] == 1800)
    lines_fit = int(geom["content_h_mm"] / geom["line_h_mm"]) if geom["line_h_mm"] > 0 else 0
    check(lines_fit >= 30)
    check(default["fits"] == [])
    check(bool(norm_page(trim="A5")["fits"]))
    check(isinstance(fits(page_geometry(lines=0)), list))
    check(bool(fits(page_geometry(chars=0, font_pt=-1.0))))
    check(bool(fits(page_geometry(font_pt=-1.0))))
    required = {"page_size", "margin_left_mm", "margin_right_mm", "margin_top_mm",
                "margin_bottom_mm", "page_numbering", "page_number_pos"}
    check(required.issubset(default["page_settings"]))
    check(default["page_settings"]["hyphenation"] is False)
    print(f"normsida: {checks - errors} av {checks} kontroller gröna")
    return errors


if __name__ == "__main__":
    raise SystemExit(_self_check())
