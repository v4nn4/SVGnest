import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from src.geometry import polygon_from_svg
from src.placer import pack_svgs


def _create_svg(path: Path, size: int) -> None:
    svg = ET.Element('svg', viewBox=f"0 0 {size} {size}")
    ET.SubElement(svg, 'rect', width=str(size), height=str(size))
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
