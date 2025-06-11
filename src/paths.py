from dataclasses import dataclass
from pathlib import Path

@dataclass
class Paths:
    root: Path = Path(__file__).resolve().parents[1]
    raw: Path = root / 'data' / 'raw'
    generated: Path = root / 'data' / 'generated'
    output: Path = root / 'output'

    def ensure(self) -> None:
        self.raw.mkdir(parents=True, exist_ok=True)
        self.generated.mkdir(parents=True, exist_ok=True)
        self.output.mkdir(parents=True, exist_ok=True)
