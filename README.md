# KoningKoffie's appstore ☕

### Meuk voor Umbrel. A personal app store with an unnecessarily official name.

I wanted to make a resume. Naturally, I started by maintaining an app store.

**KoningKoffie** is a small community app store for [Umbrel](https://umbrel.com), containing things I wanted to run on my own hardware. The target audience is mostly me, but you're welcome to join the stakeholder meeting. Bring coffee. There is no agenda.

## The extensive catalogue

### Reactive Resume

Build a resume, pick a template, and export it as a PDF. Your accounts, resumes, and uploads stay on your Umbrel.

Finally, a way to tell employers you're good at prioritising without mentioning the infrastructure project you started to format your work history.

### Tdarr

Automate media transcoding and library health checks with configurable plugins and flows. Includes a server and a worker node, with Intel GPU support for Umbrel Home.

Because buying more storage would have been too straightforward.

### Checkmate

Monitor uptime, response times, and incidents for your websites and services. Includes Docker container monitoring and Capture for keeping an eye on your Umbrel's hardware.

An application that tells you when the other applications have stopped being applications. We have achieved management.

## Getting started

Add this repository to your community app stores in Umbrel:

```text
https://github.com/cschriel/Meuk-voor-Umbrel
```

Open **Koning Koffie** in the app store, choose an app, and install it. Open the installed app through Umbrel to get started.

The procurement process is now complete. Please file your imaginary receipt.

## A few useful setup notes

### Reactive Resume

- Create your own account on first launch and use your Umbrel's local IPv4 address to sign in.
- This package is configured for personal use on your local network.
- Email delivery and password recovery by email need additional SMTP configuration. The AI Agent workspace is not included.

### Tdarr

- Add a library with a source folder under `/media`, which maps to Umbrel's shared downloads folder.
- Set the transcode cache to `/temp` and leave enough free disk space for it.
- Review your plugins or flow before starting: Tdarr can replace original media files. Enthusiasm is not a backup strategy.
- For Intel hardware encoding, choose a Quick Sync (QSV) or VAAPI plugin or flow. This package requires a host with `/dev/dri`; other hardware and external nodes need additional configuration.

### Checkmate

Create your administrator account on first launch. Use your Umbrel's local IPv4 address on port `52345`, and add monitors using addresses your Umbrel can reach.

For **Docker container monitoring**, add a Docker monitor with this host URL:

```text
unix:///var/run/docker.sock
```

For **hardware monitoring**, add a monitor in **Infrastructure** named **Umbrel**:

- **Capture endpoint:** `http://UMBREL-IP:59232/api/v1/metrics` — replace `UMBREL-IP` with your Umbrel's local IPv4 address.
- **Authorization secret:** the app password shown by Umbrel for Checkmate, without a `Bearer` prefix. This is the hardware monitoring key; your Checkmate login is the account you create yourself.

Email notifications need SMTP settings. Public status pages are visible to anyone who can reach the app on your network.

This package requires an x86-64 CPU with AVX or an ARMv8.2-A or newer CPU. Raspberry Pi 4 is not supported.

For diagnostics and backup or restore instructions, see the [Checkmate operations guide](koningkoffie-checkmate/OPERATIONS.md).

## Support

There is no support department. There is a person with a browser, several open tabs, and a growing suspicion that this could have been simpler.

If something breaks, [open an issue](https://github.com/cschriel/Meuk-voor-Umbrel/issues). Include what you were trying to do, what happened, and any useful error messages. This converts the problem into a problem with a number, which is at least administratively satisfying.

## Contributing

Found something worth fixing? Pull requests are welcome.

Found a way to turn this into a subscription platform? Please close the tab.

## Credit where it's due

The actual applications are built by the people behind [Reactive Resume](https://github.com/amruthpillai/reactive-resume), [Tdarr](https://tdarr.io), [Checkmate](https://github.com/bluewave-labs/Checkmate), and [Capture](https://github.com/bluewave-labs/capture). [Umbrel](https://umbrel.com) provides the platform.

I provide the packaging, the coffee, and another place for a configuration error to occur.

---

Built for personal use. Documented with disproportionate confidence.
