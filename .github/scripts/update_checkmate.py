"""Prepare reviewed Checkmate/Capture updates; never update MongoDB or publish directly."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'koningkoffie-checkmate'
PROJECTS = {'checkmate': 'bluewave-labs/Checkmate', 'capture': 'bluewave-labs/capture'}
ACCEPT = ', '.join(['application/vnd.oci.image.index.v1+json',
                    'application/vnd.oci.image.manifest.v1+json',
                    'application/vnd.docker.distribution.manifest.list.v2+json',
                    'application/vnd.docker.distribution.manifest.v2+json'])


def fetch(url, headers=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'koningkoffie-updater', **(headers or {})})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.headers


def version(tag):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+', tag):
        raise ValueError(f'Not a stable version: {tag}')
    return tuple(map(int, tag.removeprefix('v').split('.')))


def replace_once(pattern, replacement, content):
    result, count = re.subn(pattern, lambda _: replacement, content, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f'Expected one match for {pattern}, got {count}')
    return result


def current_tag(compose, name):
    match = re.search(rf'^    image: ghcr.io/bluewave-labs/{name}:([^@\s]+)@sha256:[a-f0-9]{{64}}$', compose, re.M)
    if not match:
        raise ValueError(f'Missing pinned {name} image')
    version(match[1])
    return match[1]


def verified_image(name, tag):
    repo = 'bluewave-labs/' + name
    token = json.loads(fetch(f'https://ghcr.io/token?service=ghcr.io&scope=repository:{repo}:pull')[0])['token']
    headers = {'Authorization': 'Bearer ' + token, 'Accept': ACCEPT}

    def manifest(ref):
        raw, returned = fetch(f'https://ghcr.io/v2/{repo}/manifests/{ref}', headers)
        digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        if returned.get('Docker-Content-Digest') != digest or (ref.startswith('sha256:') and ref != digest):
            raise ValueError('Registry digest mismatch')
        return json.loads(raw), digest

    index, digest = manifest(tag)
    for arch in ('amd64', 'arm64'):
        child = next((m for m in index.get('manifests', [])
                      if m.get('platform', {}).get('os') == 'linux'
                      and m.get('platform', {}).get('architecture') == arch), None)
        if child is None:
            raise ValueError(f'{name}:{tag} missing linux/{arch}')
        # An index can exist before its referenced platform images are available.
        manifest(child['digest'])
    return digest


def update(manifest, compose, readme, updates):
    """updates maps project names to (stable tag, verified digest)."""
    if not updates:
        return manifest, compose, readme
    package = re.search(r'^version: "(\d+\.\d+\.\d+(?:\.\d+)?)"$', manifest, re.M)
    if not package:
        raise ValueError('Unexpected Umbrel package version')
    old_checkmate = current_tag(compose, 'checkmate')
    if tuple(map(int, package[1].split('.')[:3])) != version(old_checkmate):
        raise ValueError('Package version does not match Checkmate image')
    notes = []
    for name, (tag, digest) in updates.items():
        old = current_tag(compose, name)
        if version(tag) <= version(old):
            raise ValueError('Refusing a downgrade or same-version replacement')
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', digest):
            raise ValueError('Invalid digest')
        compose = replace_once(rf'^    image: ghcr.io/bluewave-labs/{name}:.*$',
                               f'    image: ghcr.io/bluewave-labs/{name}:{tag}@{digest}', compose)
        repo = PROJECTS[name]
        notes.append(f'{name.capitalize()} {tag.removeprefix("v")}: https://github.com/{repo}/releases/tag/{tag}')
        if name == 'capture':
            manifest = manifest.replace(f'Capture {old.removeprefix("v")} is included', f'Capture {tag.removeprefix("v")} is included')
            readme = readme.replace(f'[Capture {old.removeprefix("v")}]', f'[Capture {tag.removeprefix("v")}]')
        readme = readme.replace(f'https://github.com/{repo}/releases/tag/{old}', f'https://github.com/{repo}/releases/tag/{tag}')
        if name == 'checkmate':
            readme = readme.replace(f'[{old}]', f'[{tag}]')
            # Keep the verified existing icon asset; new releases need not retain it.
    if 'checkmate' in updates:
        new_package = updates['checkmate'][0].removeprefix('v')
    else:
        parts = package[1].split('.')
        new_package = '.'.join(parts[:3] + [str(int(parts[3]) + 1 if len(parts) == 4 else 1)])
    manifest = replace_once(r'^version: .*$', f'version: "{new_package}"', manifest)
    manifest = replace_once(r'^releaseNotes: .*$', 'releaseNotes: ' + json.dumps('Updated ' + '; '.join(notes)), manifest)
    return manifest, compose, readme


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    paths = [APP / 'umbrel-app.yml', APP / 'docker-compose.yml', ROOT / 'README.md']
    contents = [p.read_text() for p in paths]
    headers = {'Accept': 'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    updates = {}
    for name, repo in PROJECTS.items():
        release = json.loads(fetch(f'https://api.github.com/repos/{repo}/releases/latest', headers)[0])
        if release.get('draft') or release.get('prerelease'):
            raise ValueError(f'Refusing non-stable {name} release')
        tag = release['tag_name']
        if version(tag) <= version(current_tag(contents[1], name)):
            print(f'{name}: already current')
            continue
        digest = verified_image(name, tag)
        updates[name] = (tag, digest)
        print(f'{name}: {tag}@{digest}')
    updated = update(*contents, updates)
    # All release/image checks finish before any package files are changed.
    if not args.dry_run:
        for path, content, original in zip(paths, updated, contents):
            if content != original:
                path.write_text(content)
    print('Update prepared for review.' if updates else 'No updates available.')


if __name__ == '__main__':
    main()
