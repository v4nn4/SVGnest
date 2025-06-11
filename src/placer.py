from pathlib import Path
from typing import Iterable, Tuple
from xml.etree import ElementTree as ET
import random

# Genetic algorithm helper functions inspired by the original JavaScript
# implementation found in old/svgnest.js

try:
    from shapely.affinity import translate, rotate
    from shapely.geometry import Polygon
except Exception:  # pragma: no cover - fallback when Shapely is missing
    from .minishapely import translate, rotate, Polygon

from .svg import load_svg
from .geometry import polygon_from_svg


def pack_svgs(
    paths: Iterable[Path],
    spacing: float = 10.0,
    bin_width: float = 1000.0,
    margin: float = 0.0,
    rotations: Iterable[float] | None = None,
) -> ET.Element:
    """Pack multiple SVGs into a single SVG document."""
    placed: list[Tuple[ET.Element, float, float, float, Polygon]] = []
    x_cursor = 0.0
    y_cursor = 0.0
    row_height = 0.0
    if rotations is None:
        rotations = [0.0 for _ in paths]
    paths_iter = list(paths)
    rotations_list = list(rotations)
    for path, angle in zip(paths_iter, rotations_list):
        svg = load_svg(path)
        poly = polygon_from_svg(path)
        minx, miny, maxx, maxy = poly.bounds
        poly = rotate(poly, angle, origin="center")
        offx, offy, maxx_r, maxy_r = poly.bounds
        poly = translate(poly, xoff=-offx, yoff=-offy)
        width = maxx_r - offx
        height = maxy_r - offy
        if x_cursor + width > bin_width:
            x_cursor = 0.0
            y_cursor += row_height + spacing
            row_height = 0.0
        placed_poly = translate(poly, xoff=x_cursor, yoff=y_cursor)
        placed.append((svg, x_cursor - offx, y_cursor - offy, angle, placed_poly))
        x_cursor += width + spacing
        row_height = max(row_height, height)
    root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg')
    group_attrib: dict[str, str] = {}
    if margin:
        group_attrib['transform'] = f'translate({margin},{margin})'
    group = ET.SubElement(root, 'g', **group_attrib)
    union_poly: Polygon | None = None
    for svg, x, y, angle, poly in placed:
        g = ET.SubElement(group, 'g', transform=f'translate({x},{y}) rotate({angle})')
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
    rotation_steps: int = 4,
) -> ET.Element:
    """Pack SVGs using a simple genetic algorithm optimization."""
    paths = list(paths)
    num = len(paths)
    angle_choices = [i * (360 / rotation_steps) for i in range(max(rotation_steps, 1))]

    def random_weighted_individual(scored: list[Tuple[float, tuple[list[int], list[float]], ET.Element]], exclude: tuple[list[int], list[float]] | None = None) -> tuple[list[int], list[float]]:
        """Select an individual weighted towards the start of the list."""
        pop = [s[1] for s in scored]
        if exclude is not None and exclude in pop:
            pop.remove(exclude)
        rand = random.random()
        lower = 0.0
        weight = 1.0 / len(pop)
        upper = weight
        for idx, indiv in enumerate(pop):
            if lower < rand <= upper:
                return indiv
            lower = upper
            upper += 2 * weight * ((len(pop) - idx) / len(pop))
        return pop[0]

    def mate(male: tuple[list[int], list[float]], female: tuple[list[int], list[float]]) -> tuple[tuple[list[int], list[float]], tuple[list[int], list[float]]]:
        placement_m, rot_m = male
        placement_f, rot_f = female
        cut = round(min(max(random.random(), 0.1), 0.9) * (len(placement_m) - 1))
        gene1 = placement_m[:cut]
        rot1 = rot_m[:cut]
        gene2 = placement_f[:cut]
        rot2 = rot_f[:cut]
        for idx, p in enumerate(placement_f):
            if p not in gene1:
                gene1.append(p)
                rot1.append(rot_f[idx])
        for idx, p in enumerate(placement_m):
            if p not in gene2:
                gene2.append(p)
                rot2.append(rot_m[idx])
        return (gene1, rot1), (gene2, rot2)

    def mutate(indiv: tuple[list[int], list[float]]) -> tuple[list[int], list[float]]:
        placement, rot = indiv
        placement = placement[:]
        rot = rot[:]
        for i in range(len(placement)):
            if random.random() < 0.01 * mutation_rate:
                j = i + 1
                if j < len(placement):
                    placement[i], placement[j] = placement[j], placement[i]
            if random.random() < 0.01 * mutation_rate:
                rot[i] = random.choice(angle_choices)
        return placement, rot

    def evaluate(indiv: tuple[list[int], list[float]]) -> Tuple[float, ET.Element]:
        order, rots = indiv
        ordered_paths = [paths[i] for i in order]
        svg = pack_svgs(ordered_paths, spacing=spacing, bin_width=bin_width, margin=margin, rotations=rots)
        rect = svg.find("rect")
        if rect is not None:
            width = float(rect.get("width"))
            height = float(rect.get("height"))
        else:
            width = float(svg.get("width") or 0)
            height = float(svg.get("height") or 0)
        return width * height, svg

    # initial population with one ordered individual and the rest random
    initial_angles = [random.choice(angle_choices) for _ in range(num)]
    population: list[tuple[list[int], list[float]]] = [(list(range(num)), initial_angles)]
    while len(population) < population_size:
        perm = list(range(num))
        random.shuffle(perm)
        angles = [random.choice(angle_choices) for _ in range(num)]
        population.append((perm, angles))

    best_svg: ET.Element | None = None
    best_fit = float("inf")

    for _ in range(generations):
        scored: list[Tuple[float, tuple[list[int], list[float]], ET.Element]] = []
        for indiv in population:
            fit, svg = evaluate(indiv)
            scored.append((fit, indiv, svg))
            if fit < best_fit:
                best_fit = fit
                best_svg = svg
        scored.sort(key=lambda x: x[0])

        new_pop: list[tuple[list[int], list[float]]] = [scored[0][1]]
        while len(new_pop) < population_size:
            male = random_weighted_individual(scored)
            female = random_weighted_individual(scored, exclude=male)
            c1, c2 = mate(male, female)
            new_pop.append(mutate(c1))
            if len(new_pop) < population_size:
                new_pop.append(mutate(c2))
        population = new_pop

    return best_svg if best_svg is not None else pack_svgs(paths, spacing=spacing, bin_width=bin_width, margin=margin)

