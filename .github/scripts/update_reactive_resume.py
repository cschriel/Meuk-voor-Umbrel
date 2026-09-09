"""Update the Umbrel package from a stable upstream release; no extra dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'koningkoffie-reactive-resume'
REPO = 'amruthpillai/reactive-resume'


def fetch(url, headers=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'koningkoffie-updater', **(headers or {})})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.headers


def version(value):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Expected a stable semantic version')
    return tuple(map(int, value.removeprefix('v').split('.')))


def replace_once(pattern, replacement, text):
    result, count = re.subn(pattern, lambda _: replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f'Expected exactly one match for {pattern}; found {count}')
    return result


def update(manifest, compose, tag, digest):
    number = tag.removeprefix('v')
    version(tag)
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Invalid image digest')
    manifest = replace_once(r'^version: .*$', f'version: "{number}"', manifest)
    notes = f'Updated to Reactive Resume {number}. Release details: https://github.com/{REPO}/releases/tag/{tag}'
    manifest = replace_once(r'^releaseNotes: "[^"\n]*"$', 'releaseNotes: ' + json.dumps(notes), manifest)
    compose = replace_once(r'^    image: amruthpillai/reactive-resume:[^\s]+$', f'    image: {REPO}:{tag}@{digest}', compose)
    return manifest, compose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    headers = {'Accept': 'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    release = json.loads(fetch(f'https://api.github.com/repos/{REPO}/releases/latest', headers)[0])
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Refusing a draft or prerelease')
    tag = release['tag_name']
    target = version(tag)
    manifest_path = APP / 'umbrel-app.yml'
    compose_path = APP / 'docker-compose.yml'
    manifest, compose = manifest_path.read_text(), compose_path.read_text()
    current = re.search(r'^version: "([^"]+)"$', manifest, re.MULTILINE).group(1)
    if target <= version(current):
        print(f'Already current: {current}. No changes.')
        return
    token = json.loads(fetch(f'https://auth.docker.io/token?service=registry.docker.io&scope=repository:{REPO}:pull')[0])['token']
    raw, response_headers = fetch(f'https://registry-1.docker.io/v2/{REPO}/manifests/{tag}', {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json',
    })
    digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
    if response_headers.get('Docker-Content-Digest') != digest:
        raise ValueError('Registry digest does not match downloaded manifest')
    platforms = {(m.get('platform', {}).get('os'), m.get('platform', {}).get('architecture')) for m in json.loads(raw).get('manifests', [])}
    if not {('linux', 'amd64'), ('linux', 'arm64')} <= platforms:
        raise ValueError('Image must support linux/amd64 and linux/arm64')
    new_manifest, new_compose = update(manifest, compose, tag, digest)
    print(f'Update {current} -> {tag}: {digest}')
    if not args.dry_run:
        manifest_path.write_text(new_manifest)
        compose_path.write_text(new_compose)


if __name__ == '__main__':
    main()
