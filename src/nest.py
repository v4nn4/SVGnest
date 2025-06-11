from pathlib import Path
from .paths import Paths
from .svg import combine_svgs, save_svg


def nest(paths: Paths) -> Path:
    paths.ensure()
    svg_files = sorted(paths.raw.glob('*.svg'))
    combined = combine_svgs(svg_files)
    output_file = paths.output / 'nested.svg'
    save_svg(combined, output_file)
    return output_file
