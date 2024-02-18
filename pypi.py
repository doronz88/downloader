import json
import os
from pathlib import Path

import click
import requests
from tqdm import tqdm

PACKAGES = [p.strip() for p in (Path(__file__).parent / 'pypi-packages.txt').read_text().splitlines() if p.strip()]
DOWNLOADED_CACHE_FILE = Path(__file__).parent / 'pypi-cache.json'


def download_file(url: str, directory: str) -> str:
    local_filename = url.split('/')[-1]
    path = os.path.join(directory, local_filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in tqdm(r.iter_content(chunk_size=8192), desc=local_filename):
                f.write(chunk)
    return local_filename


def download_latest_version_files(output: str, package_name: str) -> None:
    cache = []
    if DOWNLOADED_CACHE_FILE.exists():
        cache = json.loads(DOWNLOADED_CACHE_FILE.read_text())
    package_info_url = f'https://pypi.org/pypi/{package_name}/json'
    response = requests.get(package_info_url)
    if response.status_code == 200:
        package_info = response.json()
        latest_version = package_info['info']['version']
        files = package_info['releases'][latest_version]
        if files:
            for file_info in files:
                file_url = file_info['url']
                local_filename = file_url.rsplit('/', 1)[1]
                if (Path(output) / local_filename).exists():
                    print(f"skipping already downloaded {local_filename}")
                download_file(file_url, output)
                cache.append(local_filename)
                DOWNLOADED_CACHE_FILE.write_text(json.dumps(cache, indent=4))
        else:
            print(f"No files found for the latest version ({latest_version}) of '{package_name}'.")
    else:
        print(f"Failed to fetch package info for '{package_name}'.")


@click.command()
@click.argument('output', type=click.Path(exists=False))
def cli(output: str) -> None:
    Path(output).mkdir(parents=True, exist_ok=True)
    for package_name in PACKAGES:
        download_latest_version_files(output, package_name)


if __name__ == "__main__":
    cli()
