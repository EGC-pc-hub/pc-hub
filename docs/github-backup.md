# GitHub Dataset Backup (OAuth)

This feature automatically creates a repository in the authenticated user's GitHub account and uploads all the files of a dataset there, without using personal access tokens (PAT). The flow uses OAuth and the token is stored in the user's session.

## User experience overview

- On the dataset page, there is a “Backup to GitHub” button.
- If it's the first time:

  - A popup opens with GitHub login/consent.

  - After authorizing, the server creates the repo and uploads the files; the popup notifies the page and closes.
  - The page shows a success notice with a link to the repo and the number of files uploaded.

- If already authorized:

  - The backup is performed via AJAX without redirects.

  - AJAX (Asynchronous JavaScript and XML) refers to making background HTTP requests from the browser (via fetch/XHR) to update the page without a full reload; nowadays JSON is typically used instead of XML.

  - In this flow, the browser calls our backend endpoints over AJAX; the server then performs the actual GitHub REST API calls using the user's OAuth token stored in session.

- If the dataset does not belong to the user:

  - A notice is shown: “You are not authorized to back up this dataset.” and no interaction with GitHub is initiated.

## Prerequisites

1. [Create a GitHub OAuth App in your GitHub user/organization](#oauth-app-guide)

2. Configure environment variables in the backend:

```env
# GitHub OAuth
GITHUB_CLIENT_ID=xxxxx
GITHUB_CLIENT_SECRET=yyyyy
```

- Important: PAT is not used. The only requirement is to have `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` configured and the correct callback.
- Requested scope: `repo` (required to create private repositories in the user's account). `workflow` or organization access are not requested.

## How to create the GitHub OAuth App (step by step) <a id="oauth-app-guide"></a>

1) Decide where to create it

- Recommended: in your user account (Settings → Developer settings → OAuth Apps).
- You can also create it under an organization (Organization settings → Developer settings → OAuth Apps), but our app doesn't use organization permissions; backup repos will ALWAYS be created in the authenticated user's account.

2) Create the app

- In GitHub, go to:
  - User: Profile avatar → Settings → Developer settings → OAuth Apps → New OAuth App
  - Organization: Org → Settings → Developer settings → OAuth Apps → New OAuth App
- Fill out the fields:
  - Application name: e.g., “PC-Hub Backup” (free text)
  - Homepage URL: the base URL of your deployment, e.g., `https://YOUR_DOMAIN`
  - For local development: `http://localhost`
  - Authorization callback URL: `https://YOUR_DOMAIN/github/callback`
    - For local development: `http://localhost:PORT/github/callback`
  - Application description/logo: optional

3) Get credentials

- After registering, you'll see the `Client ID`.
- Click “Generate a new client secret” to obtain the `Client Secret`.
- Place both values in the app's environment variables (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`) and restart the server.

4) Important notes

- A GitHub OAuth App supports a SINGLE callback URL. To work locally and in production, we recommend two apps (one per environment), or temporarily changing the callback. Alternative: use a publicly accessible domain (e.g., an ngrok-like tunnel) that works for both.

- Scopes: only `repo`. We don't request `workflow`.

- “Organization access” in the consent screen is optional; the app doesn't use it to create repos. Repos are created in the user's account.

- Security: if the secret is leaked, rotate the `Client Secret` from the OAuth App page. From GitHub → Settings → Applications → Authorized OAuth Apps you can revoke the app's access.

## Relevant endpoints

- GitHub authentication (prefix `/auth`):
  - `GET /github/status` → { connected: true|false }
  - `GET /github/login?next=<url>` → redirects to GitHub (in an HTML page with client-side redirection for proxy compatibility)
  - `GET /github/callback` → exchanges `code` for `access_token` (stored in session)

- Dataset backup:
  - `GET  /dataset/<id>/backup/authorised-user` → verifies the dataset belongs to the user. If not, 403.
  - `POST /dataset/<id>/backup/github` → creates repo and uploads files (via AJAX).
  - `GET  /dataset/<id>/backup/github-ui?return=<url>[&popup=1]` → does the same on the server and redirects back with success parameters; if `popup=1`, responds with a page that does `postMessage` and closes itself.

## Technical details

- Repositories are always under the authenticated user's account (organizations are not allowed).
- Repository name: generated from the dataset title (`repo_name_formatting`). If it already exists, a friendly error is returned indicating there is already a repo with that name and it must be renamed or deleted.
- Target branch: the default branch of the newly created repository (usually `main`).
- Token: the GitHub `access_token` is stored in `session["github_token"]`. It is not persisted in the database.

### Services

- `GitHubRepoService(token: str)`
  - Creates repos with `POST https://api.github.com/user/repos`.
  - Requires OAuth token with `repo` scope.
- `GitHubContentService(token: str, repo_full_name: str, branch: str)`
  - Uploads files with `PUT /repos/{owner}/{repo}/contents/{path}` (GitHub Contents API).

### Client flow

1. When clicking “Backup to GitHub”:
   - First call `/dataset/<id>/backup/authorised-user`.
   - If OK, check `/github/status`.
     - If not connected: open a popup to `/github/login?next=/dataset/<id>/backup/github-ui?...&popup=1`.
     - If connected: `POST /dataset/<id>/backup/github-create` via AJAX.
2. After the backup:
   - If popup: the server returns a page that does `window.opener.postMessage({ type: 'github-backup-done', url, uploaded }, origin)` and closes.
   - If redirect: it returns with `?backup=done&url=...&uploaded=...`. The page shows the notice and clears the parameters from the URL.

## Security and privacy

- The OAuth token is stored in session. When logging out of the app, the session is also invalidated; if you want to revoke the app's permissions in GitHub, you can do so from GitHub → Settings → Applications → Authorized OAuth Apps.
- The requested scope is the minimum required (`repo`) to allow private repositories.
- No secrets are exposed to the client; `state` and `next` are stored in session and the redirection to GitHub is done with a small HTML page to avoid issues with proxies.

## Common issues (troubleshooting)

- Callback/mismatch error in GitHub:
  - Check that the OAuth App has `Authorization callback URL` = `https://YOUR_DOMAIN/github/callback` (or `http://localhost:PORT/github/callback`).
- Popup blocked:
  - The flow falls back to a full redirect; allow popups for a better UX.
- 403 Not authorized:
  - The dataset does not belong to the authenticated user.
- 401 Not authenticated:
  - The session expired or GitHub login has not been performed.
- 422 when creating repo (existing name):
  - Friendly message: “A repository with this name already exists…”. Rename the dataset or delete/rename the existing repo in GitHub.
- Issues with proxies/reverse proxy:
  - The login redirection is done via HTML+JS (not 302) to avoid the proxy modifying/ignoring the `Location` header or rewriting routes/domains.

## Quick test (local)

1. Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in your `.env` and restart.
2. Open a dataset you own in the app.
3. Click “Backup to GitHub”.
   - If it's the first time, authorize in the popup and wait for the success notice.
4. Verify that the repo has been created in your GitHub account and that it contains the dataset files.