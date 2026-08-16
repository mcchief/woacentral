# WoA Permanent Data Architecture

## Why this fixes the loading problem

The browser no longer fetches 10 Google Sheets directly.

Instead:

Google Sheets -> GitHub Action -> validated data.json -> GitHub Pages dashboard

The GitHub Action runs every 5 minutes. It retries each Google source up to six times.
It writes data.json only after every required source succeeds, so a failed refresh cannot
replace the last complete snapshot with partial data.

The dashboard makes one same-origin request to ./data.json. This removes the browser
CORS/redirect/rate-limit problem that caused the strict centraltest versions to fail.

## Deploy to centraltest

Copy these items to the root of mcchief/centraltest:

- index.html
- data.json
- scripts/refresh_woa_data.py
- .github/workflows/refresh-data.yml

Then enable GitHub Actions "Read and write permissions" if repository policy blocks the
workflow from committing data.json.

The included data.json is seeded from the uploaded WOA_MASTER_WORKBOOK_LIVE workbook, so
the dashboard can load immediately after deployment. The scheduled workflow then keeps
the snapshot synchronized from the published Google Sheets.

## Data integrity

If one Google source fails during a scheduled refresh, the workflow fails and DOES NOT
overwrite data.json. Members continue to receive the last complete validated dataset.

No Player Status History source is required.
