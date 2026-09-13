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

## Enterprise-grade ambition

- **Self-hosted:** because apparently I needed to be responsible for another thing.
- **Automated Reactive Resume updates:** yesterday's decisions, delivered to tomorrow's problems. Tdarr is pinned to a verified image and updated manually in this store.
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

[Reactive Resume](https://github.com/amruthpillai/reactive-resume) provides the resume builder. [Tdarr](https://tdarr.io) provides the media processing. [Umbrel](https://umbrel.com) provides the platform.

I provide the additional configuration and the opportunity for something else to go wrong.

---

Built for personal use. Documented with disproportionate confidence.
