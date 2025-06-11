from pathlib import Path
from .paths import Paths
from .svg import save_svg
from .placer import pack_svgs_ga
from xml.etree import ElementTree as ET


def nest(paths: Paths) -> Path:
    paths.ensure()
    svg_files = sorted(paths.raw.glob('*.svg'))
    # pack 25 copies of each SVG present in the raw folder
    svg_files = [p for p in svg_files for _ in range(25)]
    combined = pack_svgs_ga(svg_files, bin_width=1000.0)
    # `pack_svgs_ga` already sets the appropriate bounding rectangle and
    # dimensions on the returned SVG element.  Simply propagate those values
    # to ensure the canvas fits all nested shapes.
    rect = combined.find("rect")
    if rect is not None:
        width = rect.get("width")
        height = rect.get("height")
        if width is not None and height is not None:
            combined.set("width", width)
            combined.set("height", height)
            combined.set("viewBox", f"0 0 {width} {height}")
    output_file = paths.output / 'nested.svg'
    save_svg(combined, output_file)
    return output_file
