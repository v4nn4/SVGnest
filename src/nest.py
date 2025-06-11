from pathlib import Path
from .paths import Paths
from .svg import save_svg
from .placer import pack_svgs


def nest(paths: Paths) -> Path:
    paths.ensure()
    svg_files = sorted(paths.raw.glob('*.svg'))
    combined = pack_svgs(svg_files)
    output_file = paths.output / 'nested.svg'
    save_svg(combined, output_file)
    return output_file
