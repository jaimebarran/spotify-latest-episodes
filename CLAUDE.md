# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script Python job that keeps one Spotify playlist ("Noticias del día") in sync with the
latest episode of a list of Spanish news podcasts. It runs unattended via cron on this machine.

Code comments and print output are in Spanish; keep that convention when editing [main.py](main.py).

## Commands

```bash
# Run locally against the venv (Python 3.12)
.venv/bin/python main.py

# Run the way cron does: containerised, .env injected, repo bind-mounted at /app
./main.sh

# Install/refresh deps
.venv/bin/pip install -r requirements.txt
```

There are no tests, linter, or build step. `main.sh` and `git_push.sh` use absolute paths
(`/home/debi/jaime/repos/spotify-latest-episodes/...`) — they are not portable to another checkout
location without editing.

## Execution pipeline

`crontab.sh` is a copy of the installed crontab (`*/20 6-11 * * *` — every 20 min, 6am–11am) and is
documentation only; editing it changes nothing until installed with `crontab`. It invokes:

1. **[main.sh](main.sh)** — `docker run` of `jaimebarran/spotify-latest-episodes:latest`, appending
   stdout/stderr to `status.log`. That image is published to Docker Hub manually; the
   [Dockerfile](Dockerfile) here (`pip install -r requirements.txt` on a devcontainer base) is its
   source, but nothing in the repo builds or pushes it. Changing `requirements.txt` therefore has no
   effect on the cron run until the image is rebuilt and pushed.
2. **[git_push.sh](git_push.sh)** — commits and pushes `status.log` to `main` when it changed. This
   is why the history is a long run of "Update status.log" commits.

Note the checksum logic in `main.sh` is subtly off: `NEW_SUM` is computed *before* the run, so it
compares the previous run's log against the checksum stored in `.status_prev_sum`. Don't "fix" it
casually — the effect is a one-cycle-delayed push, not a broken one.

`main.py` truncates `status.log` on startup, so the file only ever holds the most recent run.

## Auth

`SPOTIPY_CLIENT_ID` / `SPOTIPY_CLIENT_SECRET` / `SPOTIPY_REDIRECT_URI` come from `.env` (gitignored).
Spotipy's `SpotifyOAuth` caches the access + refresh token in `.cache` (also gitignored, bind-mounted
into the container as part of `/app`).

**Since 2026-07-20 Spotify expires refresh tokens after six months.** When that happens the refresh
returns `invalid_grant` and the only fix is a fresh browser sign-in — rotating the client secret does
not help. `build_spotify_client()` in [main.py](main.py) handles this: it validates the token up
front, discards `.cache` on `invalid_grant` (Spotify forbids retrying the refresh), then either
re-runs the browser flow if stdin is a TTY, or exits 1 with instructions if not. So under cron the
job fails fast and the error lands in `status.log` instead of hanging on a browser prompt.

Recovery is manual and must happen on a machine with a browser:

```bash
/home/debi/miniconda3/bin/python main.py   # opens browser, writes a new ./.cache
```

Expect to do this roughly every six months.

## Adding or muting podcasts

Edit [config.json](config.json). Each entry is a Spotify *show* ID; `"ignore": true` mutes an entry
without deleting it, and `load_config()` filters those out while preserving file order — playlist
order follows config order.

`get_recent_episodes_from_podcast()` retries with `limit=1`, then `2`, then `3` because some shows
return `null` items for episodes that are uploaded but not yet public. If a new podcast consistently
yields nothing, that ladder is the place to look.
