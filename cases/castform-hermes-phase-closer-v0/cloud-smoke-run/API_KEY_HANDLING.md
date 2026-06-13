# API Key Handling — Castform Cloud Smoke Run (ATL-4B-CONFIG)

## Hard Rules

1. **Never** write a real `CASTFORM_API_KEY` into this repository.
2. **Never** create a `.env` file in this project.
3. **Never** paste a real `CASTFORM_API_KEY` into a markdown file, JSON config, JSONL sample, or HTML page.
4. **Never** send a real `CASTFORM_API_KEY` to Telegram, Discord, or any messaging platform.
5. **Never** log a real `CASTFORM_API_KEY` to stdout / stderr / file output of any script in this project.
6. The only allowed representation in the repo is the literal placeholder string `<CASTFORM_API_KEY>`.
7. If any script in this project detects what looks like a real key (e.g. a long opaque token assigned to a `CASTFORM_API_KEY` variable), it must **refuse to continue** and exit non-zero.
8. ATL-4B-CONFIG itself does **not** need an API key — this phase is dry configuration only.

## Allowed Real-Run Injection Path (future, not now)

If and only if the user has explicitly authorized a real launch (i.e. all pre-launch gates in `README.md` are green), the **only** approved way to inject a real key is:

```bash
# User runs this manually in their own shell, in the same terminal that will run the launch.
# The key never touches a file, never touches git, never touches markdown.
export CASTFORM_API_KEY="<redacted-at-source>"
```

The `cloud_launch_guard.py` script reads the key from the process environment only — never from a file in this repo. Even when the guard is flipped to `ALLOWED`, the script must:

- Refuse to start if the key is empty.
- Refuse to start if the key contains any whitespace or quote characters.
- Mask the key in any log line (print only first 4 chars + `...`).
- Not write the key to disk, telemetry, or stdout in cleartext.

## Forbidden Patterns (validator will scan for these)

The following patterns are FORBIDDEN inside `cloud-smoke-run/`:

- Real key shapes assigned to `CASTFORM_API_KEY`, `castform_api_key`, `api_key`, `token`, `secret`, `password`.
- `.env` filenames anywhere in the case directory.
- `Bearer <opaque-token>` strings.
- Base64 blobs longer than 64 chars assigned to key-like variable names.
- Strings matching the regex `sk-[A-Za-z0-9]{20,}` or `cf-[A-Za-z0-9]{20,}` (Castform key heuristics — these are placeholders; real keys may have other shapes, but if anything looks key-like the script refuses).

The validator (`scripts/validate_atl4b_cloud_smoke_config.py`) implements a deny-list scan and will FAIL the phase if it finds any of these patterns in `cloud-smoke-run/`.

## Current Phase Status

- ATL-4B-CONFIG: no API key in repo, no API key created, no API key authorized.
- Any real launch is gated on user-supplied explicit authorization and the pre-launch gates in `README.md`.
