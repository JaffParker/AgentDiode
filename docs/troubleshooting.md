# Troubleshooting

Run:

```bash
agentdiode doctor
systemctl --user status agentdiode-daemon.service
systemctl --user status agentdiode-tray.service
agentdiode logs
```

If the CLI says the daemon is unavailable:

```bash
systemctl --user restart agentdiode-daemon.service
```

If Codex events do not appear, start a new Codex session, run `/hooks`, inspect
the AgentDiode entries and trust their current definitions. Codex hashes hook
definitions, so a changed callback path requires another review.

Wayland can prevent focusing an existing terminal/editor window. Opening a
project directory remains reliable.

Invalid configuration is reported rather than replaced. Move the invalid file
temporarily or correct the named value:

```text
~/.config/agentdiode/config.toml
```
