Hi, I'm testing Castform's Build your own / SDK workflow.

Final status: PAUSED_PENDING_CASTFORM_BACKEND_LOGS

Two minimal SDK training runs launched successfully but both failed at step 0 before any rollout was recorded.

Run 1:

- run_id: c83f971d-2b2c-42b8-9774-ca64938c1286
- actual UI route: /train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train
- status: failed
- step: 0
- train data: none
- eval data: none
- rollouts: none
- sample count: 8 train / 2 eval

Run 2:

- run_id: 56cb5701-6b3e-424e-b671-fc2efc932aa8
- actual UI route: /train/56cb5701-6b3e-424e-b671-fc2efc932aa8?tab=train
- status: failed
- step: 0
- train data: none
- rollouts: none
- sample count: 16 train / 4 eval

What worked:

- local validate_env passed
- upload_training_run succeeded
- launch_training_run succeeded
- model: Qwen/Qwen3.5-4B
- no tools
- second run used starter-style environment
- second run used 16 train / 4 eval examples
- run_tool returns an empty string
- reward is normalized to 0.0–1.0
- batch_size was removed from launcher_args

What failed:

- both runs failed at step 0
- no rollouts were recorded
- no visible worker logs or traceback appeared in the UI

Could you check backend logs for these run IDs and tell me the failure reason?

This request intentionally excludes API keys, cookies, authorization headers, credit card information, and screenshots with private account data.
