from pathlib import Path
from .paths import Paths
from .svg import save_svg
from .placer import pack_svgs


def nest(paths: Paths) -> Path:
    paths.ensure()
    svg_files = sorted(paths.raw.glob('*.svg'))
    # pack 10 copies of each SVG present in the raw folder
    svg_files = [p for p in svg_files for _ in range(10)]
    combined = pack_svgs(svg_files)
    output_file = paths.output / 'nested.svg'
    save_svg(combined, output_file)
    return output_file
