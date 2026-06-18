# OpenClaw Tool Use Discipline — LLM Distillation Response

The model analyzed the SKILL.md and produced the following Gene JSON:

```json
{
  "type": "Gene",
  "id": "gene_distilled_openclaw-tool-use-discipline",
  "category": "optimize",
  "signals_match": [
    "tool_bypass:exec-on-grep",
    "repeated_tool_usage:exec",
    "protocol_drift:wrong-tool-for-file-read",
    "session_context:openclaw",
    "repo_context:ai-tool-test-lab"
  ],
  "preconditions": [
    "session_context is openclaw",
    "tool audit ratio exec/(read+search+edit+write) > 0.5 in last 20 calls"
  ],
  "strategy": [
    "Read files with the read tool before referencing their content in reasoning.",
    "Use the edit tool for in-place file changes; never use sed -i or awk -i inplace.",
    "Use the search tool for repo-wide content search before falling back to rg via exec.",
    "Prefix every non-validator exec invocation with a one-line EXEC: <reason> in reasoning.",
    "Re-run validators after each substantive change."
  ],
  "constraints": {
    "max_files": 12,
    "forbidden_paths": [".git", "node_modules", ".evolver", "memory"]
  },
  "validation": [
    "python3 scripts/validate_evomap_phase3a_skill_distillation.py",
    "secret-pattern scan via the validator",
    "git status --short must list only expected case files"
  ]
}
```
