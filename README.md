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

To monitor Umbrel's Docker containers, add a **Docker** monitor with host URL `unix:///var/run/docker.sock`. The package mounts the host socket and automatically adds its numeric group ID to Checkmate's supplementary groups so its non-root user can connect. This monitor covers all containers on the host. As explained in [Checkmate's installation guide](https://checkmate.so/docs/getting-started/installation), socket access grants host-level control; the read-only mount does not restrict Docker API operations.

[Capture 1.4.0](https://github.com/bluewave-labs/capture/releases/tag/v1.4.0) is included for Umbrel hardware monitoring. In Checkmate's **Infrastructure** section, add a monitor named **Umbrel**:

- **Capture endpoint:** `http://UMBREL-IP:59232/api/v1/metrics`, replacing `UMBREL-IP` with your Umbrel's local IPv4 address.
- **Authorization secret:** the app password shown by Umbrel for Checkmate. Paste the value alone, without `Bearer`. This is Capture's API key; your Checkmate login is the account you create yourself.

Capture starts with the app and uses host networking for host interface counters, plus read-only mounts of `/proc`, `/sys`, `/etc/os-release`, and the host filesystem at `/host/root` for CPU, memory, disk usage/I/O, and OS information. Disk paths may appear with the `/host/root` prefix. Temperature readings depend on the host's sensors. The agent runs as its image's non-root user with capabilities dropped; S.M.A.R.T. disk health is not included. Its API requires the generated key and listens on host port `59232`, which must be available.

Configure SMTP in Checkmate if you want email delivery. Checkmate handles its own login, with the extra Umbrel login disabled. Public status pages are accessible without an Umbrel account to anyone who can reach the app on your network.

The included MongoDB 8.0 requires AVX on x86-64 or ARMv8.2-A or newer on ARM, which excludes Raspberry Pi 4. See [MongoDB's hardware requirements](https://www.mongodb.com/docs/manual/administration/production-notes/). Checkmate is pinned to [v3.12.0](https://github.com/bluewave-labs/Checkmate/releases/tag/v3.12.0), with all three container images pinned by digest.

## Enterprise-grade ambition

- **Self-hosted:** because apparently I needed to be responsible for another thing.
- **Automated Reactive Resume updates:** yesterday's decisions, delivered to tomorrow's problems. Tdarr and Checkmate are pinned to verified images and updated manually in this store.
- **Community-driven:** I have occasionally discussed it with myself.
- **Coffee-powered:** the only dependency with a reliable upgrade cycle.
- **A focused roadmap:** get this working, then develop an entirely unrelated obsession.

## Support

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
