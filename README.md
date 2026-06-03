# Restaurant Site

This repo is the working copy for the website currently hosted on pair.com.

## Current setup

- `public/` contains files that can be uploaded to static hosting.
- `public/restaurants.html` is a first-pass page for new and upcoming restaurants by city.
- `public/data/restaurants.json` is the data source used by the page.

The first version is intentionally static-hosting friendly: the site reads a JSON file in the browser, so it can work on ordinary pair.com web hosting without a custom backend.

## Importing the existing pair.com site

1. Download the current site files from pair.com using SFTP, SSH, FTP, or the pair.com file manager.
2. Put those files in `public/`.
3. If pair.com already has an `index.html`, replace the starter `public/index.html` with the real one.
4. Commit the imported files:

   ```bash
   git add .
   git commit -m "Import current website"
   ```

## Publishing from this repo

After editing locally, upload the contents of `public/` to the web root on pair.com. The web root is commonly named something like `public_html`, `www`, `htdocs`, or a domain-specific folder.

## Restaurant updates plan

The restaurant page should be driven by published sources rather than copied article text.

Current first version:

- Track only San Francisco, Vienna, and Munich.
- Store items in `public/data/restaurants.json`.
- Show each item with restaurant name, city, neighborhood, signal type, signal date, source name, source URL, and short original notes.
- Treat new openings, new Michelin recognition, chef-led moves, and pop-up-to-permanent moves as strong signals.
- Treat Tripadvisor-style popularity as a weak signal because it tends to reward already-visible places.
- Refresh the JSON manually at first.

Later automation options:

- Add a small script that reads RSS feeds from selected publications and updates `restaurants.json`.
- Run that script on a schedule from your computer, GitHub Actions, or pair.com cron if available.
- Keep source links visible so readers can verify the information.

## Restaurant review workflow

The review workflow is local-first. It does not publish automatically.

1. Scan source pages:

   ```bash
   python3 tools/scan_restaurant_sources.py --weeks 12
   ```

2. Start a local server from the repo root:

   ```bash
   python3 -m http.server 8080
   ```

3. Open the local review page:

   ```text
   http://localhost:8080/admin/restaurants.html
   ```

4. Approve, reject, or edit candidates, then download `approved-candidates.json`.
5. Move the downloaded file to `data-work/approved-candidates.json`.
6. Merge approved candidates into the public data file:

   ```bash
   python3 tools/merge_restaurant_candidates.py
   ```

7. Preview `public/restaurants.html`, then commit, push, and upload reviewed files.

### Manual sources

Some high-quality sources block automated fetching. Falstaff is currently treated
as a manual source.

When the scanner prints a manual source, it also writes targeted search URLs to
`data-work/candidates.json` under `manualSources[].searches`. Open those search
URLs in a browser and look for events in the same lookback window:

- New opening
- Michelin star or promotion
- Bib Gourmand or Green Star
- Chef-led move
- Pop-up becoming permanent
- Expansion or larger location

For each useful event, add a candidate with:

```bash
python3 tools/make_manual_candidate.py \
  --city Munich \
  --name "Restaurant Name" \
  --neighborhood "Neighborhood" \
  --event-type "New opening" \
  --url "https://www.falstaff.com/en/example" \
  --summary "Short original summary based on the source." \
  --why "Short editorial note explaining why this is upward momentum."
```

The helper appends to `data-work/approved-candidates.json`. You can override
scores with `--momentum`, `--discovery`, or `--confidence` when needed.

The generated candidate uses this shape:

```json
{
  "id": "munich-falstaff-example",
  "status": "approved",
  "name": "Restaurant Name",
  "city": "Munich",
  "neighborhood": "Neighborhood",
  "summary": "Short original summary based on the source.",
  "whyItMatters": "Short editorial note explaining why this is upward momentum.",
  "event": {
    "type": "New opening",
    "date": "2026-06-02",
    "sourceName": "Falstaff",
    "url": "https://www.falstaff.com/en/example",
    "momentum": 4,
    "discovery": 3,
    "confidence": 4,
    "note": "Short note about the source event."
  }
}
```

Scoring guide:

- `momentum`: 5 for Michelin promotion/new star, 4 for serious chef-led opening, 3 for interesting local opening.
- `discovery`: 5 for pop-up/soft opening/under-the-radar, 3 for known publication coverage, 1-2 for already-famous restaurants.
- `confidence`: 5 for Michelin, 4 for Falstaff/Eater/Infatuation, 3 for local press, 1-2 for weak aggregators.

## Local preview

For a simple preview, open `public/index.html` in a browser. If browser security blocks loading `public/data/restaurants.json`, run a local server from the repo root:

```bash
python3 -m http.server 8080 --directory public
```

Then open `http://localhost:8080`.
