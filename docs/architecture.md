# Architecture

AgentDiode uses separate daemon, tray and CLI processes. Integrations normalize
events into protocol version 1 and send JSON Lines over a mode `0600` Unix
socket inside a mode `0700` runtime directory.

The daemon validates input, tracks each session independently, aggregates state,
persists operational metadata in SQLite WAL mode, detects stale or PID-reused
sessions, and emits deduplicated desktop notifications. It never depends on the
tray process.

The PySide6 tray polls the local snapshot every 1.5 seconds, swaps cached-style
procedural LED icons on a 650 ms timer only for animated states, and exposes
native menus and dialogs. It continues to communicate locally with no network
service.

Codex hooks are the strongest verified integration on the development machine.
Generic wrapping reliably detects process start and exit. Other integrations
report their capability and reliability without inventing state.
