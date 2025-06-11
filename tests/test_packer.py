import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.geometry import polygon_from_svg
from src.placer import pack_svgs, translate


def _create_svg(path: Path, size: int) -> None:
    svg = ET.Element('svg', viewBox=f"0 0 {size} {size}")
    ET.SubElement(svg, 'rect', width=str(size), height=str(size))
    path.write_text(ET.tostring(svg, encoding='unicode'))


def _create_font_svg(path: Path) -> None:
    svg = ET.Element('svg')
    defs = ET.SubElement(svg, 'defs')
    font = ET.SubElement(defs, 'font', **{'horiz-adv-x': '100'})
    ET.SubElement(font, 'font-face', ascent='80', descent='-20')
    path.write_text(ET.tostring(svg, encoding='unicode'))


def test_polygon_from_svg(tmp_path: Path):
    f = tmp_path / 'a.svg'
    _create_svg(f, 10)
    poly = polygon_from_svg(f)
    assert poly.bounds == (0.0, 0.0, 10.0, 10.0)


def test_pack_svgs(tmp_path: Path):
    f1 = tmp_path / 'a.svg'
    f2 = tmp_path / 'b.svg'
    _create_svg(f1, 10)
    _create_svg(f2, 20)
    result = pack_svgs([f1, f2], spacing=5.0, bin_width=50.0)
    # ensure resulting SVG has two groups with transforms
    groups = [g for g in result.findall('.//g') if 'transform' in g.attrib]
    assert len(groups) == 2


def test_pack_svgs_rectangle_bounds(tmp_path: Path):
    f1 = tmp_path / 'a.svg'
    f2 = tmp_path / 'b.svg'
    _create_svg(f1, 10)
    _create_svg(f2, 20)
    margin = 3.0
    result = pack_svgs([f1, f2], spacing=5.0, bin_width=50.0, margin=margin)
    rect = result.find('rect')
    assert rect is not None
    rect_width = float(rect.get('width'))
    rect_height = float(rect.get('height'))

    polys = []
    x_cursor = 0.0
    y_cursor = 0.0
    row_height = 0.0
    for path in [f1, f2]:
        poly = polygon_from_svg(path)
        width = poly.bounds[2] - poly.bounds[0]
        height = poly.bounds[3] - poly.bounds[1]
        if x_cursor + width > 50.0:
            x_cursor = 0.0
            y_cursor += row_height + 5.0
            row_height = 0.0
        poly = translate(poly, xoff=x_cursor, yoff=y_cursor)
        polys.append(poly)
        x_cursor += width + 5.0
        row_height = max(row_height, height)
    union_poly = polys[0]
    for p in polys[1:]:
        union_poly = union_poly.union(p)
    expected_width = (union_poly.bounds[2] - union_poly.bounds[0]) + margin * 2
    expected_height = (union_poly.bounds[3] - union_poly.bounds[1]) + margin * 2

    assert abs(rect_width - expected_width) < 1e-6
    assert abs(rect_height - expected_height) < 1e-6


def test_font_svg_bounds(tmp_path: Path):
    f = tmp_path / 'font.svg'
    _create_font_svg(f)
    poly = polygon_from_svg(f)
    assert poly.bounds == (0.0, -20.0, 100.0, 80.0)
