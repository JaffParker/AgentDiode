from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from agentdiode import __version__
from agentdiode.config import config_path, set_value
from agentdiode.config import load as load_config
from agentdiode.constants import STATES
from agentdiode.daemon.server import main as daemon_main
from agentdiode.diagnostics.doctor import format_checks, run_checks
from agentdiode.integrations.antigravity.hook_patcher import (
    install as install_antigravity_hooks,
)
from agentdiode.integrations.antigravity.hook_patcher import (
    remove as remove_antigravity_hooks,
)
from agentdiode.integrations.codex.config_patcher import PatchResult as CodexPatchResult
from agentdiode.integrations.codex.config_patcher import install as install_codex_hooks
from agentdiode.integrations.codex.config_patcher import remove as remove_codex_hooks
from agentdiode.integrations.codex.detector import detect as detect_codex
from agentdiode.integrations.json_hook_patcher import PatchResult as JsonPatchResult
from agentdiode.integrations.json_hook_patcher import install as install_json_hooks
from agentdiode.integrations.json_hook_patcher import remove as remove_json_hooks
from agentdiode.models import now_iso
from agentdiode.paths import socket_path, state_dir
from agentdiode.protocol import Event, ProtocolError
from agentdiode.storage.exports import export_csv, export_json


async def request(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        reader, writer = await asyncio.open_unix_connection(socket_path())
    except (FileNotFoundError, ConnectionRefusedError) as exc:
        raise RuntimeError("AgentDiode daemon is unavailable; run `agentdiode daemon`") from exc
    writer.write(json.dumps(payload).encode() + b"\n")
    await writer.drain()
    raw_response = json.loads(await reader.readline())
    writer.close()
    await writer.wait_closed()
    if not isinstance(raw_response, dict):
        raise TypeError("daemon returned an invalid response")
    if not raw_response.get("ok"):
        raise RuntimeError(raw_response.get("error", "daemon request failed"))
    return raw_response


def print_snapshot(data: dict[str, Any]) -> None:
    print(f"Overall: {str(data['overall_state']).upper()}")
    if data["sessions"]:
        print()
    for item in data["sessions"]:
        print(
            f"{item['agent_name']:<10} {item['state']:<20} "
            f"{item['project_name'] or '-':<18} {item['duration_seconds']}s"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentdiode")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("sessions")
    history = sub.add_parser("history")
    history.add_argument("--limit", type=int, default=100)
    history.add_argument("--export", type=Path)
    history.add_argument("--format", choices=["json", "csv"])
    sub.add_parser("doctor")
    logs = sub.add_parser("logs")
    logs.add_argument("--follow", action="store_true")
    logs.add_argument(
        "--component", choices=["daemon", "tray", "integrations", "errors"], default="daemon"
    )
    integrations = sub.add_parser("integrations")
    integration_sub = integrations.add_subparsers(dest="integration_command")
    setup = integration_sub.add_parser("setup")
    setup.add_argument("--codex", action="store_true")
    setup.add_argument("--claude", action="store_true")
    setup.add_argument("--antigravity", action="store_true")
    setup.add_argument("--hooks-file", type=Path, default=Path.home() / ".codex/hooks.json")
    setup.add_argument("--callback", type=Path)
    remove_integration = integration_sub.add_parser("remove")
    remove_integration.add_argument("agent", choices=["codex", "claude", "antigravity"])
    remove_integration.add_argument("--hooks-file", type=Path)
    config = sub.add_parser("config")
    config.add_argument("setting", nargs="?")
    config.add_argument("value", nargs="?")
    reset = sub.add_parser("reset")
    reset.add_argument("session")
    emit = sub.add_parser("emit")
    emit.add_argument("--agent", required=True)
    emit.add_argument("--session", required=True)
    emit.add_argument("--state", required=True, choices=sorted(STATES - {"stale", "unknown"}))
    emit.add_argument("--cwd", default="")
    emit.add_argument("--name")
    emit.add_argument("--reliability", choices=["exact", "partial", "heuristic"], default="partial")
    emit.add_argument("--pid", type=int)
    emit.add_argument("--source", default="manual")
    emit.add_argument("--error-message")
    run = sub.add_parser("run")
    run.add_argument("--agent", default="custom")
    run.add_argument("--name", default="Custom Agent")
    run.add_argument("program", nargs=argparse.REMAINDER)
    sub.add_parser("daemon")
    sub.add_parser("version")
    return parser


async def emit_event(event: Event) -> dict[str, Any]:
    event.validate()
    return await request({"command": "event", "payload": event.to_dict()})


async def run_wrapped(args: argparse.Namespace) -> int:
    program = args.program[1:] if args.program[:1] == ["--"] else args.program
    if not program:
        raise RuntimeError("no command provided after --")
    session = f"{args.agent}-{uuid.uuid4().hex}"
    base = {
        "agent_id": args.agent,
        "session_id": session,
        "cwd": str(Path.cwd()),
        "agent_name": args.name,
        "reliability": "partial",
        "source": "generic-wrapper",
    }
    await emit_event(Event(event="session.starting", pid=os.getpid(), **base))
    process = await asyncio.create_subprocess_exec(*program)
    await emit_event(Event(event="session.running", pid=process.pid, **base))
    try:
        code = await process.wait()
    except KeyboardInterrupt:
        process.terminate()
        code = await process.wait()
    state = "completed" if code == 0 else "error"
    error = None if code == 0 else f"Process exited with status {code}"
    await emit_event(Event(event=f"session.{state}", error_message=error, **base))
    return code


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "daemon":
        return daemon_main()
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "doctor":
        checks = run_checks()
        print(format_checks(checks))
        return 0 if all(item.ok for item in checks) else 1
    if args.command == "logs":
        target = state_dir() / "logs" / f"{args.component}.log"
        if not target.exists():
            print(f"agentdiode: log does not exist yet: {target}", file=sys.stderr)
            return 1
        with target.open(encoding="utf-8", errors="replace") as handle:
            if args.follow:
                handle.seek(0, os.SEEK_END)
                try:
                    while True:
                        line = handle.readline()
                        if line:
                            print(line, end="", flush=True)
                        else:
                            time.sleep(0.25)
                except KeyboardInterrupt:
                    return 0
            else:
                lines = handle.readlines()
                print("".join(lines[-200:]), end="")
        return 0
    if args.command == "integrations":
        if args.integration_command == "setup":
            selected = [args.codex, args.claude, args.antigravity]
            if sum(selected) != 1:
                raise SystemExit("agentdiode: select exactly one integration")
            integration = (
                "codex" if args.codex else "claude" if args.claude else "antigravity"
            )
            default_hooks = {
                "codex": Path.home() / ".codex/hooks.json",
                "claude": Path.home() / ".claude/settings.json",
                "antigravity": Path.home() / ".gemini/config/hooks.json",
            }
            hooks_file = args.hooks_file
            if hooks_file == Path.home() / ".codex/hooks.json" and integration != "codex":
                hooks_file = default_hooks[integration]
            callback = args.callback or (
                Path.home()
                / f".local/share/agentdiode/integrations/callbacks/{integration}-hook"
            )
            if not callback.is_file():
                print(f"agentdiode: callback not found: {callback}", file=sys.stderr)
                return 2
            if integration == "codex":
                result: CodexPatchResult | JsonPatchResult
                detection = detect_codex()
                if not detection.installed or not detection.hooks_supported:
                    print(
                        "Codex lifecycle hooks are unavailable in the installed version.",
                        file=sys.stderr,
                    )
                    return 2
                result = install_codex_hooks(hooks_file, str(callback.resolve()))
            elif integration == "antigravity":
                result = install_antigravity_hooks(hooks_file, str(callback.resolve()))
            else:
                events = (
                    "SessionStart",
                    "UserPromptSubmit",
                    "PreToolUse",
                    "PostToolUse",
                    "PostToolUseFailure",
                    "PermissionRequest",
                    "Notification",
                    "Stop",
                    "SessionEnd",
                )
                result = install_json_hooks(
                    hooks_file, str(callback.resolve()), events, integration
                )
            print(
                f"{'Updated' if result.changed else 'Already configured'} {result.path}"
            )
            if result.backup:
                print(f"Backup: {result.backup}")
            if integration == "codex":
                print("Open Codex and use `/hooks` to review and trust the AgentDiode hooks.")
            else:
                print(f"Restart {integration.title()} CLI to load AgentDiode hooks.")
            return 0
        if args.integration_command == "remove":
            default_hooks = {
                "codex": Path.home() / ".codex/hooks.json",
                "claude": Path.home() / ".claude/settings.json",
                "antigravity": Path.home() / ".gemini/config/hooks.json",
            }
            hooks_file = args.hooks_file or default_hooks[args.agent]
            if args.agent == "codex":
                result = remove_codex_hooks(hooks_file)
            elif args.agent == "antigravity":
                result = remove_antigravity_hooks(hooks_file)
            else:
                result = remove_json_hooks(hooks_file)
            print(f"{'Updated' if result.changed else 'No AgentDiode hooks in'} {result.path}")
            if result.backup:
                print(f"Backup: {result.backup}")
            return 0
        for item in run_checks()[6:10]:
            reliability = "partial" if item.ok else "unavailable"
            print(f"{item.name:<10} {'installed' if item.ok else 'not installed':<14} {reliability}")
        return 0
    if args.command == "config":
        if args.setting is None:
            print(json.dumps(asdict(load_config()), indent=2))
            print(f"\nPath: {config_path()}")
            return 0
        if args.value is None:
            print("agentdiode: a TOML value is required", file=sys.stderr)
            return 2
        try:
            set_value(config_path(), args.setting, args.value)
        except (OSError, TypeError, ValueError) as exc:
            print(f"agentdiode: {exc}", file=sys.stderr)
            return 2
        print(f"Updated {args.setting} in {config_path()}")
        return 0
    try:
        if args.command in {"status", "sessions"}:
            print_snapshot(asyncio.run(request({"command": "snapshot"})))
        elif args.command == "history":
            data = asyncio.run(request({"command": "history", "limit": args.limit}))
            if args.export:
                export_format = args.format or args.export.suffix.removeprefix(".").lower()
                if export_format == "json":
                    export_json(data["sessions"], args.export)
                elif export_format == "csv":
                    export_csv(data["sessions"], args.export)
                else:
                    raise RuntimeError("export format must be json or csv")
                print(f"Exported {len(data['sessions'])} sessions to {args.export}")
            else:
                print(json.dumps(data["sessions"], indent=2, ensure_ascii=False))
        elif args.command == "emit":
            event = Event(
                event=f"session.{args.state}", agent_id=args.agent, session_id=args.session,
                cwd=args.cwd, agent_name=args.name, reliability=args.reliability, pid=args.pid,
                source=args.source, error_message=args.error_message, timestamp=now_iso(),
            )
            asyncio.run(emit_event(event))
        elif args.command == "reset":
            asyncio.run(
                request(
                    {
                        "command": "event",
                        "payload": Event(
                            event="session.remove",
                            agent_id="manual",
                            session_id=args.session,
                        ).to_dict(),
                    }
                )
            )
        elif args.command == "run":
            return asyncio.run(run_wrapped(args))
    except (RuntimeError, ProtocolError, OSError, TypeError) as exc:
        print(f"agentdiode: {exc}", file=sys.stderr)
        return 2
    return 0
