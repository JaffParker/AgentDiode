import * as crypto from "crypto";
import * as net from "net";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";

type State = "running" | "completed" | "error" | "heartbeat";

let activeSession: string | undefined;
let heartbeat: NodeJS.Timeout | undefined;

function socketPath(): string {
  if (process.env.AGENTDIODE_SOCKET) {
    return process.env.AGENTDIODE_SOCKET;
  }
  const uid = typeof process.getuid === "function" ? process.getuid() : 0;
  const runtime = process.env.XDG_RUNTIME_DIR ?? `/run/user/${uid}`;
  return path.join(runtime, "agentdiode", "agentdiode.sock");
}

function workspace(): { cwd: string; name: string } {
  const folder = vscode.workspace.workspaceFolders?.[0];
  return {
    cwd: folder?.uri.fsPath ?? os.homedir(),
    name: folder?.name ?? "VS Code",
  };
}

function emit(state: State, sessionId: string): Promise<void> {
  const current = workspace();
  const eventName = state === "heartbeat" ? "session.heartbeat" : `session.${state}`;
  const request = {
    command: "event",
    payload: {
      protocol_version: 1,
      event: eventName,
      timestamp: new Date().toISOString(),
      agent_id: "vscode",
      agent_name: "VS Code Agent",
      session_id: sessionId,
      cwd: current.cwd,
      reliability: "partial",
      pid: process.pid,
      editor: "vscode",
      source: "vscode-agentdiode-extension",
      metadata: { workspace_name: current.name },
    },
  };
  return new Promise((resolve, reject) => {
    const client = net.createConnection(socketPath());
    client.setTimeout(1500);
    client.on("connect", () => client.write(`${JSON.stringify(request)}\n`));
    client.on("data", () => {
      client.end();
      resolve();
    });
    client.on("timeout", () => client.destroy(new Error("AgentDiode socket timed out")));
    client.on("error", reject);
  });
}

async function start(): Promise<void> {
  activeSession = `vscode-${crypto.randomUUID()}`;
  await emit("running", activeSession);
  const seconds = vscode.workspace
    .getConfiguration("agentdiode")
    .get<number>("heartbeatSeconds", 30);
  heartbeat = setInterval(() => {
    if (activeSession) {
      void emit("heartbeat", activeSession);
    }
  }, seconds * 1000);
  void vscode.window.showInformationMessage("AgentDiode session started.");
}

async function finish(state: "completed" | "error"): Promise<void> {
  if (!activeSession) {
    void vscode.window.showWarningMessage("AgentDiode has no active VS Code session.");
    return;
  }
  await emit(state, activeSession);
  activeSession = undefined;
  if (heartbeat) {
    clearInterval(heartbeat);
    heartbeat = undefined;
  }
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("agentdiode.startSession", start),
    vscode.commands.registerCommand("agentdiode.completeSession", () => finish("completed")),
    vscode.commands.registerCommand("agentdiode.failSession", () => finish("error")),
    vscode.commands.registerCommand("agentdiode.showStatus", () =>
      vscode.window.showInformationMessage(
        "AgentDiode: partial reliability. VS Code exposes no stable public Copilot agent lifecycle API."
      )
    )
  );
}

export function deactivate(): void {
  if (heartbeat) {
    clearInterval(heartbeat);
  }
}
