# AgentDiode VS Code companion

This optional extension sends privacy-safe workspace lifecycle events to the
local AgentDiode socket. It never reads prompts, chat history, source files, or
generated code.

Reliability is currently **partial**. The installed VS Code release does not
provide a stable public API for observing all GitHub Copilot agent lifecycle
events. Therefore the extension provides explicit commands that can also be
called by other extensions:

- `AgentDiode: Start Agent Session`
- `AgentDiode: Complete Agent Session`
- `AgentDiode: Fail Agent Session`

It sends heartbeats while a manually started session is active. DOM scraping is
not used.

Development:

```bash
npm install
npm run check
npm run compile
```
