# Naukri Profile Updater

## Run locally

This project requires Python 3.12 or newer and uses `uv` for dependency
management.

```bash
uv sync
NAUKRI_EMAIL="your-email" \
NAUKRI_PASSWORD="your-password" \
uv run python -m jobapplier.app.scheduled_profile_update
```

The scheduled job logs in to Naukri, toggles the trailing period in the
resume headline, and closes the HTTP client when it finishes.

When the FastAPI app is running, the same action is available through
`POST /profile/naukri/toggle-headline`. The web page served at `/` includes a
button for invoking this endpoint and displays the result.

## Run every three hours with GitHub Actions

The workflow in `.github/workflows/update-profile.yml` runs at minute `00`
of every third hour using UTC time. GitHub Actions schedules are approximate,
so a run may start a few minutes late.

Add these repository secrets under **Settings → Secrets and variables →
Actions**:

- `NAUKRI_EMAIL`
- `NAUKRI_PASSWORD`

The workflow can also be started manually from the **Actions** tab using
**Run workflow**.

Do not commit a `.env` file or Naukri credentials to the repository. Scheduled
workflows run only from the repository's default branch.