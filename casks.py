import json
from pathlib import Path
from typing import Mapping

import click
import requests
from plumbum import FG, local

PACKAGES = ['mattermost', 'pycharm-ce', 'emacs', 'sublime-text', 'rectangle', 'proxyman', 'flycut', 'wireshark',
            'google-chrome', 'firefox', 'drawio', 'audacity', 'microsoft-remote-desktop', 'vlc', 'cheatsheet',
            'vmware-fusion', 'db-browser-for-sqlite', 'iterm2', 'docker', 'ghidra', 'charles', 'pycharm',
            'webstorm', 'typora', 'clion', 'visual-studio-code', 'temurin', 'izip', 'rar', 'alt-tab', 'sourcetree',
            'scroll-reverser', 'discretescroll', 'obsidian', 'sensiblesidebuttons', 'freeplane', 'filemonitor']

ASSETS_DIR = 'assets'
DOWNLOADED_CACHE_FILE = Path(__file__).parent / 'casks-cache.json'

wget = local['wget']


def query_cask_json(name: str) -> Mapping:
    return json.loads(requests.get(f'https://formulae.brew.sh/api/cask/{name}.json').text)


def download_cask_rb(name: str) -> str:
    return requests.get(
        f'https://raw.githubusercontent.com/Homebrew/homebrew-cask/master/Casks/{name[0]}/{name}.rb').text


@click.group()
def cli():
    pass


@cli.command()
def versions():
    """ Query brew casks versions """
    for package_name in PACKAGES:
        package_json = query_cask_json(package_name)
        print(f'{package_name} {package_json["version"]}')


@cli.command()
@click.argument('output', type=click.Path())
@click.option('--prefix', default='', help='prefix downloaded packages')
@click.option('--new-url-base', default='PATCHED_BASE', help='what to replace the original URL base with')
def download(output, prefix: str, new_url_base: str):
    """ Download and patch brew casks """
    cache = {}
    if DOWNLOADED_CACHE_FILE.exists():
        cache = json.loads(DOWNLOADED_CACHE_FILE.read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for package_name in PACKAGES:
        package_json = query_cask_json(package_name)
        package_version = package_json['version']

        if package_version == cache.get(package_name):
            print(f'skipping already downloaded package: {package_name}-{package_version}')
            continue

        package_rb = download_cask_rb(package_name)
        url_packaged_based = f'{new_url_base}/{package_name}'

        package_rb = package_rb.replace('https://github.com/TermiT/Flycut/releases/download/#{version}',
                                        url_packaged_based)
        package_rb = package_rb.replace('https://github.com/jgraph/drawio-desktop/releases/download/v#{version}',
                                        url_packaged_based)
        package_rb = package_rb.replace('https://github.com/audacity/audacity/releases/download/Audacity-#{version}',
                                        url_packaged_based)
        package_rb = package_rb.replace(
            'https://www.charlesproxy.com/assets/release/#{version}', url_packaged_based)
        package_rb = package_rb.replace('https://github.com/sqlitebrowser/sqlitebrowser/releases/download/v#{version}',
                                        url_packaged_based)
        package_rb = package_rb.replace('https://desktop.docker.com/mac/main',
                                        url_packaged_based)
        package_rb = package_rb.replace(
            'https://download-installer.cdn.mozilla.net/pub/firefox/releases/#{version}/mac/#{language}',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_#{version.csv.first}_build',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://download.proxyman.io/#{version.csv.second}', url_packaged_based)
        package_rb = package_rb.replace('https://github.com/rxhanson/Rectangle/releases/download/v#{version}',
                                        url_packaged_based)
        package_rb = package_rb.replace(
            'https://get.videolan.org/vlc/#{version}/macosx', url_packaged_based)
        package_rb = package_rb.replace('https://download3.vmware.com/software/FUS-#{version.csv.first.no_dots}',
                                        url_packaged_based)
        package_rb = package_rb.replace('https://update.code.visualstudio.com',
                                        url_packaged_based)
        package_rb = package_rb.replace(
            'https://github.com/adoptium/temurin#{version.major}-binaries/releases/download/jdk-#{version.csv.first}'
            '%2B#{version.csv.second}',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://releases.mattermost.com/desktop/#{version}',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://github.com/lwouis/alt-tab-macos/releases/download/v#{version}',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://product-downloads.atlassian.com/software/sourcetree/ga',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://github.com/emreyolcu/discrete-scroll/releases/download',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://github.com/obsidianmd/obsidian-releases/releases/download/v#{version}',
            url_packaged_based)
        package_rb = package_rb.replace(
            'https://github.com/archagon/sensible-side-buttons/releases/download/#{version}',
            url_packaged_based)

        assets = set()
        assets.add(package_json['url'])
        url_base = package_json['url'].rsplit('/', 1)[0]
        for variation in package_json['variations'].values():
            url = variation.get('url')
            if url is not None:
                url_base = url.rsplit('/', 1)[0]
                assert url.startswith(
                    url_base), 'not all assets start with same base'
                assets.add(url)

        package_rb = package_rb.replace(f'cask "{package_name}" do', f'cask "{prefix}{package_name}" do')
        package_rb = package_rb.replace(url_base, url_packaged_based)
        (output / f'{prefix}{package_name}.rb').write_text(package_rb)

        assets_dir = output / ASSETS_DIR / package_name

        for url in assets:
            url_components = url.split('/')

            # handle specific package directories where filename doesn't encode the arch and version
            directory_prefix = assets_dir
            if package_name == 'docker':
                directory_prefix = assets_dir / \
                    url_components[-3] / url_components[-2]
            elif package_name == 'visual-studio-code':
                directory_prefix = assets_dir / \
                    url_components[-3] / url_components[-2]
            wget[url, '--directory-prefix', directory_prefix, '--no-clobber'] & FG

        cache[package_name] = package_version
        DOWNLOADED_CACHE_FILE.write_text(json.dumps(cache, indent=4))


if __name__ == '__main__':
    cli()
