# Site Modernization Plan

This site contains a small number of hand-maintained pages and a large static
archive of photos, generated gallery pages, applets, and historical files. The
modernization work should improve the visible entry points without deleting or
renaming archived content.

## Phase 0: Preservation Guardrails

The baseline preservation manifest is:

```text
docs/public-preservation-manifest.json
```

It records every file under `public/` with path, size, and SHA-256 hash. Before
modernizing pages, verify the current tree against the baseline:

```bash
python3 tools/public_manifest.py check
```

Expected behavior during cleanup:

- Missing files are treated as blockers unless the deletion is intentional.
- Changed files under `public/ourphotos/`, `public/applets/`, and
  `public/index_files/` need extra review.
- New files are allowed; the checker reports them as extra but does not fail on
  extras.
- Regenerate the manifest only after intentional, reviewed changes:

  ```bash
  python3 tools/public_manifest.py write
  ```

## Preservation-Critical Areas

Do not rewrite, rename, or bulk-format these by default:

- `public/ourphotos/**/images/`
- `public/ourphotos/**/thumbnails/`
- generated gallery files such as `target*.html`, `caption.html`, and
  `imageset.html`
- `public/applets/`
- original homepage media under `public/index_files/`

## First Modernization Targets

Start with entry pages and archive indexes:

- `public/ourphotos/index.html`
- `public/ourphotos/2004_trip/index.html`
- `public/professional.html`
- `public/bookmarks.html`
- `public/index.html`

Keep existing album and file URLs working. Prefer adding modern landing pages
around the archive instead of replacing generated gallery internals.
