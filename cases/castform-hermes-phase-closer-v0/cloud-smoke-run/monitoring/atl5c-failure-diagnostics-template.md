# ATL-5C — Failure Diagnostics Template

**Date**: 2026-06-13
**Phase**: ATL-5C (failure-diagnostics scaffold)
**Status**: template — fill in below after each diagnostic step

This template is a **structured checklist** for capturing failure diagnostics for the first Castform training run. It does NOT contain any actual diagnostics yet — it is a scaffold. Fill in each field from the read-only SDK/API status probe output (or from the Castform UI screenshot you take locally).

---

## Run identity

| Field | Value |
|-------|-------|
| `run_id` | `c83f971d-2b2c-42b8-9774-ca64938c1286` |
| actual UI URL | `https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train` |
| display name | `simple-28de6dd2` |

## Status

| Field | Value |
|-------|-------|
| status | `<failed \| queued \| running \| completed \| cancelled \| unknown>` |
| step | `<integer — 0 means "before first rollout">` |
| failure reason visible in UI | `<yes \| no>` |
| UI-visible traceback | `<paste verbatim here, or "N/A">` |
| UI-visible worker log | `<paste verbatim here, or "N/A">` |

## Tabs

| Tab | Visible | Data Available | Rollouts Recorded | Notes |
|-----|---------|----------------|--------------------|-------|
| train | `<yes \| no>` | `<yes \| no>` | `<yes \| no>` | |
| train rollout deepdive | `<yes \| no>` | `<yes \| no>` | `<yes \| no>` | |
| eval | `<yes \| no>` | `<yes \| no>` | `<yes \| no>` | |
| eval rollout deepdive | `<yes \| no>` | `<yes \| no>` | `<yes \| no>` | |
| compare | `<yes \| no>` | external eval `<completed \| pending \| failed>`; your model `<rollouts yes \| no>` | — | |
| config | `<yes \| no>` | — | — | |
| settings | `<yes \| no>` | — | — | |

## Usage / credit (after first run)

| Field | Value |
|-------|-------|
| credit consumed (USD) | `<number or "unknown">` |
| credit remaining (USD) | `<number or "unknown">` |
| usage page visible | `<yes \| no>` |
| billing page visible | `<yes \| no>` |
| auto-charge state | `<on \| off \| unknown>` |
| inference cost (per request) shown | `<number or "unknown">` |

## Failure clues (paste read-only SDK/API probe output here, sanitized)

```
<paste the read-only probe output (run by user locally) here, removing any
 prefix / fragment / Authorization header / cookie / card number / email>
```

### Probe output highlights

- `NO_READ_ONLY_STATUS_METHOD_FOUND` printed? `<yes \| no>`
- If yes: jump to **ATL-5E — support-ready failure bundle**
- If no: continue to **ATL-5D — failure root cause record** with the captured method name and response

## Backend error (if surfaced by probe)

```
<paste the error response here, sanitized>
```

## Final diagnostic status (pick one)

- `ROOT_CAUSE_IDENTIFIED` — probe + UI together produced a clear backend error
- `BACKEND_SILENT_FAILED` — UI says `failed` but no traceback / log / API response with root cause
- `NO_READ_ONLY_METHOD` — `benchmax.platform.client.TrainerClient` has no candidate `get_*` / `list_*` / `status_*` method
- `OTHER` — describe

## Hard-rule compliance (check after fill-in)

- [ ] no `CASTFORM_API_KEY` value or fragment anywhere in the filled-in template
- [ ] no Authorization header / cookie / card number / user email pasted
- [ ] no `cf_<...>` prefix or `sk-<...>` key fragment in any field
- [ ] all values are from local user observation (UI screenshot / probe stdout), not invented
- [ ] if a UI-visible traceback was pasted, only sanitized versions of the values appear

## Next-step branch

- After filling in this template, branch to either:
  - **ATL-5D — failure root cause record** (if `ROOT_CAUSE_IDENTIFIED` or `BACKEND_SILENT_FAILED`)
  - **ATL-5E — support-ready failure bundle** (if `NO_READ_ONLY_METHOD`)
