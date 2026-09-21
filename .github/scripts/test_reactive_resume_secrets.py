import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'koningkoffie-reactive-resume'
SECRETS = {
    'APP_KONINGKOFFIE_REACTIVE_RESUME_POSTGRES_PASSWORD': 'postgres-password',
    'APP_KONINGKOFFIE_REACTIVE_RESUME_AUTH_SECRET': 'auth-secret',
    'APP_KONINGKOFFIE_REACTIVE_RESUME_ENCRYPTION_SECRET': 'encryption-secret',
}


class SecretTests(unittest.TestCase):
    def source(self, mode='normal', suffix=''):
        script = r'''
set -euo pipefail
app_entropy_identifier=test
ip() { printf '1.1.1.1 dev eth0 src 192.168.1.50\n'; }
derive_entropy() {
 if [[ "$1" == "test-$AUDIT_SUFFIX" ]]; then
  case "$AUDIT_MODE" in
   failure) printf 'partial-output'; return 1;;
   empty) printf '\n'; return 0;;
   pipeline_failure) false | cat; return $?;;
  esac
 fi
 printf '%s\n' "$1"
}
source koningkoffie-reactive-resume/exports.sh || exit 11
# A child shell verifies that the values are exported, not just assigned.
bash -c 'printf "%s\n" "$APP_KONINGKOFFIE_REACTIVE_RESUME_POSTGRES_PASSWORD" "$APP_KONINGKOFFIE_REACTIVE_RESUME_AUTH_SECRET" "$APP_KONINGKOFFIE_REACTIVE_RESUME_ENCRYPTION_SECRET"'
'''
        return subprocess.run(['bash', '-c', script], cwd=ROOT, capture_output=True, text=True,
                              env={**os.environ, 'AUDIT_MODE': mode, 'AUDIT_SUFFIX': suffix})

    def test_preserves_existing_secret_values_and_exports(self):
        result = self.source()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['test-' + suffix for suffix in SECRETS.values()])

    def test_failed_derivations_abort_even_with_partial_output(self):
        for suffix in SECRETS.values():
            with self.subTest(suffix=suffix):
                result = self.source('failure', suffix)
                self.assertEqual(result.returncode, 11)
                self.assertEqual(result.stdout, '')

    def test_empty_derivations_abort(self):
        for suffix in SECRETS.values():
            with self.subTest(suffix=suffix):
                self.assertEqual(self.source('empty', suffix).returncode, 11)

    def test_failed_derivation_pipeline_aborts(self):
        for suffix in SECRETS.values():
            with self.subTest(suffix=suffix):
                self.assertEqual(self.source('pipeline_failure', suffix).returncode, 11)


@unittest.skipUnless(shutil.which('docker'), 'Docker Compose is not installed')
class ComposeSecretTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        proxy = Path(self.directory.name) / 'proxy.yml'
        proxy.write_text('services:\n  app_proxy:\n    image: getumbrel/app-proxy:validation-only\n')
        self.command = ['docker', 'compose', '-p', 'reactive-resume-validation',
                        '-f', str(APP / 'docker-compose.yml'), '-f', str(proxy), 'config', '--format', 'json']
        self.env = {**os.environ, 'APP_DATA_DIR': self.directory.name, 'APP_PROXY_PORT': '3067',
                    'APP_KONINGKOFFIE_REACTIVE_RESUME_LOCAL_IP': '192.168.1.50',
                    **{key: 'test-' + suffix for key, suffix in SECRETS.items()}}

    def test_valid_credentials_reach_both_services(self):
        result = subprocess.run(self.command, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        server = services['server']['environment']
        self.assertEqual(services['db']['environment']['POSTGRES_PASSWORD'], 'test-postgres-password')
        self.assertIn(':test-postgres-password@', server['DATABASE_URL'])
        self.assertEqual(server['AUTH_SECRET'], 'test-auth-secret')
        self.assertEqual(server['ENCRYPTION_SECRET'], 'test-encryption-secret')

    def test_missing_and_empty_secrets_prevent_startup(self):
        for key in SECRETS:
            for value in (None, ''):
                with self.subTest(key=key, value=value):
                    env = self.env.copy()
                    if value is None:
                        del env[key]
                    else:
                        env[key] = value
                    result = subprocess.run(self.command, env=env, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(key, result.stderr)


if __name__ == '__main__':
    unittest.main()
