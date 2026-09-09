# Koning Koffie — Umbrel Community App Store

A personal app store by [cschriel](https://github.com/cschriel), for Umbrel Home.

## Installation

1. Publish this repository on GitHub (commit and push from VS Code).
2. Open the App Store on your Umbrel and select Community App Stores from the menu.
3. Add this repository: `https://github.com/cschriel/Meuk-voor-Umbrel`.
4. Open **Koning Koffie**, install **Reactive Resume**, and wait for the app to start.
5. Open the app from your Umbrel home screen and create your own account.

Use your Umbrel's local `.local` address, such as `http://umbrel.local`,
to access the dashboard. The app uses the same device address on port **3067**.
If your device has a different name, the configuration uses that name automatically.
Port 3067 must be available on your device.

## Included

- Reactive Resume **5.3.0**, with PDF export in your browser.
- PostgreSQL **17.9** and persistent local storage for uploads.
- Umbrel authentication to protect access to the app.
- Separate, automatically derived database, session, and encryption secrets.
- Official images pinned to a version and image digest.

The public repository contains installation files, not resumes or passwords.

## Limitations of this basic installation

- SMTP is not configured. Emails are not sent; password recovery requires
  additional SMTP configuration. Keep your Reactive Resume password safe.
- The AI Agent workspace (Redis/S3) is not included. External AI providers are optional
  and receive the data you send to them when used.
- The configuration uses your local Umbrel hostname. Access through an IP address,
  external domain, Tor, or reverse proxy has not been tested and may require changes to `APP_URL`.
- Account registration is enabled so you can sign up on first launch.
  The app remains protected by Umbrel's login screen.

## Data and updates

The database is stored in `data/postgres`, and uploads in `data/uploads`, within
Umbrel's app data for `koningkoffie-reactive-resume`. Create a consistent backup of
both (stop the app first for a file-based backup). Do not change the app ID after installation.
Only upgrade to a new PostgreSQL major version with an appropriate data migration.

## Verification before use

The package configuration and public images have passed local checks. Installation
on an Umbrel has not yet been tested. On your device, check registration, login,
resume creation, image upload, and PDF export. Then restart the app and confirm
that your account, resume, and image are preserved.

## Sources

- [Reactive Resume](https://github.com/amruthpillai/reactive-resume)
- [Self-hosting](https://docs.rxresu.me/self-hosting/docker)
- [Umbrel Community App Store template](https://github.com/getumbrel/umbrel-community-app-store)
