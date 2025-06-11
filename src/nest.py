from pathlib import Path
from .paths import Paths
from .svg import save_svg
from .placer import pack_svgs
from xml.etree import ElementTree as ET


def nest(paths: Paths) -> Path:
    paths.ensure()
    svg_files = sorted(paths.raw.glob('*.svg'))
    # pack 4 copies of each SVG present in the raw folder
    svg_files = [p for p in svg_files for _ in range(4)]
    combined = pack_svgs(svg_files, bin_width=10000.0)
    rect = combined.find('rect')
    if rect is not None:
        rect.set('width', '10000')
        rect.set('height', '5000')
    else:
        ET.SubElement(
            combined,
            'rect',
            width='10000',
            height='5000',
            fill='none',
            stroke='black',
        )
    output_file = paths.output / 'nested.svg'
    save_svg(combined, output_file)
    return output_file
