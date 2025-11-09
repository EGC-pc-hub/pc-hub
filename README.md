<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

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
