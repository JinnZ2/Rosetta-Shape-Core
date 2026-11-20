# traffic/

Weekly record of GitHub traffic (clones, views, referrers, paths) for every JinnZ2 repo. GitHub keeps traffic for 14 days only, so the history exists only here. CC0. Written by `scripts/traffic_pull.py` through `.github/workflows/traffic.yml`. Do not edit these files by hand.

```text
history_clones.csv     date, repo, count, uniques    (daily, from the API)
history_views.csv      date, repo, count, uniques    (daily, from the API)
history_referrers.csv  fetched, repo, name, count, uniques   (14-day top 10, one snapshot per run)
history_paths.csv      fetched, repo, name, count, uniques   (14-day top 10, one snapshot per run)
latest.md              last 14 days per repo, sorted by unique cloners; BOT? = clones > 0 and views = 0
```

**History is never deleted.**
- A (repo, date) row is kept even after it leaves GitHub's 14-day window.
- A later fetch can only raise a row's count. The day of a fetch is partial, and it fills in on the next run.
- Referrer and path snapshots are keyed by the fetch date.

**BOT? is a pattern, not a finding.** Clones with no page views usually means CI, mirrors, crawlers or scripted clones. It can also be a person who cloned without opening the web page.

## Token (one time, from a phone)

1. **Open the token page.** In a browser (the GitHub app has no token page), go to github.com, then Settings, then Developer settings, then Personal access tokens, then **Fine-grained tokens**, then **Generate new token**.
2. **Name it and set its scope.**
   - Name: `traffic-read`.
   - Expiration: your choice. A 1-year token means one renewal a year.
   - Resource owner: **JinnZ2**.
   - Repository access: **All repositories**.
3. **Set the permission.** Under Repository permissions, set **Administration: Read-only**. Leave everything else at **No access**; Metadata: Read-only is added automatically.
   - **Why Administration?** GitHub groups the traffic endpoints under that permission for fine-grained tokens. Read-only is enough; the token can view settings and traffic and cannot change anything.
   - **Not verified here.** That this is the minimum was stated from memory, because docs.github.com was not reachable from the session that wrote this. The first run checks it: if the token lacks the permission, every repo shows `403` under "Not read" in `latest.md`.
   - **Classic token alternative.** Scope `repo` also works, but it grants write access. Use the fine-grained token.
4. **Copy the token.** Generate it and copy the value.
5. **Store it as a secret.** Open this repository (Rosetta-Shape-Core), then Settings, then Secrets and variables, then Actions, then **New repository secret**. Name it `TRAFFIC_TOKEN` and paste the value.

The workflow's own `GITHUB_TOKEN` is used only to commit the files in `traffic/`. Its permission is `contents: write`, and only in this repository.

## Run

- **Automatic.** Weekly, on Monday at 10:23 UTC.
- **By hand.** From the GitHub app or a browser: open this repository, then **Actions**, then **traffic**, then **Run workflow**.
  - The workflow must be on the default branch before **Run workflow** appears.
  - In the mobile app, look under the repository's Actions tab. If the button is missing there, use a browser.
- **Locally.** `TRAFFIC_TOKEN=... python3 scripts/traffic_pull.py` writes the same files.
- **Selftest.** `python3 scripts/traffic_pull.py --selftest` runs with no network.

The first run has 14 days of history. Every run after that adds a week.
