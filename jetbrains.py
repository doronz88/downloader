import xml.etree.ElementTree as ET
from pathlib import Path

import click
import requests
from plumbum import local, FG

PLUGINS = [
    # https://plugins.jetbrains.com/plugin/20710-rainbow-brackets-lite--free-and-opensource
    'izhangzhihao.rainbow.brackets.lite',

    # https://plugins.jetbrains.com/plugin/10044-atom-material-icons
    'com.mallowigi',

    # https://plugins.jetbrains.com/plugin/15635-diagrams-net-integration
    'de.docs_as_co.intellij.plugin.diagramsnet',

    # https://plugins.jetbrains.com/plugin/12255-visual-studio-code-dark-plus-theme
    'com.samdark.intellij-visual-studio-code-dark-plus',

    # https://plugins.jetbrains.com/plugin/11938-one-dark-theme
    'com.markskelton.one-dark-theme',

    # https://plugins.jetbrains.com/plugin/8006-material-theme-ui
    'com.chrisrm.idea.MaterialThemeUI',

    # https://plugins.jetbrains.com/plugin/7724-docker
    'Docker',

    # https://plugins.jetbrains.com/plugin/13122-shell-script
    'com.jetbrains.sh',

    # https://plugins.jetbrains.com/plugin/9333-makefile-language
    'name.kropp.intellij.makefile',
]
BUILD = '233.11799.298'
DOWNLOAD_URL = 'https://plugins.jetbrains.com/pluginManager?action=download&id={plugin_xml_id}&build={build}'
DETAILS_URL = 'https://plugins.jetbrains.com/plugins/list?pluginId={plugin_xml_id}'

wget = local['wget']
file = local['file']
mv = local['mv']
rm = local['rm']


def get_plugin_latest_version(plugin_xml_id: str) -> str:
    root = ET.fromstring(requests.get(DETAILS_URL.format(plugin_xml_id=plugin_xml_id)).text)
    for node in root.iter('version'):
        return node.text
    raise Exception('failed to get latest version')


def download(plugin_xml_id: str, output: Path, build: str = BUILD) -> None:
    wget[DOWNLOAD_URL.format(plugin_xml_id=plugin_xml_id, build=build), '-O', output, '--no-clobber'] & FG


@click.command()
@click.argument('output', type=click.Path(file_okay=False))
def cli(output: str):
    output = Path(output)
    rm('-rf', output)
    output.mkdir(exist_ok=True, parents=True)
    for plugin in PLUGINS:
        latest_version = get_plugin_latest_version(plugin)
        output_file_prefix = output / f'{plugin}_{latest_version}'
        output_file_zip = output_file_prefix.with_suffix('.zip')
        output_file_jar = output_file_prefix.with_suffix('.jar')
        if output_file_zip.exists() or output_file_jar.exists():
            continue
        download(plugin, output_file_prefix)
        if 'JAR' in file(output_file_prefix):
            mv(output_file_prefix, output_file_jar)
        else:
            mv(output_file_prefix, output_file_zip)


if __name__ == '__main__':
    cli()