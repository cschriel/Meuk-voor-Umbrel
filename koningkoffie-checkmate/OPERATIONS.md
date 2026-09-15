# Operating Checkmate on Umbrel

## Upgrade and access

Version 3.12.0.2 keeps the installed Checkmate/Capture image versions and the existing successful secret derivations. On startup, `db_init` authenticates with the existing MongoDB administrator and creates or updates `checkmate_app` with `readWrite` access only to `uptime_db`, plus a narrowly scoped `serverStatus` privilege for Checkmate’s database diagnostics. Existing collections remain untouched. Checkmate waits for this step before starting. The root account remains available for database administration, but its credentials are no longer passed to Checkmate.

Existing Docker monitors using `unix:///var/run/docker.sock` keep working through the local filter. Other Unix paths or custom Docker API clients are not supported by the filter. It permits Checkmate's ping, container list, inspection, non-streaming statistics and bounded logs. Mutations, exec, file archive/export, environment variables in inspection, and TCP access to the proxy are excluded. The small proxy process still has full daemon authority internally; it is an isolation boundary, not Docker authorization enforcement on the host. Do not add the raw socket back to the Checkmate container.

The proxy and MongoDB helper use files generated from `.template` files so Umbrel 1.7.x copies them during upgrades. Volume declarations remain strings for the same installer compatibility reason.

## Address and authentication

The dashboard uses Checkmate accounts; Umbrel proxy authentication remains disabled as requested. Capture's separate API key is the app password displayed by Umbrel. Its endpoint remains `http://UMBREL-IP:59232/api/v1/metrics`.

Put your URL (for example `https://your-monitoring-hostname`) on a single line in `app-data/koningkoffie-checkmate/data/public-url`, then restart via Umbrel, to override automatic LAN URL detection. This only configures Checkmate's public URL: configure HTTPS in your reverse proxy separately. The plain-text setting is read by `exports.sh` and survives package updates.

Capture continues to use host networking and an authenticated HTTP listener on 59232. Network reachability and TLS termination are host/network configuration, not silently changed by this package. Keep access within a trusted LAN or protected tunnel and do not forward this port to the Internet. A separate TLS endpoint is needed if untrusted networks must carry its bearer key.

## Health and diagnostics

Checkmate's health check now requires both worker readiness (including its database connection) and the web API health endpoint. The Docker proxy health check exercises its real socket path. Docker health status is diagnostic; Docker does not restart a container just because it becomes unhealthy. Umbrel remains responsible for app lifecycle and restart policies stay `on-failure` to retain existing behavior.

For a read-only diagnostic on Umbrel:

```bash
sudo bash /home/umbrel/umbrel/app-data/koningkoffie-checkmate/hooks/diagnostics
```

This prints container status, two Capture network samples five seconds apart, host counters, and Docker proxy reachability. It does not print the API key. Capture's minimal image does not contain curl or a shell, so diagnostics run from the host. Interface counters should increase with traffic. The Checkmate 3.12.0 network charts can show zero when a chart bucket contains only one sample; use a 15-second monitor interval and compare with the day view. The misleading container-namespace notice does not prove network isolation.

Checkmate 3.12.0 also labels total disk capacity as “Free” in its disk gauge. Compare the actual `free_bytes` in Capture or `df -h`; don't delete system files based on that label. These upstream UI behaviors have not been patched or reported upstream by this repository. There is no supported global 24-hour formatting toggle in the pinned release; display timezone is independently configurable.

## Backup and restore

Persistent storage is not a backup. Use Umbrel's backup facility and verify a restoration before relying on it. Keep backups encrypted and access restricted: the database includes accounts, monitoring history, API credentials, and notification settings.

For a manual consistent filesystem backup:

1. Record the installed package revision and image digests from `docker-compose.yml`.
2. Preserve the original Umbrel secret/seed recovery material securely using your Umbrel backup procedure. Checkmate's encryption key, MongoDB administrator password, application password, JWT key, and Capture key derive from it. A database-only backup on a different Umbrel seed is insufficient.
3. Stop Checkmate through Umbrel and confirm its server and database containers have stopped. Copy/archive the entire `app-data/koningkoffie-checkmate` directory while stopped; do not copy live MongoDB files and assume the result is consistent.
4. Restart the app through Umbrel and verify monitoring resumed.

Restore first to a test installation with the same secret derivation inputs and pinned images. Restore files with their original ownership and permissions while the app is stopped, then start through Umbrel. Confirm sign-in, existing monitors/history, database migration completion, Capture authentication, and decryption of any stored Docker TLS credentials. The `docker-monitor-socket` volume is disposable runtime state and need not be backed up.

Do not rotate or replace the original Umbrel seed or change the encryption derivation during recovery. Cross-seed migration requires an explicit credential/key migration plan. Do not simply change `MONGO_INITDB_ROOT_PASSWORD`: it does not change an existing MongoDB user's password.

## Remaining host-dependent hardening

Capture retains the read-only host root/proc/sys mounts needed by the current host-metrics implementation. Its non-root user, dropped capabilities and no-new-privileges setting reduce risk, but readable host files remain visible. Narrowing those mounts requires testing the specific Umbrel filesystem layout and connected disks; it is not claimed as fixed here.

Running services now rotate Docker JSON logs at 10 MB per file, retaining three files each. Monitoring database retention remains configured in Checkmate's Monitoring settings. Consider a separate external availability check for Umbrel: Checkmate cannot reliably notify you about its own complete outage.
