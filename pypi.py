import os

import click
import requests
from tqdm import tqdm

PACKAGES = [
    'pymobiledevice3', 'aiofiles', 'arrow', 'asn1', 'bpylist2', 'click', 'coloredlogs', 'construct',
    'cryptography', 'daemonize', 'developer-disk-image', 'fastapi', 'gpxpy', 'hexdump', 'hyperframe',
    'ifaddr', 'inquirer3', 'ipsw-parser', 'IPython', 'nest-asyncio', 'opack', 'packaging',
    'parameter-decorators', 'Pillow', 'prompt-toolkit', 'psutil', 'pycrashreport', 'pygments', 'pygnuutils',
    'pyimg4', 'pykdebugparser', 'pytun-pmd3', 'pyusb', 'qh3', 'remotezip', 'requests', 'srptools',
    'sslpsk-pmd3', 'starlette', 'tqdm', 'uvicorn', 'wsproto', 'xonsh', 'zeroconf', 'cfprefsmon', 'harlogger',
    'hilda', 'netifaces-plus']

def download_file(url, directory):
    local_filename = url.split('/')[-1]
    path = os.path.join(directory, local_filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in tqdm(r.iter_content(chunk_size=8192), desc=local_filename):
                f.write(chunk)
    return local_filename


def download_latest_version_files(output: str, package_name: str) -> None:
    package_info_url = f'https://pypi.org/pypi/{package_name}/json'
    response = requests.get(package_info_url)
    if response.status_code == 200:
        package_info = response.json()
        latest_version = package_info['info']['version']
        files = package_info['releases'][latest_version]
        if files:
            os.makedirs(output, exist_ok=True)
            for file_info in files:
                file_url = file_info['url']
                download_file(file_url, output)
        else:
            print(f"No files found for the latest version ({latest_version}) of '{package_name}'.")
    else:
        print(f"Failed to fetch package info for '{package_name}'.")


@click.command()
@click.argument('output', type=click.Path(dir_okay=True, file_okay=False, exists=True))
def cli(output: str) -> None:
    for package_name in PACKAGES:
        download_latest_version_files(output, package_name)


if __name__ == "__main__":
    cli()
