# API Key Runtime-Only Handling — ATL-4C / ATL-5

## Hard Rules

1. **Never** create a `.env` file in this project.
2. **Never** write a real `CASTFORM_API_KEY` into this repository (no markdown, no JSON, no JSONL, no HTML, no Python source).
3. **Never** paste a real `CASTFORM_API_KEY` into Telegram, Discord, or any messaging platform.
4. **Never** log a real `CASTFORM_API_KEY` to stdout / stderr / file output of any script in this project.
5. **Never** commit a file that contains a real `CASTFORM_API_KEY`.
6. The only allowed representation in the repo is the literal placeholder string `<CASTFORM_API_KEY>`.
7. ATL-4C does **not** need an API key — this phase is guarded preflight only.
8. ATL-5 may need an API key, but only if the user explicitly authorizes a real cloud smoke run.

## Allowed Runtime Injection Path (ATL-5 only, not now)

If and only if the user has explicitly authorized a real launch (i.e. all pre-launch gates in `FINAL_LAUNCH_GATE.md` are green), the **only** approved way to inject a real key is:

```bash
# User runs this manually in their own shell.
# The key never touches a file, never touches git, never touches markdown.
read -s CASTFORM_API_KEY
export CASTFORM_API_KEY
```

Why `read -s` instead of `export CASTFORM_API_KEY="..."`:

- `read -s` hides the input from the terminal (no echo).
- `read -s` prevents the key from appearing in shell history (unlike `export KEY="value"` which is logged to `~/.bash_history`).
- The key exists only in the current shell process's memory.
- When the shell exits, the key is gone (unless the user explicitly saves it somewhere, which is their responsibility and outside the scope of this project).

## What the Scripts Do With the Key

- `guarded_upload_preflight.py` reads `CASTFORM_API_KEY` from `os.environ`.
- `guarded_launch_preflight.py` reads `CASTFORM_API_KEY` from `os.environ`.
- Neither script writes the key to disk, telemetry, or stdout in cleartext.
- Both scripts mask the key in any log line (print only first 4 chars + `...`).
- Both scripts refuse to start if the key is empty or contains whitespace.

## Forbidden Patterns (validators will scan for these)

The following patterns are FORBIDDEN inside `guarded-cloud-preflight/`:

- Real key shapes assigned to `CASTFORM_API_KEY`, `castform_api_key`, `api_key`, `token`, `secret`, `password`.
- `.env` filenames anywhere in the case directory.
- `Bearer <opaque-token>` strings.
- Base64 blobs longer than 64 chars assigned to key-like variable names.
- Strings matching the regex `sk-[A-Za-z0-9]{20,}` or `cf-[A-Za-z0-9]{20,}` (Castform key heuristics).

The validator (`scripts/validate_atl4c_guarded_preflight.py`) implements a deny-list scan and will FAIL the phase if it finds any of these patterns in `guarded-cloud-preflight/`.

## Current Phase Status

- ATL-4C: no API key in repo, no API key created, no API key authorized.
- Any real launch is gated on user-supplied explicit authorization and the pre-launch gates in `FINAL_LAUNCH_GATE.md`.
- ATL-5 is the only phase that may use a real `CASTFORM_API_KEY`, and only via the `read -s` + `export` path described above.
