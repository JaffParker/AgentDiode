# Privacy

AgentDiode is local-first and has no telemetry, cloud account, analytics upload,
or internet requirement at runtime.

Stored by default:

- agent and session identifiers;
- lifecycle state and reliability;
- working directory and derived project name;
- timestamps, duration and process identifiers;
- integration source and bounded safe metadata.

Not stored:

- prompts or assistant conversations;
- source or generated code;
- tool arguments and outputs;
- API keys, tokens, environment dumps or clipboard contents.

The Codex callback deliberately selects a small allowlist of metadata and does
not read the transcript path. Logs rotate and suppress messages containing
common credential markers.
