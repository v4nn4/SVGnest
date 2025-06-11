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
    root_width = '10000'
    root_height = '5000'
    if rect is not None:
        rect.set('width', root_width)
        rect.set('height', root_height)
    else:
        ET.SubElement(
            combined,
            'rect',
            width=root_width,
            height=root_height,
            fill='none',
            stroke='black',
        )
    # ensure the svg element itself reflects the final canvas size
    combined.set('width', root_width)
    combined.set('height', root_height)
    combined.set('viewBox', f"0 0 {root_width} {root_height}")
    output_file = paths.output / 'nested.svg'
    save_svg(combined, output_file)
    return output_file
