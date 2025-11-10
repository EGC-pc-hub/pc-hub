# Fakenodo (Zenodo-like fake service)

Fakenodo is a lightweight HTTP service that simulates a minimal subset of the Zenodo API for local development and testing purposes.

## Minimal Endpoints

- `POST /api/deposit/depositions` – Create a draft deposition with metadata.
- `PUT /api/deposit/depositions/{id}` – Update draft metadata only.
- `GET /api/deposit/depositions` – List all depositions.
- `GET /api/deposit/depositions/{id}` – Retrieve a single deposition.
- `DELETE /api/deposit/depositions/{id}` – Delete a deposition.
- `POST /api/deposit/depositions/{id}/files` – Add/update a file to the draft.
- `POST /api/deposit/depositions/{id}/actions/publish` – Publish the draft.
  - Metadata-only changes → same DOI (no new version).
  - File changes + publish → new DOI/version.
- `GET /api/records/{conceptrecid}/versions` – List published versions.

## Quick Start

Run the module:

```bash
python -m fakenodo
```

Server starts at `http://localhost:5005`.

## Integration with PCHub

Point PCHub to Fakenodo instead of live Zenodo via environment variable:

```bash
FAKENODO_URL=http://localhost:5005/api/deposit/depositions
```

This overrides the default Zenodo API endpoint.

## Testing

```bash
pytest fakenodo/tests -q
```

## Postman Collection

Use the included Postman suite (`fakenodo/postman/`) to test all endpoints:

Import both files:
- `Fakenodo.postman_collection.json`
- `Fakenodo.postman_environment.json`

### Requests included:

1. **Create deposition** – POST `/deposit/depositions` → `201`
2. **Publish (first)** → DOI v1 → `202`
3. **Update metadata** – PUT `/deposit/depositions/{id}` → `200`
4. **Publish again** (metadata-only) → same DOI v1 → `202`
5. **Upload file** – POST `/deposit/depositions/{id}/files` → `201`
6. **Publish after file change** → new DOI v2 → `202`
7. **List versions** – GET `/records/{conceptrecid}/versions` → `200`
8. **Get deposition** – GET `/deposit/depositions/{id}` → `200`
9. **List depositions** – GET `/deposit/depositions` → `200`
10. **Delete deposition** – DELETE `/deposit/depositions/{id}` → `204`

The environment automatically resolves the test file path without manual configuration.