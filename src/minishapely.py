from dataclasses import dataclass
from typing import Tuple
import math

@dataclass
class Polygon:
    bounds: Tuple[float, float, float, float]

    def union(self, other: 'Polygon') -> 'Polygon':
        minx = min(self.bounds[0], other.bounds[0])
        miny = min(self.bounds[1], other.bounds[1])
        maxx = max(self.bounds[2], other.bounds[2])
        maxy = max(self.bounds[3], other.bounds[3])
        return Polygon((minx, miny, maxx, maxy))


def box(minx: float, miny: float, maxx: float, maxy: float) -> Polygon:
    return Polygon((minx, miny, maxx, maxy))


def translate(poly: Polygon, xoff: float = 0.0, yoff: float = 0.0) -> Polygon:
    minx, miny, maxx, maxy = poly.bounds
    return Polygon((minx + xoff, miny + yoff, maxx + xoff, maxy + yoff))


def rotate(poly: Polygon, angle: float, origin: str | Tuple[float, float] = "center") -> Polygon:
    """Rotate a polygon by angle degrees around origin (approximate)."""
    minx, miny, maxx, maxy = poly.bounds
    if origin == "center":
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
    else:
        cx, cy = origin  # type: ignore[misc]
    rad = math.radians(angle)
    corners = [
        (minx, miny),
        (maxx, miny),
        (maxx, maxy),
        (minx, maxy),
    ]
    new_corners = []
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    for x, y in corners:
        dx = x - cx
        dy = y - cy
        x_new = cx + dx * cos_a - dy * sin_a
        y_new = cy + dx * sin_a + dy * cos_a
        new_corners.append((x_new, y_new))
    xs = [c[0] for c in new_corners]
    ys = [c[1] for c in new_corners]
    return Polygon((min(xs), min(ys), max(xs), max(ys)))
