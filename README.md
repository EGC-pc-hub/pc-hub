<div style="text-align: center;">
  <img src="app/static/img/pc-hub-logo.jpeg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

## Fakenodo (Zenodo test service)

The app can run a tiny Zenodo-like HTTP service for local development and tests. It exposes only the minimum endpoints UVLHub needs (create deposition, publish, list versions) and follows Zenodo’s basic rules: metadata-only edits do not create a new DOI; changing/adding files and publishing creates a new DOI/version. See detailed setup and usage in:

- [fakenodo/README.md](fakenodo/README.md)

Quick setup:

1. Start the service locally:

   ```pwsh
   python -m fakenodo
   ```

2. Uncomment the environment variable FAKENODO_URL in your .env file:

   ```
   FAKENODO_URL = "http://localhost:5005/api/deposit/depositions"
   ```

3. (Optional) Import the Postman collection from `fakenodo/postman/` to run the end-to-end flow (create → publish v1 → metadata publish (same DOI) → file upload → publish v2 → list versions).

## GitHub backup (OAuth)

The app can create a repository in the authenticated user account and upload all dataset files using GitHub OAuth (no Personal Access Token required). See detailed setup and usage in:

- [docs/github-backup.md](docs/github-backup.md)

Quick setup:

Once you have logged into GitHub, click on your profile picture and select ‘Settings’ from the menu. Next, select ‘Developer settings’ from the sidebar on the left. Click on ‘OAuth Apps’ and press the ‘New OAuth App’ button.

1. Create a GitHub OAuth App with callback URL `https://YOUR_DOMAIN/github/callback` (or `http://localhost:PORT/github/callback` for local) and with homepage URL `https://YOUR_DOMAIN` (or http://localhost for local).
2. Set env vars:
  - `GITHUB_CLIENT_ID`
  - `GITHUB_CLIENT_SECRET`
3. On a dataset you own, click “Backup to Github”. First time will open a popup to login/authorize; after accepting, the backup runs and you’ll see a success alert and a link to the repository.
## Two-Factor Authentication (TwoAuth)

The app implements a two-factor authentication (2FA) system using email. It adds an extra layer of security by requiring users to enter a verification code sent to their email address during login and signup. See detailed setup and usage in:

- [docs/TwoAuth.md](docs/TwoAuth.md)

Quick setup:

The system is pre-configured to work with Gmail using App Passwords:

1. Enable 2-Step Verification on your Google Account at [Google Account Security](https://myaccount.google.com/security).
2. Generate an App Password in your Google Account settings (search for "App passwords") and create a new app password for PC-Hub.
3. Set env vars:
  - `MAIL_USERNAME` (your Gmail address)
  - `MAIL_PASSWORD` (the 16-character App Password)
  - `MAIL_DEFAULT_SENDER` (your Gmail address)
  - `ENABLE_2FA=true`
4. During login/signup, users will be prompted to enter the 6-digit code sent to their registered email.

> [!NOTE]
> **TwoAuth is not implemented on Render** because [Render does not allow mail servers to run on their platform](https://community.render.com/t/mail-server-on-render-com/10529). For deployments on Render, TwoAuth must be disabled by setting `ENABLE_2FA=false`.