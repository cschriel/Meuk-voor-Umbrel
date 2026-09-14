import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import update_checkmate as updater

DIGEST = 'sha256:' + 'd' * 64
COMPOSE = '\n'.join([
    '    image: ghcr.io/bluewave-labs/checkmate:v3.12.0@sha256:' + 'a' * 64,
    '    image: ghcr.io/bluewave-labs/capture:v1.4.0@sha256:' + 'b' * 64,
    '    image: mongo:8.0@sha256:' + 'c' * 64,
])
MANIFEST = 'version: "3.12.0.1"\n  Capture 1.4.0 is included\nreleaseNotes: "Old notes"\n'
README = ('[Capture 1.4.0](https://github.com/bluewave-labs/capture/releases/tag/v1.4.0)\n'
          '[v3.12.0](https://github.com/bluewave-labs/Checkmate/releases/tag/v3.12.0)')


class UpdateTests(unittest.TestCase):
    def test_no_release_preserves_packaging_revision(self):
        self.assertEqual(updater.update(MANIFEST, COMPOSE, README, {}), (MANIFEST, COMPOSE, README))

    def test_capture_only_bumps_packaging_revision(self):
        m, c, r = updater.update(MANIFEST, COMPOSE, README, {'capture': ('v1.5.0', DIGEST)})
        self.assertIn('version: "3.12.0.2"', m)
        self.assertIn('Capture 1.5.0 is included', m)
        self.assertIn('[Capture 1.5.0]', r)
        self.assertIn('/capture/releases/tag/v1.5.0', r)
        self.assertIn('checkmate:v3.12.0@', c)
        self.assertIn(COMPOSE.splitlines()[-1], c)

    def test_both_updates_reset_packaging_revision(self):
        m, c, r = updater.update(MANIFEST, COMPOSE, README, {'checkmate': ('v3.13.0', DIGEST), 'capture': ('v1.5.0', DIGEST)})
        self.assertIn('version: "3.13.0"', m)
        self.assertIn('checkmate:v3.13.0@' + DIGEST, c)
        self.assertIn('[v3.13.0]', r)
        self.assertIn('/Checkmate/releases/tag/v3.13.0', r)
        self.assertIn(COMPOSE.splitlines()[-1], c)

    def test_capture_only_without_existing_revision(self):
        m, _, _ = updater.update(MANIFEST.replace('3.12.0.1', '3.12.0'), COMPOSE, README, {'capture': ('v1.5.0', DIGEST)})
        self.assertIn('version: "3.12.0.1"', m)

    def test_refuse_unstable_downgrade_and_retag(self):
        for tag in ('v3.13.0-rc.1', 'latest', 'v3.11.0', 'v3.12.0'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                updater.update(MANIFEST, COMPOSE, README, {'checkmate': (tag, DIGEST)})

    def test_reject_bad_digest_and_mismatched_package(self):
        with self.assertRaises(ValueError):
            updater.update(MANIFEST, COMPOSE, README, {'capture': ('v1.5.0', 'invalid')})
        with self.assertRaises(ValueError):
            updater.update(MANIFEST.replace('3.12.0.1', '3.11.0'), COMPOSE, README, {'capture': ('v1.5.0', DIGEST)})

    def registry(self, arches=('amd64', 'arm64'), bad_digest=False, missing_child=False):
        child = json.dumps({'schemaVersion': 2, 'config': {}}).encode()
        child_digest = 'sha256:' + hashlib.sha256(child).hexdigest()
        index = json.dumps({'manifests': [{'platform': {'os': 'linux', 'architecture': a}, 'digest': child_digest} for a in arches]}).encode()
        index_digest = 'sha256:' + hashlib.sha256(index).hexdigest()
        def fetch(url, headers=None):
            if '/token?' in url:
                return b'{"token":"test"}', {}
            if child_digest in url:
                if missing_child:
                    raise OSError('Platform image unavailable')
                return child, {'Docker-Content-Digest': child_digest}
            return index, {'Docker-Content-Digest': DIGEST if bad_digest else index_digest}
        return fetch, index_digest

    def test_verify_both_platforms_and_digest(self):
        fetch, digest = self.registry()
        with patch.object(updater, 'fetch', side_effect=fetch) as mock:
            self.assertEqual(updater.verified_image('capture', 'v1.5.0'), digest)
            self.assertEqual(mock.call_count, 4)

    def test_refuse_incomplete_or_corrupted_images(self):
        for options, error in [({'arches': ('amd64',)}, ValueError), ({'bad_digest': True}, ValueError), ({'missing_child': True}, OSError)]:
            with self.subTest(options=options):
                fetch, _ = self.registry(**options)
                with patch.object(updater, 'fetch', side_effect=fetch), self.assertRaises(error):
                    updater.verified_image('capture', 'v1.5.0')

    def test_validator_rejects_mount_that_crashed_umbrel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / '.github/scripts'
            scripts.mkdir(parents=True)
            validator = scripts / 'validate_checkmate.rb'
            validator.write_text(Path(__file__).with_name('validate_checkmate.rb').read_text())
            app = root / 'koningkoffie-checkmate'
            app.mkdir()
            (app / 'umbrel-app.yml').write_text('{}')
            (app / 'docker-compose.yml').write_text(json.dumps({'services': {'capture': {'volumes': [
                {'type': 'bind', 'source': '/', 'target': '/host/root', 'read_only': True}
            ]}}}))
            result = subprocess.run(['ruby', str(validator)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Umbrel 1.7.x requires string-form mounts', result.stderr)


if __name__ == '__main__':
    unittest.main()
