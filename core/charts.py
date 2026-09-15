"""
core/charts.py — Diagram- och grafmotor för OmaScribe.

Genererar skarpa, högupplösta diagram (stapel-, linje-, cirkel-, donut- och områdesdiagram)
med QPainter utan externa tunga beroenden. Renderar direkt till QImage/QPixmap för
infogning i dokumentet och 100% felfri PDF-export.
"""

import math
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QFont, QPen, QBrush,
    QLinearGradient, QPainterPath
)

PALETTES = {
    # Förval: gråskala. Ett diagram i ett dokument ska kunna tryckas rent —
    # staplar och linjer skiljs åt av ljushet, inte av kulör.
    "mono": [
        "#1a1a1a", "#4d4d4d", "#808080", "#a6a6a6", "#c9c9c9", "#e8e8e8"
    ],
    "modern_blue": [
        "#2563eb", "#0ea5e9", "#6366f1", "#3b82f6", "#0284c7", "#818cf8"
    ],
    "emerald_teal": [
        "#059669", "#0d9488", "#10b981", "#14b8a6", "#34d399", "#2dd4bf"
    ],
    "warm_sunset": [
        "#f97316", "#ef4444", "#f59e0b", "#fb923c", "#f87171", "#fbbf24"
    ],
    "royal_purple": [
        "#7c3aed", "#9333ea", "#c026d3", "#8b5cf6", "#a855f7", "#d946ef"
    ],
}

def get_palette_colors(palette_name: str, count: int) -> list[QColor]:
    hex_list = PALETTES.get(palette_name, PALETTES["mono"])
    colors = []
    for i in range(count):
        hex_val = hex_list[i % len(hex_list)]
        colors.append(QColor(hex_val))
    return colors


class ChartRenderer:
    """Renderar olika typer av diagram till en högupplöst QImage."""

    @staticmethod
    def render(
        chart_type: str,
        title: str,
        categories: list[str],
        series_data: list[dict],  # [{"name": "...", "values": [1, 2, ...], "color": "#..."}]
        subtitle: str = "",
        palette: str = "mono",
        width: int = 720,
        height: int = 420,
        show_values: bool = True,
        show_grid: bool = True,
        show_legend: bool = True,
        bg_color: str = "#ffffff",
        text_color: str = "#000000"
    ) -> QImage:
        # Skapa en 2x supersamplad bild för perfekt skärpa på Retina/HiDPI och vid PDF-utskrift
        scale = 2
        img = QImage(width * scale, height * scale, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(bg_color))

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.scale(scale, scale)

        try:
            # 1. Header (Titel och Undertitel)
            y_offset = 24
            if title:
                painter.setPen(QColor(text_color))
                font_title = QFont("sans-serif", 13, QFont.Weight.Bold)
                painter.setFont(font_title)
                title_rect = QRectF(24, y_offset, width - 48, 26)
                painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
                y_offset += 28

            if subtitle:
                sub_color = QColor(text_color)
                sub_color.setAlpha(170)
                painter.setPen(sub_color)
                font_sub = QFont("sans-serif", 10, QFont.Weight.Normal)
                painter.setFont(font_sub)
                sub_rect = QRectF(24, y_offset, width - 48, 20)
                painter.drawText(sub_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, subtitle)
                y_offset += 24

            # 2. Legend / Förklaring
            legend_height = 0
            if show_legend and series_data:
                legend_height = 30

            # 3. Beräkna plot-yta
            plot_left = 60
            plot_right = width - 30
            plot_top = y_offset + 10
            plot_bottom = height - 45 - legend_height
            plot_width = max(10, plot_right - plot_left)
            plot_height = max(10, plot_bottom - plot_top)
            plot_rect = QRectF(plot_left, plot_top, plot_width, plot_height)

            # Standardfärger från palett
            palette_colors = get_palette_colors(palette, max(len(series_data), len(categories)))

            # Validera data
            if chart_type in ("pie", "donut"):
                ChartRenderer._render_pie_or_donut(
                    painter, chart_type, categories, series_data, palette_colors,
                    plot_rect, text_color, show_values
                )
            elif chart_type == "horizontal_bar":
                ChartRenderer._render_horizontal_bar(
                    painter, categories, series_data, palette_colors,
                    plot_rect, text_color, show_values, show_grid
                )
            elif chart_type in ("line", "area"):
                ChartRenderer._render_line_or_area(
                    painter, chart_type, categories, series_data, palette_colors,
                    plot_rect, text_color, show_values, show_grid
                )
            else:  # default: "bar"
                ChartRenderer._render_bar(
                    painter, categories, series_data, palette_colors,
                    plot_rect, text_color, show_values, show_grid
                )

            # 4. Rita Legend längst ned
            if show_legend:
                ChartRenderer._render_legend(
                    painter, chart_type, categories, series_data, palette_colors,
                    QRectF(24, height - legend_height - 12, width - 48, legend_height),
                    text_color
                )

        finally:
            painter.end()

        return img

    @staticmethod
    def _render_bar(
        painter: QPainter, categories: list[str], series_data: list[dict],
        palette_colors: list[QColor], plot_rect: QRectF, text_color: str,
        show_values: bool, show_grid: bool
    ):
        num_cats = len(categories)
        num_series = len(series_data)
        if num_cats == 0 or num_series == 0:
            return

        # Hitta maxvärde för y-axeln
        max_val = 0.0
        for s in series_data:
            for v in s.get("values", []):
                try:
                    max_val = max(max_val, float(v))
                except (ValueError, TypeError):
                    pass
        if max_val <= 0:
            max_val = 100.0

        # Runda upp till snyggt tak
        y_max = ChartRenderer._nice_num(max_val, round_up=True)

        # Rita Y-axel och stödlinjer
        ChartRenderer._draw_y_axis_and_grid(painter, plot_rect, y_max, text_color, show_grid)

        # Rita staplar
        cat_width = plot_rect.width() / num_cats
        group_padding = cat_width * 0.18
        avail_width = cat_width - (2 * group_padding)
        bar_width = max(6.0, avail_width / num_series)

        font_cat = QFont("sans-serif", 9, QFont.Weight.Medium)
        font_val = QFont("sans-serif", 8, QFont.Weight.Bold)

        for cat_idx, cat in enumerate(categories):
            cat_x = plot_rect.left() + (cat_idx * cat_width)

            # Rita kategori-etikett på X-axeln
            painter.setFont(font_cat)
            painter.setPen(QColor(text_color))
            lbl_rect = QRectF(cat_x, plot_rect.bottom() + 6, cat_width, 24)
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, cat)

            for s_idx, s in enumerate(series_data):
                vals = s.get("values", [])
                val = 0.0
                if cat_idx < len(vals):
                    try:
                        val = float(vals[cat_idx])
                    except (ValueError, TypeError):
                        val = 0.0

                bar_h = (val / y_max) * plot_rect.height() if y_max > 0 else 0
                bar_x = cat_x + group_padding + (s_idx * bar_width)
                bar_y = plot_rect.bottom() - bar_h

                bar_color = QColor(s.get("color", palette_colors[s_idx % len(palette_colors)]))

                # Gradientfyllning på stapeln
                grad = QLinearGradient(bar_x, bar_y, bar_x, plot_rect.bottom())
                grad.setColorAt(0.0, bar_color)
                dark_color = bar_color.darker(115)
                grad.setColorAt(1.0, dark_color)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(grad))

                # Rita med mjukt rundade hörn upptill
                r = min(4.0, bar_width / 3.0)
                path = QPainterPath()
                bar_rect = QRectF(bar_x, bar_y, max(2.0, bar_width - 2), bar_h)
                path.addRoundedRect(bar_rect, r, r)
                painter.drawPath(path)

                # Rita värdeetikett
                if show_values and val > 0:
                    painter.setFont(font_val)
                    painter.setPen(bar_color.darker(140))
                    val_str = f"{val:g}"
                    v_rect = QRectF(bar_x - 10, bar_y - 18, bar_width + 18, 16)
                    painter.drawText(v_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, val_str)

    @staticmethod
    def _render_horizontal_bar(
        painter: QPainter, categories: list[str], series_data: list[dict],
        palette_colors: list[QColor], plot_rect: QRectF, text_color: str,
        show_values: bool, show_grid: bool
    ):
        num_cats = len(categories)
        num_series = len(series_data)
        if num_cats == 0 or num_series == 0:
            return

        max_val = 0.0
        for s in series_data:
            for v in s.get("values", []):
                try:
                    max_val = max(max_val, float(v))
                except (ValueError, TypeError):
                    pass
        if max_val <= 0:
            max_val = 100.0

        x_max = ChartRenderer._nice_num(max_val, round_up=True)

        cat_height = plot_rect.height() / num_cats
        group_padding = cat_height * 0.18
        avail_height = cat_height - (2 * group_padding)
        bar_height = max(6.0, avail_height / num_series)

        font_cat = QFont("sans-serif", 9, QFont.Weight.Medium)
        font_val = QFont("sans-serif", 8, QFont.Weight.Bold)

        for cat_idx, cat in enumerate(categories):
            cat_y = plot_rect.top() + (cat_idx * cat_height)

            # Rita kategori på Y-axeln till vänster
            painter.setFont(font_cat)
            painter.setPen(QColor(text_color))
            lbl_rect = QRectF(0, cat_y, plot_rect.left() - 8, cat_height)
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, cat)

            for s_idx, s in enumerate(series_data):
                vals = s.get("values", [])
                val = 0.0
                if cat_idx < len(vals):
                    try:
                        val = float(vals[cat_idx])
                    except (ValueError, TypeError):
                        val = 0.0

                bar_w = (val / x_max) * plot_rect.width() if x_max > 0 else 0
                bar_y = cat_y + group_padding + (s_idx * bar_height)
                bar_x = plot_rect.left()

                bar_color = QColor(s.get("color", palette_colors[s_idx % len(palette_colors)]))

                grad = QLinearGradient(bar_x, bar_y, bar_x + bar_w, bar_y)
                grad.setColorAt(0.0, bar_color)
                grad.setColorAt(1.0, bar_color.darker(115))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(grad))

                r = min(4.0, bar_height / 3.0)
                path = QPainterPath()
                bar_rect = QRectF(bar_x, bar_y, bar_w, max(2.0, bar_height - 2))
                path.addRoundedRect(bar_rect, r, r)
                painter.drawPath(path)

                if show_values and val > 0:
                    painter.setFont(font_val)
                    painter.setPen(bar_color.darker(140))
                    val_str = f"{val:g}"
                    v_rect = QRectF(bar_x + bar_w + 6, bar_y, 60, bar_height)
                    painter.drawText(v_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_str)

    @staticmethod
    def _render_line_or_area(
        painter: QPainter, chart_type: str, categories: list[str], series_data: list[dict],
        palette_colors: list[QColor], plot_rect: QRectF, text_color: str,
        show_values: bool, show_grid: bool
    ):
        num_cats = len(categories)
        if num_cats == 0 or not series_data:
            return

        max_val = 0.0
        for s in series_data:
            for v in s.get("values", []):
                try:
                    max_val = max(max_val, float(v))
                except (ValueError, TypeError):
                    pass
        if max_val <= 0:
            max_val = 100.0

        y_max = ChartRenderer._nice_num(max_val, round_up=True)
        ChartRenderer._draw_y_axis_and_grid(painter, plot_rect, y_max, text_color, show_grid)

        x_step = plot_rect.width() / max(1, num_cats - 1) if num_cats > 1 else plot_rect.width() / 2

        font_cat = QFont("sans-serif", 9, QFont.Weight.Medium)
        font_val = QFont("sans-serif", 8, QFont.Weight.Bold)

        # X-axelns kategori-etiketter
        for cat_idx, cat in enumerate(categories):
            cat_x = plot_rect.left() + (cat_idx * x_step) if num_cats > 1 else plot_rect.center().x()
            painter.setFont(font_cat)
            painter.setPen(QColor(text_color))
            lbl_rect = QRectF(cat_x - 40, plot_rect.bottom() + 6, 80, 24)
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, cat)

        # Rita serier
        for s_idx, s in enumerate(series_data):
            vals = s.get("values", [])
            points = []
            for c_idx in range(num_cats):
                val = 0.0
                if c_idx < len(vals):
                    try:
                        val = float(vals[c_idx])
                    except (ValueError, TypeError):
                        val = 0.0
                px = plot_rect.left() + (c_idx * x_step) if num_cats > 1 else plot_rect.center().x()
                py = plot_rect.bottom() - ((val / y_max) * plot_rect.height() if y_max > 0 else 0)
                points.append((QPointF(px, py), val))

            if not points:
                continue

            base_color = QColor(s.get("color", palette_colors[s_idx % len(palette_colors)]))

            # Områdesfyllning (Area)
            if chart_type == "area":
                area_path = QPainterPath()
                area_path.moveTo(points[0][0].x(), plot_rect.bottom())
                for pt, _ in points:
                    area_path.lineTo(pt)
                area_path.lineTo(points[-1][0].x(), plot_rect.bottom())
                area_path.closeSubpath()

                grad = QLinearGradient(0, plot_rect.top(), 0, plot_rect.bottom())
                area_c1 = QColor(base_color)
                area_c1.setAlpha(120)
                area_c2 = QColor(base_color)
                area_c2.setAlpha(15)
                grad.setColorAt(0.0, area_c1)
                grad.setColorAt(1.0, area_c2)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(grad))
                painter.drawPath(area_path)

            # Rita linje
            pen = QPen(base_color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            line_path = QPainterPath()
            line_path.moveTo(points[0][0])
            for pt, _ in points[1:]:
                line_path.lineTo(pt)
            painter.drawPath(line_path)

            # Rita punkter & värden
            for pt, val in points:
                # Yttre ring
                painter.setPen(QPen(base_color, 2.0))
                painter.setBrush(QBrush(QColor("#ffffff")))
                painter.drawEllipse(pt, 4.5, 4.5)

                if show_values and val > 0:
                    painter.setFont(font_val)
                    painter.setPen(base_color.darker(140))
                    val_str = f"{val:g}"
                    v_rect = QRectF(pt.x() - 30, pt.y() - 20, 60, 16)
                    painter.drawText(v_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, val_str)

    @staticmethod
    def _render_pie_or_donut(
        painter: QPainter, chart_type: str, categories: list[str], series_data: list[dict],
        palette_colors: list[QColor], plot_rect: QRectF, text_color: str,
        show_values: bool
    ):
        # För cirkeldiagram tar vi första serien som värden
        values = []
        if series_data:
            raw_vals = series_data[0].get("values", [])
            for v in raw_vals:
                try:
                    values.append(max(0.0, float(v)))
                except (ValueError, TypeError):
                    values.append(0.0)

        total = sum(values)
        if total <= 0:
            return

        center = plot_rect.center()
        radius = min(plot_rect.width(), plot_rect.height()) / 2.0 * 0.88
        pie_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        start_angle = 90 * 16  # Börja kl 12
        font_slice = QFont("sans-serif", 9, QFont.Weight.Bold)

        for idx, (cat, val) in enumerate(zip(categories, values)):
            if val <= 0:
                continue
            span_angle = int((val / total) * 360 * 16)
            slice_color = palette_colors[idx % len(palette_colors)]

            painter.setPen(QPen(QColor("#ffffff"), 2.0))
            painter.setBrush(QBrush(slice_color))
            painter.drawPie(pie_rect, start_angle, span_angle)

            # Rita procent-etikett i tårtbiten
            if show_values:
                mid_angle_deg = (start_angle + (span_angle / 2)) / 16.0
                rad = math.radians(mid_angle_deg)
                label_dist = radius * (0.65 if chart_type == "pie" else 0.75)
                lx = center.x() + (label_dist * math.cos(rad))
                ly = center.y() - (label_dist * math.sin(rad))

                pct = (val / total) * 100.0
                if pct >= 4.0:  # Rita bara om tårtbiten är tillräckligt stor
                    painter.setFont(font_slice)
                    painter.setPen(QColor("#ffffff"))
                    lbl_rect = QRectF(lx - 25, ly - 10, 50, 20)
                    painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, f"{pct:.0f}%")

            start_angle += span_angle

        # Rita donut-hål om donut
        if chart_type == "donut":
            inner_radius = radius * 0.52
            inner_rect = QRectF(center.x() - inner_radius, center.y() - inner_radius, inner_radius * 2, inner_radius * 2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(inner_rect)

            # Mitten-text
            painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
            painter.setPen(QColor(text_color))
            painter.drawText(inner_rect, Qt.AlignmentFlag.AlignCenter, f"Totalt\n{total:g}")

    @staticmethod
    def _draw_y_axis_and_grid(painter: QPainter, plot_rect: QRectF, y_max: float, text_color: str, show_grid: bool):
        num_ticks = 4
        font_axis = QFont("sans-serif", 8, QFont.Weight.Normal)
        painter.setFont(font_axis)

        for i in range(num_ticks + 1):
            pct = i / num_ticks
            val = pct * y_max
            y = plot_rect.bottom() - (pct * plot_rect.height())

            # Stödlinje
            if show_grid and i > 0:
                grid_pen = QPen(QColor("#d9d9d9"), 1.0, Qt.PenStyle.DashLine)
                painter.setPen(grid_pen)
                painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

            # Y-axel etikett
            axis_pen = QPen(QColor("#666666"))
            painter.setPen(axis_pen)
            lbl_rect = QRectF(0, y - 8, plot_rect.left() - 8, 16)
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{val:g}")

        # Rita baslinjen på X-axeln
        base_pen = QPen(QColor("#999999"), 1.5, Qt.PenStyle.SolidLine)
        painter.setPen(base_pen)
        painter.drawLine(QPointF(plot_rect.left(), plot_rect.bottom()), QPointF(plot_rect.right(), plot_rect.bottom()))

    @staticmethod
    def _render_legend(
        painter: QPainter, chart_type: str, categories: list[str], series_data: list[dict],
        palette_colors: list[QColor], legend_rect: QRectF, text_color: str
    ):
        items = []
        if chart_type in ("pie", "donut"):
            for idx, cat in enumerate(categories):
                color = palette_colors[idx % len(palette_colors)]
                items.append((cat, color))
        else:
            for idx, s in enumerate(series_data):
                color = QColor(s.get("color", palette_colors[idx % len(palette_colors)]))
                items.append((s.get("name", f"Serie {idx + 1}"), color))

        if not items:
            return

        font_legend = QFont("sans-serif", 9, QFont.Weight.Medium)
        painter.setFont(font_legend)

        # Beräkna bredd för centrerad layout
        total_w = sum(len(name) * 7.5 + 28 for name, _ in items)
        start_x = max(legend_rect.left(), legend_rect.center().x() - (total_w / 2.0))
        curr_x = start_x
        y = legend_rect.top() + 6

        for name, color in items:
            # Färgplatta
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(QRectF(curr_x, y + 2, 12, 12), 3, 3)

            # Text
            painter.setPen(QColor(text_color))
            w = len(name) * 7.5 + 8
            painter.drawText(QRectF(curr_x + 16, y, w, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
            curr_x += w + 24

    @staticmethod
    def _nice_num(val: float, round_up: bool = False) -> float:
        if val <= 0:
            return 10.0
        exp = math.floor(math.log10(val))
        frac = val / (10 ** exp)
        if round_up:
            if frac <= 1.0:
                nice_frac = 1.0
            elif frac <= 2.0:
                nice_frac = 2.0
            elif frac <= 5.0:
                nice_frac = 5.0
            else:
                nice_frac = 10.0
        else:
            nice_frac = math.ceil(frac)
        return nice_frac * (10 ** exp)
