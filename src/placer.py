from pathlib import Path
from typing import Iterable, Tuple
from xml.etree import ElementTree as ET
import random

try:
    from shapely.affinity import translate
    from shapely.geometry import Polygon
except Exception:  # pragma: no cover - fallback when Shapely is missing
    from .minishapely import translate, Polygon

from .svg import load_svg
from .geometry import polygon_from_svg


def pack_svgs(
    paths: Iterable[Path],
    spacing: float = 10.0,
    bin_width: float = 1000.0,
    margin: float = 0.0,
) -> ET.Element:
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
    group_attrib: dict[str, str] = {}
    if margin:
        group_attrib['transform'] = f'translate({margin},{margin})'
    group = ET.SubElement(root, 'g', **group_attrib)
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
        rect_width = total_width + margin * 2
        rect_height = total_height + margin * 2
        # Set overall SVG dimensions so the packed shapes fit within the canvas
        root.set('width', str(rect_width))
        root.set('height', str(rect_height))
        root.set('viewBox', f"0 0 {rect_width} {rect_height}")
        ET.SubElement(
            root,
            'rect',
            width=str(rect_width),
            height=str(rect_height),
            fill='none',
            stroke='black',
        )
    return root

def pack_svgs_ga(
    paths: Iterable[Path],
    spacing: float = 10.0,
    bin_width: float = 1000.0,
    margin: float = 0.0,
    population_size: int = 10,
    generations: int = 20,
    mutation_rate: float = 0.1,
) -> ET.Element:
    """Pack SVGs using a simple genetic algorithm optimization."""
    paths = list(paths)
    num = len(paths)

    def evaluate(order: list[int]) -> Tuple[float, ET.Element]:
        ordered_paths = [paths[i] for i in order]
        svg = pack_svgs(ordered_paths, spacing=spacing, bin_width=bin_width, margin=margin)
        rect = svg.find("rect")
        if rect is not None:
            width = float(rect.get("width"))
            height = float(rect.get("height"))
        else:
            width = float(svg.get("width") or 0)
            height = float(svg.get("height") or 0)
        return width * height, svg

    # initial population
    population: list[list[int]] = [list(range(num))]
    while len(population) < population_size:
        perm = list(range(num))
        random.shuffle(perm)
        population.append(perm)

    best_svg: ET.Element | None = None
    best_fit = float("inf")

    for _ in range(generations):
        scored: list[Tuple[float, list[int], ET.Element]] = []
        for indiv in population:
            fit, svg = evaluate(indiv)
            scored.append((fit, indiv, svg))
            if fit < best_fit:
                best_fit = fit
                best_svg = svg
        scored.sort(key=lambda x: x[0])
        new_pop: list[list[int]] = [scored[0][1]]
        while len(new_pop) < population_size:
            m = random.choice(scored)[1]
            f = random.choice(scored)[1]
            cut = random.randint(1, num - 1)
            child = m[:cut] + [x for x in f if x not in m[:cut]]
            # mutation by swapping elements
            for i in range(num):
                if random.random() < mutation_rate:
                    j = random.randint(0, num - 1)
                    child[i], child[j] = child[j], child[i]
            new_pop.append(child)
        population = new_pop

    return best_svg if best_svg is not None else pack_svgs(paths, spacing=spacing, bin_width=bin_width, margin=margin)

