from pathlib import Path
from xml.etree import ElementTree as ET
try:
    from shapely.geometry import box, Polygon
except Exception:  # pragma: no cover - fallback when Shapely is missing
    from .minishapely import box, Polygon


def polygon_from_svg(path: Path) -> Polygon:
    """Return a simple bounding box polygon for the SVG viewBox."""
    root = ET.parse(path).getroot()
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

    # fallback for SVG fonts that provide <font> and <font-face> information
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
