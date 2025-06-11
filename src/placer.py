from pathlib import Path
from typing import Iterable, Tuple
from xml.etree import ElementTree as ET

from shapely.affinity import translate
from shapely.geometry import Polygon

from .svg import load_svg
from .geometry import polygon_from_svg


def pack_svgs(paths: Iterable[Path], spacing: float = 10.0, bin_width: float = 1000.0) -> ET.Element:
    """Pack multiple SVGs into a single SVG document."""
    placed: list[Tuple[ET.Element, float, float, Polygon]] = []
    x_cursor = 0.0
    y_cursor = 0.0
    row_height = 0.0
    for path in paths:
        svg = load_svg(path)
        poly = polygon_from_svg(path)
        width = poly.bounds[2] - poly.bounds[0]
        height = poly.bounds[3] - poly.bounds[1]
        if x_cursor + width > bin_width:
            x_cursor = 0.0
            y_cursor += row_height + spacing
            row_height = 0.0
        placed_poly = translate(poly, xoff=x_cursor, yoff=y_cursor)
        placed.append((svg, x_cursor, y_cursor, placed_poly))
        x_cursor += width + spacing
        row_height = max(row_height, height)
    root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg')
    group = ET.SubElement(root, 'g')
    union_poly: Polygon | None = None
    for svg, x, y, poly in placed:
        g = ET.SubElement(group, 'g', transform=f'translate({x},{y})')
        g.extend(list(svg))
        if union_poly is None:
            union_poly = poly
        else:
            union_poly = union_poly.union(poly)
    if union_poly is not None:
        total_width = union_poly.bounds[2] - union_poly.bounds[0]
        total_height = union_poly.bounds[3] - union_poly.bounds[1]
        ET.SubElement(root, 'rect', width=str(total_width), height=str(total_height),
                     fill='none', stroke='black')
    return root
