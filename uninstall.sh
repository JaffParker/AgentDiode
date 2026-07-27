#!/usr/bin/env bash
set -euo pipefail

keep_data=true
restore_integrations=false
manage_services=true
for argument in "$@"; do
  case "$argument" in
    --keep-data) keep_data=true ;;
    --remove-data) keep_data=false ;;
    --restore-integrations) restore_integrations=true ;;
    --no-services) manage_services=false ;;
    *)
      printf 'Unknown option: %s\n' "$argument" >&2
      exit 2
      ;;
  esac
done

install_root="${XDG_DATA_HOME:-$HOME/.local/share}/agentdiode"
systemd_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agentdiode"
hooks_file="$HOME/.codex/hooks.json"

if "$restore_integrations" && [[ -x "$install_root/venv/bin/agentdiode" ]]; then
  "$install_root/venv/bin/agentdiode" integrations remove codex --hooks-file "$hooks_file"
  "$install_root/venv/bin/agentdiode" integrations remove claude
  "$install_root/venv/bin/agentdiode" integrations remove antigravity
fi

if "$manage_services"; then
  systemctl --user disable --now agentdiode-tray.service 2>/dev/null || true
  systemctl --user disable --now agentdiode-daemon.service 2>/dev/null || true
fi

for target in \
  "$HOME/.local/bin/agentdiode" \
  "$HOME/.local/bin/agentdiode-daemon" \
  "$HOME/.local/bin/agentdiode-tray" \
  "$systemd_dir/agentdiode-daemon.service" \
  "$systemd_dir/agentdiode-tray.service" \
  "${XDG_DATA_HOME:-$HOME/.local/share}/applications/io.agentdiode.AgentDiode.desktop" \
  "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps/io.agentdiode.AgentDiode.svg"
do
  if [[ -L "$target" || -f "$target" ]]; then
    rm -- "$target"
  fi
done

if [[ -d "$install_root" ]]; then
  rm -rf -- "$install_root"
fi
if "$manage_services"; then
  systemctl --user daemon-reload
fi

if ! "$keep_data" && [[ -d "$state_dir" ]]; then
  printf 'Delete AgentDiode history and logs in %s? [y/N] ' "$state_dir"
  read -r answer
  if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    rm -rf -- "$state_dir"
    printf '%s\n' "History and logs removed; this cannot be undone."
  fi
fi

printf '%s\n' "AgentDiode application files removed."
if "$keep_data"; then
  printf 'History preserved in %s\n' "$state_dir"
fi
