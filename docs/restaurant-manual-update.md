# Manual Restaurant Update Recipe

This file is for local/Git use only. It lives outside `public/`, so it is not part
of the website upload.

## When to use this

Use this when a valuable source is not automatically scanned, especially
Falstaff.

## Quick Flow

1. Run the scanner:

   ```bash
   cd /Users/borisratchev_hm/Documents/work/GitHub/restaurant-site
   python3 tools/scan_restaurant_sources.py --weeks 12
   ```

2. Open `data-work/candidates.json`.

3. Look at `manualSources`.

4. Open the search URLs listed under `manualSources[].searches`.

5. For each promising article, ask:

   - Is this a real event, not just a listicle?
   - Is it recent enough?
   - Is it about upward movement?
   - Is the restaurant name clear?

## Good Manual Events

- New opening
- New Michelin star
- Michelin promotion
- Bib Gourmand
- Green Star
- Chef-led move
- Pop-up becoming permanent
- Expansion to larger location
- Strong early demand from credible local reporting

## Usually Skip

- Generic best-of lists
- Old awards with no new event
- Tourist popularity rankings
- Roundups where nothing changed
- Articles where the restaurant name is unclear

## Add A Manual Candidate

Use the helper:

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

This appends to:

```text
data-work/approved-candidates.json
```

## Score Overrides

The helper uses defaults, but you can override:

```bash
--momentum 4 --discovery 3 --confidence 4
```

Scoring:

- `momentum`: How strong is the upward movement?
- `discovery`: How early or under-the-radar is it?
- `confidence`: How reliable is the source/event?

Typical values:

- Michelin promotion or new star: momentum 5, confidence 5
- Serious chef-led opening: momentum 4
- Pop-up or soft opening: discovery 5
- Falstaff/Eater/Infatuation: confidence 4
- Local press: confidence 3

## Merge Approved Candidates

After adding manual candidates:

```bash
python3 tools/merge_restaurant_candidates.py
```

Then preview:

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080/public/restaurants.html
```

## Publish

After review:

1. Commit in GitHub Desktop.
2. Push.
3. Upload changed public files to pair.com.

If only restaurant data changed:

```sftp
cd public_html
put public/data/restaurants.json data/restaurants.json
bye
```
