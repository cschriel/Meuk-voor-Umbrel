# Koning Koffie ☕

### Meuk voor Umbrel. Now with a README, so you know it's serious.

I wanted to make a resume. Naturally, I started by maintaining an app store.

Welcome to **Koning Koffie**, a personal Umbrel Community App Store with a target audience of one. Market research was brief. The stakeholder meeting went badly anyway.

## Our extensive catalogue

**Reactive Resume.**

You can use it to explain to prospective employers that you're good at prioritising, while carefully omitting the evening you spent configuring infrastructure to edit a PDF.

**Tdarr.**

Automated media transcoding and health checks. Because the files were taking up space, and apparently the solution was another application.

After installing, open Tdarr through Umbrel and add a library with a source folder under `/media` (Umbrel's shared downloads folder). Set the transcode cache to `/temp`. Review the plugins or flow before enabling processing, since Tdarr can replace original files, and leave enough free disk space for the cache.

The included node, **Umbrel**, has one GPU transcode worker plus CPU workers for software tasks and health checks. Intel GPU access is enabled for Umbrel Home through `/dev/dri`; Tdarr's startup script grants its user the matching device group permissions. Select an Intel Quick Sync (QSV) or VAAPI encoding plugin or flow in your library to use hardware encoding, then check a sample job's report for `hevc_qsv`, `h264_qsv`, `hevc_vaapi`, or `h264_vaapi`, depending on your selected encoder. See [Tdarr's hardware transcoding documentation](https://docs.tdarr.io/docs/installation/docker/hardware-transcoding/).

This package requires `/dev/dri` on the host. On hardware without it, remove the `devices` mapping and set `transcodegpuWorkers` to `"0"` before starting. External nodes require additional configuration.

**Checkmate.**

Uptime monitoring, response-time charts, and incident tracking. So now there's an application to tell me when the other applications have stopped being applications.

Open Checkmate through Umbrel on port `52345` and create your administrator account on first launch. Use your Umbrel's local IPv4 address; the package detects it automatically for notification links. Add your first website or service monitor using an address reachable from Umbrel. Accounts, settings, and monitoring history persist in MongoDB, and authentication and encryption secrets are derived automatically per installation.

To monitor Umbrel's Docker containers, add a **Docker** monitor with host URL `unix:///var/run/docker.sock`. Existing monitor URLs continue to work. This now connects to a local filtering proxy: container listing, statistics, limited inspection, and the most recent 500 log lines are allowed; Docker mutations, file archives, and other API endpoints are denied. Inspection responses omit environment variables. The proxy alone holds the host socket, runs without a TCP network, and shares its filtered socket with Checkmate. Container logs can still contain sensitive application output; enable them only where useful.

[Capture 1.4.0](https://github.com/bluewave-labs/capture/releases/tag/v1.4.0) is included for Umbrel hardware monitoring. In Checkmate's **Infrastructure** section, add a monitor named **Umbrel**:

- **Capture endpoint:** `http://UMBREL-IP:59232/api/v1/metrics`, replacing `UMBREL-IP` with your Umbrel's local IPv4 address.
- **Authorization secret:** the app password shown by Umbrel for Checkmate. Paste the value alone, without `Bearer`. This is Capture's API key; your Checkmate login is the account you create yourself.

Capture starts with the app and uses host networking for host interface counters, plus read-only mounts of `/proc`, `/sys`, `/etc/os-release`, and the host filesystem at `/host/root` for CPU, memory, disk usage/I/O, and OS information. Disk paths may appear with the `/host/root` prefix. Temperature readings depend on the host's sensors. The agent runs as its image's non-root user with capabilities dropped; S.M.A.R.T. disk health is not included. Its API requires the generated key and listens on host port `59232`, which must be available.

Configure SMTP in Checkmate if you want email delivery. Checkmate handles its own login, with the extra Umbrel login disabled. Public status pages are accessible without an Umbrel account to anyone who can reach the app on your network.

The included MongoDB 8.0 requires AVX on x86-64 or ARMv8.2-A or newer on ARM, which excludes Raspberry Pi 4. See [MongoDB's hardware requirements](https://www.mongodb.com/docs/manual/administration/production-notes/). Checkmate is pinned to [v3.12.0](https://github.com/bluewave-labs/Checkmate/releases/tag/v3.12.0), with all container images pinned by digest. The Node image used by the Docker filter and MongoDB are updated manually.

## Enterprise-grade ambition

- **Self-hosted:** because apparently I needed to be responsible for another thing.
- **Automated updates:** yesterday's decisions, delivered to tomorrow's problems. Reactive Resume updates automatically; Checkmate and Capture updates arrive as pull requests for review. Tdarr is updated manually.
- **Community-driven:** I have occasionally discussed it with myself.
- **Coffee-powered:** the only dependency with a reliable upgrade cycle.
- **A focused roadmap:** get this working, then develop an entirely unrelated obsession.

## Support

The **Update Checkmate and Capture** GitHub Action checks stable upstream releases daily at 05:43 UTC and can also be run manually from Actions. It verifies image digests and availability for both amd64 and arm64, then validates Compose and Umbrel installer compatibility before opening or updating one review PR. Capture-only updates increment the Umbrel package revision. MongoDB stays pinned and is updated manually.

The workflow uses the existing `SYNC_TOKEN` secret when available (it needs repository contents and pull-request write access), otherwise `GITHUB_TOKEN`. For the fallback, enable **Allow GitHub Actions to create and approve pull requests** in the repository's Actions settings. The workflow never approves or merges its PR. Validation also runs before PR creation, so it does not depend on whether a bot-created PR triggers another workflow. The CI smoke test starts a disposable stack with test credentials and a fake Docker API, checks data-preserving database migration and restricted permissions, exercises the real Docker client through the filter, and checks Capture authentication. Review upstream configuration changes and verify physical host metrics on Umbrel before merging.

There is no support department. There is a person with a browser, several open tabs, and a growing suspicion that this could have been simpler.

If it breaks, you're welcome to open an issue. This will convert the problem into a problem with a number.

## Contributing

Found something worth fixing? Open a pull request.

Found a way to turn this into a subscription platform? Please close the tab.

## Acknowledgements

[Reactive Resume](https://github.com/amruthpillai/reactive-resume) provides the resume builder. [Tdarr](https://tdarr.io) provides the media processing. [Checkmate](https://github.com/bluewave-labs/Checkmate) provides the monitoring. [Umbrel](https://umbrel.com) provides the platform.

I provide the additional configuration and the opportunity for something else to go wrong.

---

Built for personal use. Documented with disproportionate confidence.
