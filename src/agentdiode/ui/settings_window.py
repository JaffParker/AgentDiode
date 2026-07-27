from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from agentdiode import AUTHOR, PROJECT_URL, __version__
from agentdiode.config import config_path, load, set_value


class SettingsWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AgentDiode Settings")
        self.setMinimumWidth(460)
        config = load()
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        general = QWidget()
        form = QFormLayout(general)
        self.stale = QSpinBox()
        self.stale.setRange(10, 86400)
        self.stale.setSuffix(" seconds")
        self.stale.setValue(config.general.stale_timeout_seconds)
        form.addRow("Stale timeout", self.stale)
        self.completed = QSpinBox()
        self.completed.setRange(0, 3600)
        self.completed.setSuffix(" seconds")
        self.completed.setValue(config.general.completed_display_seconds)
        form.addRow("Completed indicator", self.completed)
        self.notifications = QCheckBox("Enable desktop notifications")
        self.notifications.setChecked(config.notifications.enabled)
        form.addRow(self.notifications)
        self.blink = QCheckBox("Animate active states")
        self.blink.setChecked(config.tray.blink_running)
        form.addRow(self.blink)
        tabs.addTab(general, "General")
        privacy = QWidget()
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.addWidget(QLabel("Prompts, source code and generated code are not stored."))
        privacy_layout.addStretch()
        tabs.addTab(privacy, "Privacy")
        layout.addWidget(tabs)
        about = QLabel(
            f"<b>Version: {__version__}</b>"
            f'&nbsp;&nbsp;·&nbsp;&nbsp;<a href="{PROJECT_URL}">{AUTHOR}</a>'
        )
        about.setOpenExternalLinks(True)
        about.setToolTip(PROJECT_URL)
        layout.addWidget(about)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self) -> None:
        path = config_path()
        set_value(path, "general.stale_timeout_seconds", str(self.stale.value()))
        set_value(path, "general.completed_display_seconds", str(self.completed.value()))
        set_value(
            path, "notifications.enabled", str(self.notifications.isChecked()).lower()
        )
        set_value(path, "tray.blink_running", str(self.blink.isChecked()).lower())
        set_value(path, "tray.blink_waiting", str(self.blink.isChecked()).lower())
        self.accept()
