import base64
import hashlib
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SecretTests(unittest.TestCase):
    def source(self, mode='normal'):
        script = r'''
app_entropy_identifier=test
ip() { printf '1.1.1.1 dev eth0 src 192.168.1.50\n'; }
stat() { printf '998\n'; }
derive_entropy() {
 case "$1:$AUDIT_MODE" in
  *-encryption-key:failure) return 1;;
  *-encryption-key:empty) return 0;;
  *-jwt-secret:failure_jwt) return 1;;
  *-mongo-password:failure_mongo) return 1;;
  *-database-user-password:failure_app) return 1;;
 esac
 printf '%s\n' "$1"
}
source koningkoffie-checkmate/exports.sh || exit 11
printf '%s\n' "$APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY"
printf '%s\n' "$APP_KONINGKOFFIE_CHECKMATE_MONGO_PASSWORD"
printf '%s\n' "$APP_KONINGKOFFIE_CHECKMATE_DB_PASSWORD"
'''
        return subprocess.run(['bash', '-c', script], cwd=ROOT, env={**os.environ, 'AUDIT_MODE': mode}, capture_output=True, text=True)

    def test_preserves_existing_encryption_bytes_including_newline(self):
        r = self.source()
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = base64.b64encode(hashlib.sha256(b'test-encryption-key\n').digest()).decode()
        self.assertEqual(r.stdout.splitlines()[0], expected)
        self.assertEqual(r.stdout.splitlines()[1], 'test-mongo-password')
        self.assertNotEqual(r.stdout.splitlines()[1], r.stdout.splitlines()[2])

    def test_derivation_failures_abort(self):
        for mode in ['failure', 'empty', 'failure_jwt', 'failure_mongo', 'failure_app']:
            with self.subTest(mode=mode):
                self.assertEqual(self.source(mode).returncode, 11)


if __name__ == '__main__':
    unittest.main()
