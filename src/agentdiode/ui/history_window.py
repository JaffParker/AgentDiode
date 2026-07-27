from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class HistoryWindow(QDialog):
    def __init__(self, rows: list[dict[str, Any]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AgentDiode History")
        self.resize(820, 420)
        layout = QVBoxLayout(self)
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search"))
        search = QLineEdit()
        search.setPlaceholderText("Agent, project, state…")
        search_row.addWidget(search)
        layout.addLayout(search_row)
        headings = ["Agent", "Project", "State", "Started", "Completed", "Reliability"]
        model = QStandardItemModel(0, len(headings), self)
        model.setHorizontalHeaderLabels(headings)
        for row in rows:
            values = [
                row.get("agent_name", ""),
                row.get("project_name", ""),
                row.get("state", ""),
                row.get("started_at", ""),
                row.get("completed_at") or "",
                row.get("reliability", ""),
            ]
            model.appendRow([QStandardItem(str(value)) for value in values])
        proxy = QSortFilterProxyModel(self)
        proxy.setSourceModel(model)
        proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxy.setFilterKeyColumn(-1)
        search.textChanged.connect(proxy.setFilterFixedString)
        table = QTableView()
        table.setModel(proxy)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
