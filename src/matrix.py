from dataclasses import dataclass

@dataclass
class Matrix:
    a: float = 1
    b: float = 0
    c: float = 0
    d: float = 1
    e: float = 0
    f: float = 0

    def translate(self, x: float, y: float) -> 'Matrix':
        self.e += x
        self.f += y
        return self

    def __str__(self) -> str:
        return f'matrix({self.a},{self.b},{self.c},{self.d},{self.e},{self.f})'
