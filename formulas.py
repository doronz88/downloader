import json
from pathlib import Path
from sys import version

import click
import requests
from plumbum import FG, local

ASSETS_DIR = 'assets'
DOWNLOADED_CACHE_FILE = Path(__file__).parent / 'formulas-cache.json'

wget = local['wget']

PACKAGES = {
    'ipsw': 'https://raw.githubusercontent.com/blacktop/homebrew-tap/master/Formula/ipsw.rb',
}

@click.command()
@click.argument('output', type=click.Path())
@click.option('--prefix', default='', help='prefix downloaded packages')
@click.option('--new-url-base', default='PATCHED_BASE', help='what to replace the original URL base with')
def cli(output, prefix: str, new_url_base: str):
    """ Download and patch brew formulas """
    cache = {}
    if DOWNLOADED_CACHE_FILE.exists():
        cache = json.loads(DOWNLOADED_CACHE_FILE.read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for package_name, package_url in PACKAGES.items():
        package_rb = requests.get(package_url).text
        package_version = package_rb.split('version "', 1)[1].split('"', 1)[0]

        if package_version == cache.get(package_name):
            print(f'skipping already downloaded package: {package_name}-{package_version}')
            continue

        url_packaged_based = f'{new_url_base}/{package_name}'

        assets = set()
        for line in package_rb.splitlines():
            if 'url "' not in line:
                continue
            url = line.split('url "', 1)[1].split('"', 1)[0]
            assets.add(url)

        package_rb = package_rb.replace('https://github.com/blacktop/ipsw/releases/download', url_packaged_based)
        package_rb = package_rb.replace(f'v{package_version}/', '')
        
        class_name = package_name.capitalize()
        package_rb = package_rb.replace(f'class {class_name} < Formula', f'class {prefix.replace("-", "").capitalize()}{class_name} < Formula')
        (output / f'{prefix}{package_name}.rb').write_text(package_rb)

        assets_dir = output / ASSETS_DIR / package_name

        for url in assets:
            directory_prefix = assets_dir
            wget[url, '--directory-prefix', directory_prefix, '--no-clobber'] & FG

        cache[package_name] = package_version
        DOWNLOADED_CACHE_FILE.write_text(json.dumps(cache, indent=4))


if __name__ == '__main__':
    cli()
