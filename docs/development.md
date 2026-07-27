# Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,tray]'
./scripts/run-tests.sh
```

VS Code companion:

```bash
cd integrations/vscode-agentdiode
npm install
npm run check
npm run compile
```

Manual KDE verification:

1. Start `agentdiode daemon`.
2. Start `agentdiode-tray`.
3. Emit two sessions with `agentdiode emit`.
4. Verify state priority, animation, tooltip, session actions and details.
5. Complete one session and verify temporary green behavior.
6. Run a generic command with success and failure exit codes.
7. Restart the daemon and verify prior active sessions become stale.
8. Suspend/resume and confirm timestamp-derived durations.

Installer packaging test without service mutation:

```bash
./install.sh --no-start
./uninstall.sh --keep-data --no-services
```
