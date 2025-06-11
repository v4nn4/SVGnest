import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


def _bbox(points: Sequence[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _orientation(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> int:
    val = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if val > 0:
        return 1
    if val < 0:
        return -1
    return 0


def _on_segment(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> bool:
    return (
        min(a[0], b[0]) <= c[0] <= max(a[0], b[0])
        and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])
    )


def _segments_intersect(p1, p2, q1, q2) -> bool:
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(p1, p2, q1):
        return True
    if o2 == 0 and _on_segment(p1, p2, q2):
        return True
    if o3 == 0 and _on_segment(q1, q2, p1):
        return True
    if o4 == 0 and _on_segment(q1, q2, p2):
        return True
    return False


def _point_in_polygon(pt: Tuple[float, float], poly: Sequence[Tuple[float, float]]) -> bool:
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _polygons_intersect(a: Sequence[Tuple[float, float]], b: Sequence[Tuple[float, float]]) -> bool:
    na = len(a)
    nb = len(b)
    for i in range(na):
        p1 = a[i]
        p2 = a[(i + 1) % na]
        for j in range(nb):
            q1 = b[j]
            q2 = b[(j + 1) % nb]
            if _segments_intersect(p1, p2, q1, q2):
                return True
    if _point_in_polygon(a[0], b) or _point_in_polygon(b[0], a):
        return True
    return False


@dataclass
class Polygon:
    points: List[Tuple[float, float]]

    def __init__(self, points: Iterable[Tuple[float, float]]):
        self.points = list(points)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return _bbox(self.points)

    def union(self, other: "Polygon") -> "Polygon":
        minx = min(self.bounds[0], other.bounds[0])
        miny = min(self.bounds[1], other.bounds[1])
        maxx = max(self.bounds[2], other.bounds[2])
        maxy = max(self.bounds[3], other.bounds[3])
        return Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)])

    def intersects(self, other: "Polygon") -> bool:
        return _polygons_intersect(self.points, other.points)


def box(minx: float, miny: float, maxx: float, maxy: float) -> Polygon:
    return Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)])


def translate(poly: Polygon, xoff: float = 0.0, yoff: float = 0.0) -> Polygon:
    return Polygon([(x + xoff, y + yoff) for x, y in poly.points])


def rotate(poly: Polygon, angle: float, origin: str | Tuple[float, float] = "center") -> Polygon:
    if origin == "center":
        cx = sum(p[0] for p in poly.points) / len(poly.points)
        cy = sum(p[1] for p in poly.points) / len(poly.points)
    else:
        cx, cy = origin  # type: ignore[misc]
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    new_points = []
    for x, y in poly.points:
        dx = x - cx
        dy = y - cy
        x_new = cx + dx * cos_a - dy * sin_a
        y_new = cy + dx * sin_a + dy * cos_a
        new_points.append((x_new, y_new))
    return Polygon(new_points)
