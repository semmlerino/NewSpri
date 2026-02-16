# Web UI Status

The web version is **not currently implemented in this repository**.

## Current State

- `web_backend/` is not present.
- `web_frontend/` does not contain application source (only dependency cache content).
- No runnable FastAPI/React web app is tracked here today.

## What This Means

- Desktop app (`sprite_viewer.py`) is the actively maintained product.
- Instructions for running a web backend/frontend from earlier iterations are obsolete.

## If Web Work Is Resumed

A minimal expected layout would be:

```
web_backend/
  main.py
  requirements.txt

web_frontend/
  package.json
  src/
  public/
```

Until those files are added, treat this repository as desktop-only.
