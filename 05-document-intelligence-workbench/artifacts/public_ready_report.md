# Public-Ready Report Artifact

- generated_at_utc: `2026-05-05T19:42:28.304040+00:00`

## Validation Summary
- pytest: `pass`
- public release packaging: `pass`
- provider live-check artifact: `fail`
- provider live-check overall status: `fail`

## Screenshot Assets
- `examples/workbench-dashboard.png`: `present`
- `examples/workbench-review-table.png`: `present`
- `examples/workbench-export.png`: `present`

## Artifacts
- provider output: `artifacts/provider_live_check_output.json` (`present`)
- docker proof output: `artifacts/docker_proof_output.txt` (`present`)

## Command Outputs
### pytest
```text
...........                                                              [100%]
```

### prepare_public_release
```text
Public release artifact ready: /private/tmp/document-intelligence-workbench-public
Files included: 70
```

### provider_live_checks
```text
Provider live-check artifact written: /Users/manjunathhanmantgad/Desktop/mj-projects-new/05-document-intelligence-workbench/artifacts/provider_live_check_output.json
```

### provider_live_check_failures
- openai_mode: openai_mode -> OPENAI_API_KEY is required for openai mode
- azure_mode: azure_mode -> Missing Azure OpenAI configuration: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT
