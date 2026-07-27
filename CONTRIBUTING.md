# Contributing to AgentDiode

Thank you for helping improve AgentDiode.

## Before opening an issue

- Run `agentdiode doctor`.
- Check existing issues.
- Remove prompts, source code, tokens and personal paths from logs.
- Include the AgentDiode version, Linux distribution, Plasma version, session
  type and relevant agent version.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,tray]'
./scripts/run-tests.sh
```

For VS Code extension changes:

```bash
cd integrations/vscode-agentdiode
npm install
npm run check
npm run compile
```

## Pull requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Preserve privacy-safe defaults.
- Never label heuristic behavior as exact.
- Do not introduce telemetry or a required remote service.
- Preserve unrelated user hooks and configuration.
- Update documentation when commands, configuration or integration behavior changes.

All Python checks and the TypeScript check must pass before review.
