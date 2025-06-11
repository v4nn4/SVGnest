from pathlib import Path
import re
from xml.etree import ElementTree as ET
try:
    from shapely.geometry import box, Polygon, Point
    from shapely.affinity import scale
    from shapely.ops import unary_union
except Exception:  # pragma: no cover - fallback when Shapely is missing
    from .minishapely import box, Polygon

    class Point:
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

        def buffer(self, r: float) -> Polygon:
            return box(self.x - r, self.y - r, self.x + r, self.y + r)

    def scale(poly: Polygon, sx: float, sy: float) -> Polygon:  # type: ignore[misc]
        minx, miny, maxx, maxy = poly.bounds
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        width = (maxx - minx) * sx / 2
        height = (maxy - miny) * sy / 2
        return box(cx - width, cy - height, cx + width, cy + height)

    def unary_union(polys: list[Polygon]) -> Polygon:  # type: ignore[misc]
        result = polys[0]
        for p in polys[1:]:
            result = result.union(p)
        return result


def _parse_points(val: str) -> list[tuple[float, float]]:
    parts = [p for p in re.split(r'[ ,]+', val.strip()) if p]
    coords = [float(p) for p in parts]
    return [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]


def polygon_from_svg(path: Path) -> Polygon:
    """Return a polygon representing the visible shapes of the SVG."""
    root = ET.parse(path).getroot()
    polys: list[Polygon] = []

    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag == 'rect':
            x = float(el.get('x', '0'))
            y = float(el.get('y', '0'))
            w = float(el.get('width', '0'))
            h = float(el.get('height', '0'))
            polys.append(box(x, y, x + w, y + h))
        elif tag in {'polygon', 'polyline'}:
            pts_attr = el.get('points')
            if pts_attr:
                pts = _parse_points(pts_attr)
                if tag == 'polygon':
                    if len(pts) >= 3:
                        polys.append(Polygon(pts))
                else:
                    if len(pts) >= 3:
                        polys.append(Polygon(pts))
        elif tag == 'circle':
            cx = float(el.get('cx', '0'))
            cy = float(el.get('cy', '0'))
            r = float(el.get('r', '0'))
            polys.append(Point(cx, cy).buffer(r))
        elif tag == 'ellipse':
            cx = float(el.get('cx', '0'))
            cy = float(el.get('cy', '0'))
            rx = float(el.get('rx', '0'))
            ry = float(el.get('ry', '0'))
            e = Point(cx, cy).buffer(1.0)
            polys.append(scale(e, rx, ry))

    if polys:
        return unary_union(polys)

    viewbox = root.get('viewBox')
    if viewbox:
        parts = [float(v) for v in viewbox.replace(',', ' ').split()]
        if len(parts) == 4:
            x, y, w, h = parts
            return box(x, y, x + w, y + h)
    width = root.get('width')
    height = root.get('height')
    if width and height:
        w = float(width)
        h = float(height)
        return box(0, 0, w, h)

    font = root.find('.//font')
    face = root.find('.//font-face')
    if font is not None and face is not None:
        try:
            w = float(font.get('horiz-adv-x', face.get('units-per-em', '0')))
            ascent = float(face.get('ascent', '0'))
            descent = float(face.get('descent', '0'))
            return box(0, descent, w, ascent)
        except (TypeError, ValueError):
            pass

    raise ValueError(f"Cannot determine bounds for {path}")
