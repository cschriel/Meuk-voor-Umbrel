"""Update the Umbrel Relay package from the latest upstream main commit."""

import argparse
import json
import os
from pathlib import Path
import re
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "koningkoffie-relay"
REPO = "richardosseweijer/Relay-AV-Room-Control-"
IMAGE = "ghcr.io/cschriel/relay-av-room-control"


def fetch_json(url, token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "koningkoffie-relay-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def replace_once(pattern, replacement, text):
    result, count = re.subn(pattern, lambda _: replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Expected exactly one match for {pattern}; found {count}")
    return result


def parse_version(value):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError(f"Expected a stable semantic version, got {value!r}")
    return tuple(map(int, match.groups()))


def next_package_version(current, upstream):
    match = re.fullmatch(r"(\d+\.\d+\.\d+)\.(\d+)", current)
    if not match:
        raise ValueError(f"Unexpected Umbrel package version {current!r}")
    current_upstream, revision = match.groups()
    if parse_version(upstream) < parse_version(current_upstream):
        raise ValueError(f"Refusing upstream version downgrade {current_upstream} -> {upstream}")
    next_revision = int(revision) + 1 if upstream == current_upstream else 1
    return f"{upstream}.{next_revision}", f"{upstream}-{next_revision}"


def update_files(commit, upstream_version):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid upstream commit SHA")

    dockerfile_path = APP / "Dockerfile"
    compose_path = APP / "docker-compose.yml"
    manifest_path = APP / "umbrel-app.yml"
    dockerfile = dockerfile_path.read_text()
    compose = compose_path.read_text()
    manifest = manifest_path.read_text()

    current_commit = re.search(r"^ARG RELAY_COMMIT=([0-9a-f]{40})$", dockerfile, re.MULTILINE)
    current_version = re.search(r'^version: "([^"]+)"$', manifest, re.MULTILINE)
    if not current_commit or not current_version:
        raise ValueError("Could not read the current Relay package state")
    if current_commit.group(1) == commit:
        print(f"Already current: {commit[:7]}. No changes.")
        return False

    package_version, image_tag = next_package_version(current_version.group(1), upstream_version)
    dockerfile = replace_once(
        r"^ARG RELAY_COMMIT=[0-9a-f]{40}$",
        f"ARG RELAY_COMMIT={commit}",
        dockerfile,
    )
    compose = replace_once(
        rf"^    image: {re.escape(IMAGE)}:\S+$",
        f"    image: {IMAGE}:{image_tag}",
        compose,
    )
    manifest = replace_once(
        r'^version: "[^"]+"$',
        f'version: "{package_version}"',
        manifest,
    )
    manifest = replace_once(
        r"^icon: https://raw\.githubusercontent\.com/.+$",
        f"icon: https://raw.githubusercontent.com/{REPO}/{commit}/public/favicon.svg",
        manifest,
    )
    notes = f"Updated Relay {upstream_version} to upstream main commit {commit[:7]}."
    manifest = replace_once(
        r'^releaseNotes: "[^"\n]*"$',
        "releaseNotes: " + json.dumps(notes),
        manifest,
    )

    dockerfile_path.write_text(dockerfile)
    compose_path.write_text(compose)
    manifest_path.write_text(manifest)
    print(f"Update {current_commit.group(1)[:7]} -> {commit[:7]} as {package_version}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN")
    commit = fetch_json(f"https://api.github.com/repos/{REPO}/commits/main", token)["sha"]
    package = fetch_json(
        f"https://api.github.com/repos/{REPO}/contents/package.json?ref={commit}", token
    )
    import base64

    upstream_version = json.loads(base64.b64decode(package["content"]))["version"]
    parse_version(upstream_version)
    if args.dry_run:
        current = re.search(
            r"^ARG RELAY_COMMIT=([0-9a-f]{40})$",
            (APP / "Dockerfile").read_text(),
            re.MULTILINE,
        ).group(1)
        print(
            f"Current {current[:7]}; upstream {commit[:7]}; version {upstream_version}; "
            f"update needed: {current != commit}"
        )
        return
    update_files(commit, upstream_version)


if __name__ == "__main__":
    main()
