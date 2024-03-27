from pathlib import Path

import click
from plumbum import local, FG

python3 = local['python3']


@click.command()
@click.argument('prefix')
@click.argument('path', type=click.Path(dir_okay=True, file_okay=False, exists=True))
def cli(prefix: str, path: str) -> None:
    path = Path(path)
    local['python3']['pypi.py', path / 'pypi'] & FG
    local['python3']['formulas.py', path / 'formulas', '--prefix', prefix] & FG
    local['python3']['casks.py', 'download', path / 'casks', '--prefix', prefix] & FG


if __name__ == '__main__':
    cli()
