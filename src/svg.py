from pathlib import Path
import xml.etree.ElementTree as ET
from .matrix import Matrix


def load_svg(path: Path) -> ET.Element:
    tree = ET.parse(path)
    return tree.getroot()


def save_svg(element: ET.Element, path: Path) -> None:
    path.write_text(ET.tostring(element, encoding='unicode'))


def combine_svgs(paths: list[Path], spacing: float = 10.0) -> ET.Element:
    offset = 0.0
    root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg')
    group = ET.SubElement(root, 'g')
    for p in paths:
        svg = load_svg(p)
        m = Matrix().translate(offset, 0)
        g = ET.SubElement(group, 'g', transform=str(m))
        g.extend(list(svg))
        offset += spacing + 100
    ET.SubElement(root, 'rect', width=str(offset), height='100', fill='none', stroke='black')
    return root
