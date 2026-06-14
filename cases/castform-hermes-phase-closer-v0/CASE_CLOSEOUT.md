# Castform Hermes Phase Closer v0 — Case Closeout

## Final Status

PAUSED_PENDING_CASTFORM_BACKEND_LOGS

## What Was Tested

- Castform Web App access
- API key page access
- $50 free credit visibility
- Build your own / SDK path
- benchmax install and import
- real local validate_env
- upload_training_run
- launch_training_run
- Castform Web UI run monitoring

## Local Successes

- JSONL validation passed
- reward smoke passed
- benchmax import passed
- validate_env passed locally
- starter-style environment validate_env passed locally

## Cloud Successes

- ATL-5B upload succeeded
- ATL-5B launch succeeded
- ATL-6 upload succeeded
- ATL-6 launch succeeded
- two real Castform training runs were created

## Cloud Failure

Both real runs failed at step 0 before rollouts.

### Run 1
- run_id: c83f971d-2b2c-42b8-9774-ca64938c1286
- sample count: 8 train / 2 eval
- status: failed
- step: 0
- rollouts: none

### Run 2
- run_id: 56cb5701-6b3e-424e-b671-fc2efc932aa8
- sample count: 16 train / 4 eval
- status: failed
- step: 0
- rollouts: none

## Ruled Out or Reduced

- Missing API key
- Local validate_env failure
- upload failure
- launch failure
- unsupported batch_size
- train dataset under 16 examples
- run_tool raising in a no-tools environment
- reward not normalized

## Not Yet Ruled Out

- Castform remote worker bootstrap failure
- remote dataset loading failure
- remote env unpickle/import failure
- trainer backend internal error
- quota / runtime / account-level issue
- platform-side failure hidden from UI

## Final Decision

Stop further cloud attempts for now.
Do not run more upload / launch tests until Castform backend logs or support feedback are available.

## Optional Future Action

Send support request to Castform / Castie with both run IDs.

## Sensitive Information Exclusion

This case excludes:

- API key
- API key prefix
- credit card data
- cookie
- Authorization header
- user email
- screenshots with private account data

## Vendor Fix Update

Vendor response received.
Castform confirmed the issue was fixed.
Vendor-confirmed root cause: raw data dict caused trainer incompatibilities.
Castform added $100 extra credits.
Case can be resumed for retest.
New status: VENDOR_FIX_RECEIVED_RETEST_PENDING.

> Note: the historical closeout status `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` above remains
> preserved as audit trail. This update is appended in place and does not delete or overwrite
> any earlier conclusion. See `VENDOR_FIX_RESPONSE.md` for the full vendor response record.
