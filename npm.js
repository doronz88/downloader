import axios from 'axios';
import PQueue from 'p-queue';
import { join } from 'path';
import { createHash } from 'crypto'
import { gt, satisfies } from 'semver';
import { SingleBar, Presets } from 'cli-progress';
import { readFileSync, existsSync, mkdirSync, writeFileSync, createWriteStream } from 'fs';

const CACHE_FILE = 'npm-cache.json';
const OUTPUT_DIR = process.argv[2] ?? 'package-tar';
const REGISTRY_URL = 'https://registry.npmjs.org';
const PROGRESS_NAME = 'Searching...';
const PACKAGES_LIST = readFileSync('npm-packages.txt', 'utf-8').split('\n');

const queue = new PQueue({ concurrency: 1200 });
const error = [];
let totalTasks = 0;
let completedTasks = 0;

if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR);
}

const cache = new Set(existsSync(CACHE_FILE) ? readFileSync(CACHE_FILE, 'utf-8').split('\n') : []);

const progressBar = new SingleBar({
    format: '{bar} {percentage}% | ETA: {eta}s | {value}/{total} | {name}',
}, Presets.shades_classic);

function calculateMD5(input) {
    const hash = createHash('md5');
    hash.update(input);
    return hash.digest('hex');
}

function extractVersionFromURL(url) {
    const regex = /(\d+\.\d+\.\d+\.tgz)/;
    const match = url.match(regex);
    return match ? match[1] : null;
}

function extractBeforeDash(inputString) {
    const regex = /^(.*?)(\/-.*)$/;
    const match = inputString.match(regex);
    return match ? match[1].replace('/', '-').replace('@', '') : null;
}

function extractFileNameFromURL(url) {
    url = url.replace(`${ REGISTRY_URL }/`, '');
    const name = extractBeforeDash(url);
    const version = extractVersionFromURL(url);
    return `${ name }-${ calculateMD5(url) }-${ version }`;
}

async function getPackageMetadata(query) {
    const result = await axios.get(`${ REGISTRY_URL }/${ query }`);
    return result.data;
}

async function downloadTarFile(tarUrl, filePath) {
    try {
        const response = await axios.get(tarUrl, { responseType: 'stream' });
        const writer = createWriteStream(filePath);
        response.data.pipe(writer);
        await new Promise((resolve, reject) => {
            writer.on('finish', resolve);
            writer.on('error', reject);
        });
    } catch (error) {
        console.error('Error downloading or saving the file:', error);
    }
}

function findHighestMatchingVersion(metadata, versionRange) {
    const matchingVersions = Object.keys(metadata.versions).filter(version => satisfies(version, versionRange));
    if (matchingVersions.length === 0) {
        return metadata['dist-tags']['latest'];
    }
    return matchingVersions.reduce((highest, current) => gt(current, highest) ? current : highest);
}

async function addDependencies(dependencies) {
    await Promise.all(Object.entries(dependencies).map(async ([ key, value ]) => {
        const packageName = value.includes('npm:') ? value.replace('npm:', '') : `${ key }@${ value }`;
        await collectPackage(packageName);
    }));
}

async function collectPackage(data) {
    let packageName, targetVersion;
    const matches = data.match(/^(.*)@(.*)$/);
    if (matches && matches[1]) {
        packageName = matches[1];
        targetVersion = matches[2];
    } else {
        packageName = data;
    }
    const metadata = await getPackageMetadata(packageName);
    const version = findHighestMatchingVersion(metadata, targetVersion || '');
    const pack = metadata.versions[version];
    if (!cache.has(pack['_id'])) {
        cache.add(pack['_id']);
        totalTasks++;
        progressBar.setTotal(totalTasks);
        progressBar.update({ name: packageName });
        await downloadTarFile(pack.dist.tarball, join(OUTPUT_DIR, extractFileNameFromURL(pack.dist.tarball)));
        await addDependencies({ ...pack.dependencies, ...pack.peerDependencies });
        completedTasks++;
        progressBar.update(completedTasks);
    }
}

async function npm() {
    progressBar.start(0, 0, { name: PROGRESS_NAME });
    await Promise.all(PACKAGES_LIST.map(async item => {
        await queue.add(() => collectPackage(item));
    }));
    await queue.onEmpty();
    progressBar.stop();
    writeFileSync('npm-cache.json', [ ...cache ].join('\n'));
    if (error.length > 0) {
        console.log('Failed to install', error.join(', '));
    }
}

npm().catch(console.error);
