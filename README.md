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

## Local preview

For a simple preview, open `public/index.html` in a browser. If browser security blocks loading `public/data/restaurants.json`, run a local server from the repo root:

```bash
python3 -m http.server 8080 --directory public
```

Then open `http://localhost:8080`.
