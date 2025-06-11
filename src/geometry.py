from pathlib import Path
from xml.etree import ElementTree as ET
from shapely.geometry import box, Polygon


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
    raise ValueError(f"Cannot determine bounds for {path}")
