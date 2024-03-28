from pathlib import Path

import click
from plumbum import local, FG

python3 = local['python3']
node = local['node']


@click.command()
@click.argument('prefix')
@click.argument('path', type=click.Path(dir_okay=True, file_okay=False, exists=True))
def cli(prefix: str, path: str) -> None:
    path = Path(path)
    python3['pypi.py', path / 'pypi'] & FG
    node['npm.js', path / 'npm'] & FG
    python3['formulas.py', path / 'formulas', '--prefix', prefix] & FG
    python3['casks.py', 'download', path / 'casks', '--prefix', prefix] & FG


if __name__ == '__main__':
    cli()
