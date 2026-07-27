# Integrations

## Codex CLI

AgentDiode uses the official lifecycle hooks available in Codex CLI 0.145.0.
The detector checks the installed version and confirms that the `hooks` feature
exists before changing configuration.

Setup:

```bash
agentdiode integrations setup --codex
```

AgentDiode merges its entries into `~/.codex/hooks.json`, preserves unrelated
hooks, and creates a timestamped backup before any change. Repeating setup does
not duplicate entries. Codex requires non-managed hooks to be reviewed:

1. Start a new Codex CLI session.
2. Run `/hooks`.
3. Review the AgentDiode callback path and trust the hooks.

Events:

| Codex hook | AgentDiode state |
|---|---|
| `SessionStart` | `starting` |
| `UserPromptSubmit` | `running` |
| `PreToolUse`, `PostToolUse` | `running` |
| `PermissionRequest` | `waiting_approval` |
| `Stop` | `completed` |
| `SessionEnd` | `idle` |

Reliability is `partial`. These mappings use official lifecycle events, but the
installed Codex version has no dedicated hook that identifies every case where
the agent is waiting for a user answer.

Remove only AgentDiode entries:

```bash
agentdiode integrations remove codex
```

The callback stores no prompt, tool arguments, transcript, source content, or
assistant message. It forwards only lifecycle identifiers, working directory,
model slug, permission mode, and timestamps over the local user socket.

## Claude Code

Claude Code uses its official JSON settings hooks:

```bash
agentdiode integrations setup --claude
```

AgentDiode merges lifecycle handlers into `~/.claude/settings.json`, preserves
unrelated settings and hooks, and writes a timestamped backup before changes.
The callback maps session, prompt, tool, permission, notification and stop
events without retaining prompts, transcripts or tool input.

The integration can be configured and contract-tested without a paid Claude
account. A real model turn requires an eligible Claude subscription, Anthropic
API billing, or a supported cloud provider.

## Antigravity and Gemini CLI

For individual Google accounts, AgentDiode targets Antigravity CLI:

```bash
agentdiode integrations setup --antigravity
```

AgentDiode adds a named hook to `~/.gemini/config/hooks.json`, preserving other
named hooks. It observes `PreInvocation`, `PostInvocation`, `PreToolUse`,
`PostToolUse`, and `Stop`. Antigravity's current hook API does not provide a
dedicated event for permission prompts, so that state is not claimed.

The legacy open-source Gemini CLI remains relevant for enterprise and API-key
users, but it is a separate integration target and is not currently configured
by `--antigravity`. AgentDiode identifies the runtime honestly and does not
claim that an inferred event is exact.

## VS Code and GitHub Copilot

The optional companion is in `integrations/vscode-agentdiode`. It reports
`partial` reliability because the installed VS Code release exposes no stable
public API covering every Copilot agent lifecycle transition. The extension
provides explicit lifecycle commands and heartbeats without inspecting prompts,
chat history, source files, generated code, or VS Code's DOM.
