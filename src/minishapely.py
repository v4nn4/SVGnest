from dataclasses import dataclass
from typing import Tuple

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
