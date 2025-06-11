from .paths import Paths
from .nest import nest

class Cli:
    def __init__(self) -> None:
        self.paths = Paths()

    def nest(self) -> str:
        output_file = nest(self.paths)
        return f'Created {output_file}'

    def clean(self) -> str:
        for p in [self.paths.generated, self.paths.output]:
            if p.exists():
                for child in p.iterdir():
                    if child.is_file():
                        child.unlink()
        return 'Cleaned.'

    def show_paths(self) -> str:
        return f'raw={self.paths.raw}\ngenerated={self.paths.generated}\noutput={self.paths.output}'
