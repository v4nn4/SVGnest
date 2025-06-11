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


def _expand_bounds(bounds: tuple[float, float, float, float], margin: float) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = bounds
    return minx - margin, miny - margin, maxx + margin, maxy + margin


def _boxes_intersect(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def pack_svgs(
    paths: Iterable[Path],
    spacing: float = 10.0,
    bin_width: float = 1000.0,
    margin: float = 0.0,
    rotations: Iterable[float] | None = None,
) -> ET.Element:
    """Pack multiple SVGs into a single SVG document."""
    placed: list[Tuple[ET.Element, float, float, float, Polygon]] = []
    if rotations is None:
        rotations = [0.0 for _ in paths]
    paths_iter = list(paths)
    rotations_list = list(rotations)
    for path, angle in zip(paths_iter, rotations_list):
        svg = load_svg(path)
        poly = polygon_from_svg(path)
        poly = rotate(poly, angle)
        offx, offy, maxx_r, maxy_r = poly.bounds
        poly = translate(poly, xoff=-offx, yoff=-offy)
        width = maxx_r - offx
        height = maxy_r - offy

        y = 0.0
        placed_poly = None
        while placed_poly is None:
            for x in range(0, int(bin_width - width) + 1):
                candidate = translate(poly, xoff=float(x), yoff=y)
                candidate_bb = _expand_bounds(candidate.bounds, spacing / 2)
                collide = False
                for _, _, _, _, other_poly in placed:
                    other_bb = _expand_bounds(other_poly.bounds, spacing / 2)
                    if _boxes_intersect(candidate_bb, other_bb):
                        if spacing > 0 or candidate.intersects(other_poly):
                            collide = True
                            break
                if not collide:
                    placed_poly = candidate
                    px = float(x)
                    py = y
                    break
            if placed_poly is None:
                y += 1.0

        placed.append((svg, px - offx, py - offy, angle, placed_poly))
    root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg')
    group_attrib: dict[str, str] = {}
    if margin:
        group_attrib['transform'] = f'translate({margin},{margin})'
    group = ET.SubElement(root, 'g', **group_attrib)
    # Track overall bounds without repeatedly unioning polygons which can be
    # quite expensive.  The bounding box of the union is simply the min/max of
    # all individual boxes, so accumulate those values directly for better
    # performance.
    union_minx: float | None = None
    union_miny: float | None = None
    union_maxx: float | None = None
    union_maxy: float | None = None
    for svg, x, y, angle, poly in placed:
        g = ET.SubElement(group, 'g', transform=f'rotate({angle}) translate({x},{y})')
        g.extend(list(svg))
        minx, miny, maxx, maxy = poly.bounds
        if union_minx is None:
            union_minx, union_miny, union_maxx, union_maxy = minx, miny, maxx, maxy
        else:
            union_minx = min(union_minx, minx)
            union_miny = min(union_miny, miny)
            union_maxx = max(union_maxx, maxx)
            union_maxy = max(union_maxy, maxy)

    if union_minx is not None:
        total_width = union_maxx - union_minx
        total_height = union_maxy - union_miny
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

