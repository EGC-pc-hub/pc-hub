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
