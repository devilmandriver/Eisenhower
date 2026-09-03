import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QCheckBox, QPushButton, QListWidget, QListWidgetItem, QDateEdit,
    QFrame, QMenu, QGraphicsDropShadowEffect, QGridLayout,
    QFileDialog, QDialog, QDialogButtonBox, QTextEdit,
)
from PySide6.QtCore import Qt, QRect, QDate, QTimer
from PySide6.QtGui import QFont, QColor, QAction, QPixmap, QIcon, QPainter, QBrush

if getattr(sys, "frozen", False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SAVE_FILE = os.path.join(_base_dir, "tasks.json")

QUADRANT_META = {
    "urgent_important":     {"title": "Do First",  "sub": "Urgent & Important",          "accent": "#F87171", "bg": "#FFF1F2"},
    "important_not_urgent": {"title": "Schedule",  "sub": "Important · Not Urgent",       "accent": "#52525B", "bg": "#2A2A2A"},
    "urgent_not_important": {"title": "Delegate",  "sub": "Urgent · Not Important",       "accent": "#FB923C", "bg": "#FFF7ED"},
    "neither":              {"title": "Eliminate", "sub": "Not Urgent · Not Important",   "accent": "#A78BFA", "bg": "#F5F3FF"},
}


def make_app_icon(size: int = 256) -> QIcon:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    gap = size // 14
    half = size // 2
    radius = size // 9
    for color, col, row in [
        ("#F39191", 0, 0),
        ("#6B7280", 1, 0),
        ("#F4AA6E", 0, 1),
        ("#C3B2F5", 1, 1),
    ]:
        p.setBrush(QBrush(QColor(color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(
            QRect(col * half + gap, row * half + gap, half - gap * 2, half - gap * 2),
            radius, radius,
        )
    p.end()
    return QIcon(px)


def _shadow(blur=15, offset=(0, 2), alpha=30):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(*offset)
    fx.setColor(QColor(0, 0, 0, alpha))
    return fx


class DueDateDialog(QDialog):
    def __init__(self, parent=None, current_date: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Set due date")
        self.setModal(True)
        self.setFixedSize(280, 120)
        self.setStyleSheet("background: #161616; color: #E5E7EB;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(12)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_date_edit.setFixedHeight(34)
        if current_date:
            date = QDate.fromString(current_date, "yyyy-MM-dd")
            if date.isValid():
                self.due_date_edit.setDate(date)
            else:
                self.due_date_edit.setDate(QDate.currentDate())
        else:
            self.due_date_edit.setDate(QDate.currentDate())

        self._layout.addWidget(self.due_date_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._layout.addWidget(buttons)

    def selected_date(self) -> str:
        return self.due_date_edit.date().toString("yyyy-MM-dd")


class NoteDialog(QDialog):
    def __init__(self, parent=None, current_note: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit note")
        self.setModal(True)
        self.setFixedSize(360, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.note_edit = QTextEdit()
        self.note_edit.setPlainText(current_note or "")
        self.note_edit.setStyleSheet("""
            QTextEdit {
                border: 1.5px solid #3D3D3D; border-radius: 8px;
                padding: 8px; font-family: 'Segoe UI'; font-size: 13px;
                color: #E5E7EB; background: #1E1E1E;
            }
        """)
        layout.addWidget(self.note_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_note(self) -> str:
        return self.note_edit.toPlainText().strip()


class TagDialog(QDialog):
    def __init__(self, parent=None, current_tag: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit tag")
        self.setModal(True)
        self.setFixedSize(300, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.tag_edit = QLineEdit()
        self.tag_edit.setText(current_tag or "")
        self.tag_edit.setPlaceholderText("Tag")
        self.tag_edit.setFixedHeight(36)
        self.tag_edit.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #3D3D3D; border-radius: 8px;
                padding: 0 12px; font-family: 'Segoe UI'; font-size: 13px;
                color: #E5E7EB; background: #161616;
            }
            QLineEdit:focus { border-color: #52525B; background: #1E1E1E; }
        """)
        layout.addWidget(self.tag_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_tag(self) -> str:
        return self.tag_edit.text().strip()


class DeletedHistoryDialog(QDialog):
    def __init__(self, parent=None, deleted_tasks: list[dict] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Deleted tasks history")
        self.setModal(True)
        self.setMinimumSize(520, 360)

        self._deleted_tasks = deleted_tasks or []
        self._selected_index = -1

        self.setStyleSheet("""
            QDialog { background: #161616; color: #E5E7EB; }
            QDialogButtonBox QPushButton {
                background: #2A2A2A; color: #E5E7EB;
                border: 1px solid #3D3D3D; border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 12px;
                padding: 6px 18px; min-width: 80px;
            }
            QDialogButtonBox QPushButton:hover { background: #333333; }
            QDialogButtonBox QPushButton:pressed { background: #1E1E1E; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #161616;
                border: 1.5px solid #3D3D3D;
                border-radius: 10px;
                padding: 6px;
                font-family: 'Segoe UI';
                font-size: 13px;
                outline: none;
                color: #E5E7EB;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin: 4px 0;
                color: #E5E7EB;
            }
            QListWidget::item:selected {
                background: #2E2E2E;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: rgba(255,255,255,0.08);
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Reuse task")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate_list()

    def _format_task_label(self, text: str, due_date: str | None, tag: str | None, note: str | None) -> str:
        label = text
        if tag:
            label += f" [{tag}]"
        if due_date:
            label += f" [{due_date}]"
        if note:
            label += " 📝"
        return label

    def _populate_list(self):
        self.list_widget.clear()
        for task in self._deleted_tasks:
            item = QListWidgetItem(self._format_task_label(task.get("text", ""), task.get("due"), task.get("tag"), task.get("note")))
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setToolTip(task.get("note", "") or "")
            self.list_widget.addItem(item)

    def _on_accept(self):
        self._selected_index = self.list_widget.currentRow()
        if self._selected_index < 0:
            return
        self.accept()

    def selected_task(self) -> dict | None:
        if 0 <= self._selected_index < len(self._deleted_tasks):
            return self._deleted_tasks[self._selected_index]
        return None


class QuadrantCard(QFrame):
    _MIN_FONT = 8
    _MAX_FONT = 24

    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.meta = QUADRANT_META[key]
        self._font_size = 13
        self._build()
        self.setGraphicsEffect(_shadow())
        self.setStyleSheet("QuadrantCard { background: #161616; border-radius: 10px; border: 1px solid #3D3D3D; }")

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(58)
        header.setStyleSheet(f"background: {self.meta['accent']}; border-radius: 0px;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(14, 8, 14, 8)
        hl.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_lbl = QLabel(self.meta["title"])
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white; background: transparent;")

        self.count_lbl = QLabel("0")
        self.count_lbl.setFixedSize(24, 24)
        self.count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_lbl.setStyleSheet(
            "background: rgba(255,255,255,0.28); color: white; border-radius: 12px;"
            "font-size: 11px; font-weight: bold;"
        )

        btn_style = """
            QPushButton {
                background: rgba(255,255,255,0.18); color: white;
                border: 1px solid rgba(255,255,255,0.35); border-radius: 4px;
                font-size: 14px; font-weight: bold; padding: 0;
            }
            QPushButton:hover { background: rgba(255,255,255,0.30); }
            QPushButton:pressed { background: rgba(255,255,255,0.10); }
        """
        dec_btn = QPushButton("−")
        dec_btn.setFixedSize(22, 22)
        dec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dec_btn.setStyleSheet(btn_style)
        dec_btn.setToolTip("Decrease font size")
        dec_btn.clicked.connect(self._decrease_font)

        inc_btn = QPushButton("+")
        inc_btn.setFixedSize(22, 22)
        inc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        inc_btn.setStyleSheet(btn_style)
        inc_btn.setToolTip("Increase font size")
        inc_btn.clicked.connect(self._increase_font)

        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(self.count_lbl)
        title_row.addWidget(dec_btn)
        title_row.addWidget(inc_btn)

        sub_lbl = QLabel(self.meta["sub"])
        sub_lbl.setFont(QFont("Segoe UI", 8))
        sub_lbl.setStyleSheet("color: rgba(255,255,255,0.75); background: transparent;")

        hl.addLayout(title_row)
        hl.addWidget(sub_lbl)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: #1E1E1E;
                border: none;
                padding: 6px;
                font-family: 'Segoe UI';
                font-size: {self._font_size}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 7px 10px;
                border-radius: 5px;
                margin: 2px 0;
                color: #E5E7EB;
            }}
            QListWidget::item:selected {{
                background: {self.meta['accent']};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background: rgba(255,255,255,0.08);
            }}
        """)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._context_menu)
        self.list_widget.model().rowsInserted.connect(self._refresh_count)
        self.list_widget.model().rowsRemoved.connect(self._refresh_count)
        self.list_widget.model().rowsMoved.connect(lambda: self.window().save_tasks())

        layout.addWidget(header)
        layout.addWidget(self.list_widget, stretch=1)

    def _refresh_count(self):
        self.count_lbl.setText(str(self.list_widget.count()))

    def _increase_font(self):
        if self._font_size < self._MAX_FONT:
            self._font_size += 1
            self._apply_font()

    def _decrease_font(self):
        if self._font_size > self._MIN_FONT:
            self._font_size -= 1
            self._apply_font()

    def _apply_font(self):
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: #1E1E1E;
                border: none;
                padding: 6px;
                font-family: 'Segoe UI';
                font-size: {self._font_size}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 7px 10px;
                border-radius: 5px;
                margin: 2px 0;
                color: #E5E7EB;
            }}
            QListWidget::item:selected {{
                background: {self.meta['accent']};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background: rgba(255,255,255,0.08);
            }}
        """)

    def _context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #161616; border: 1px solid #3D3D3D;
                border-radius: 6px; padding: 4px;
                font-family: 'Segoe UI'; font-size: 13px;
                color: #E5E7EB;
            }
            QMenu::item { padding: 7px 18px; border-radius: 4px; color: #E5E7EB; }
            QMenu::item:selected { background: rgba(150,150,150,0.20); }
            QMenu::separator { height: 1px; background: #3D3D3D; margin: 4px 8px; }
        """)

        delete_act = QAction("Delete task", self)
        delete_act.triggered.connect(lambda: self._delete(item))
        menu.addAction(delete_act)

        edit_due_act = QAction("Set due date...", self)
        edit_due_act.triggered.connect(lambda _=False, i=item: self.window().edit_task_due_date(i))
        menu.addAction(edit_due_act)

        _, current_due, current_tag, current_note = self.window().get_task_data(item)
        if current_due:
            clear_due_act = QAction("Remove due date", self)
            clear_due_act.triggered.connect(lambda _=False, i=item: self.window().clear_task_due_date(i))
            menu.addAction(clear_due_act)

        edit_tag_act = QAction("Edit tag...", self)
        edit_tag_act.triggered.connect(lambda _=False, i=item: self.window().edit_task_tag(i))
        menu.addAction(edit_tag_act)

        if current_tag:
            clear_tag_act = QAction("Remove tag", self)
            clear_tag_act.triggered.connect(lambda _=False, i=item: self.window().clear_task_tag(i))
            menu.addAction(clear_tag_act)

        edit_note_act = QAction("Edit note...", self)
        edit_note_act.triggered.connect(lambda _=False, i=item: self.window().edit_task_note(i))
        menu.addAction(edit_note_act)

        if current_note:
            clear_note_act = QAction("Remove note", self)
            clear_note_act.triggered.connect(lambda _=False, i=item: self.window().clear_task_note(i))
            menu.addAction(clear_note_act)

        menu.addSeparator()

        move_menu = menu.addMenu("Move to")
        move_menu.setStyleSheet(menu.styleSheet())
        for key, meta in QUADRANT_META.items():
            if key == self.key:
                continue
            act = QAction(f"{meta['title']}  —  {meta['sub']}", self)
            act.triggered.connect(lambda _=False, k=key, i=item: self._move(i, k))
            move_menu.addAction(act)

        menu.exec(self.list_widget.mapToGlobal(pos))

    def _delete(self, item):
        self.list_widget.takeItem(self.list_widget.row(item))
        self.window().delete_task(item, self.key)

    def _move(self, item, target_key):
        task, due_date, tag, note = self.window().get_task_data(item)
        self.list_widget.takeItem(self.list_widget.row(item))
        self.window().receive_task(task, target_key, due_date, tag, note)


class EisenhowerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eisenhower Matrix")
        self.setWindowIcon(make_app_icon())
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(920, 680)
        self._save_file = DEFAULT_SAVE_FILE
        self._cards: dict[str, QuadrantCard] = {}
        self._deleted_tasks: list[dict] = []
        self._drag_pos = None
        self._is_maximized = False
        self._build_ui()
        self.load_tasks()
        self._due_check_timer = QTimer(self)
        self._due_check_timer.timeout.connect(self._check_due_dates)
        self._due_check_timer.start(60_000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────
        bar = QFrame()
        bar.setFixedHeight(42)
        bar.setObjectName("title_bar")
        bar.setStyleSheet("QFrame#title_bar { background: #000000; border-bottom: 1px solid #111111; }")
        bar_l = QHBoxLayout(bar)
        bar_l.setContentsMargins(20, 0, 16, 0)
        bar_l.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(make_app_icon(24).pixmap(24, 24))
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_l.addWidget(icon_label)

        title = QLabel("Eisenhower Matrix")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        bar_l.addWidget(title)

        self.file_label = QLabel(self._short_path(self._save_file))
        self.file_label.setFont(QFont("Segoe UI", 9))
        self.file_label.setStyleSheet("color: rgba(248,247,252,0.65);")
        bar_l.addWidget(self.file_label)
        bar_l.addStretch()

        open_btn = QPushButton("Open file")
        open_btn.setFixedSize(90, 30)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setStyleSheet("""
            QPushButton {
                background: #090A0D; color: #E5E7EB;
                border: 1px solid #121316; border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 12px;
            }
            QPushButton:hover { background: #101217; }
            QPushButton:pressed { background: #07080B; }
        """)
        open_btn.clicked.connect(self.open_file)
        bar_l.addWidget(open_btn)

        self.deleted_btn = QPushButton("Deleted")
        self.deleted_btn.setFixedSize(90, 30)
        self.deleted_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.deleted_btn.setStyleSheet("""
            QPushButton {
                background: #090A0D; color: #E5E7EB;
                border: 1px solid #121316; border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 12px;
            }
            QPushButton:hover { background: #101217; }
            QPushButton:pressed { background: #07080B; }
        """)
        self.deleted_btn.clicked.connect(self.show_deleted_history)
        bar_l.addWidget(self.deleted_btn)

        self.minimize_btn = QPushButton("—")
        self.maximize_btn = QPushButton("☐")
        self.close_btn = QPushButton("✕")
        for btn, color in ((self.minimize_btn, "#E5E7EB"), (self.maximize_btn, "#E5E7EB"), (self.close_btn, "#F87171")):
            btn.setFixedSize(32, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: #0A0B0F; color: {color}; border: 1px solid #121316; border-radius: 6px; font-size: 14px; }}
                QPushButton:hover {{ background: #111319; }}
                QPushButton:pressed {{ background: #08090C; }}
            """)
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self._toggle_maximize_restore)
        self.close_btn.clicked.connect(self.close)

        bar_l.addWidget(self.minimize_btn)
        bar_l.addWidget(self.maximize_btn)
        bar_l.addWidget(self.close_btn)

        root.addWidget(bar)

        # ── Body ─────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #000000;")
        body_l = QVBoxLayout(body)
        body_l.setContentsMargins(24, 20, 24, 20)
        body_l.setSpacing(18)

        input_card = QFrame()
        input_card.setStyleSheet("QFrame { background: #1E1E1E; border-radius: 10px; border: 1px solid #3D3D3D; }")
        input_card.setGraphicsEffect(_shadow(alpha=25))
        input_card.setFixedHeight(68)
        il = QHBoxLayout(input_card)
        il.setContentsMargins(16, 14, 16, 14)
        il.setSpacing(12)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("What needs to be done?")
        self.task_input.setFixedHeight(38)
        self.task_input.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #3D3D3D; border-radius: 7px;
                padding: 0 12px; font-family: 'Segoe UI'; font-size: 13px;
                color: #E5E7EB; background: #161616;
            }
            QLineEdit:focus { border-color: #52525B; background: #1E1E1E; }
        """)
        self.task_input.returnPressed.connect(self.add_task)

        checkbox_style = """
            QCheckBox { font-family: 'Segoe UI'; font-size: 13px; color: #E5E7EB; spacing: 6px; }
            QCheckBox::indicator { width: 17px; height: 17px; border-radius: 4px; border: 1.5px solid #2D2D2D; background: #161616; }
            QCheckBox::indicator:checked { background: #52525B; border-color: #52525B; }
        """
        self.urgent_check = QCheckBox("Urgent")
        self.important_check = QCheckBox("Important")
        self.urgent_check.setStyleSheet(checkbox_style)
        self.important_check.setStyleSheet(checkbox_style)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag")
        self.tag_input.setFixedHeight(38)
        self.tag_input.setFixedWidth(100)
        self.tag_input.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #3D3D3D; border-radius: 7px;
                padding: 0 12px; font-family: 'Segoe UI'; font-size: 13px;
                color: #E5E7EB; background: #161616;
            }
            QLineEdit:focus { border-color: #52525B; background: #1E1E1E; }
        """)

        self.date_check = QCheckBox("Date")
        self.date_check.setStyleSheet(checkbox_style)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setEnabled(False)
        self.due_date_edit.setFixedHeight(38)
        self.due_date_edit.setStyleSheet("""
            QDateEdit {
                border: 1.5px solid #3D3D3D; border-radius: 7px;
                padding: 0 12px; font-family: 'Segoe UI'; font-size: 13px;
                color: #E5E7EB; background: #161616;
            }
            QDateEdit:focus { border-color: #52525B; background: #1E1E1E; }
        """)
        self.date_check.toggled.connect(self.due_date_edit.setEnabled)

        add_btn = QPushButton("Add Task")
        add_btn.setFixedSize(110, 38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton { background: #090A0D; color: white; border: none; border-radius: 7px;
                          font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: #101217; }
            QPushButton:pressed { background: #07080B; }
        """)
        add_btn.clicked.connect(self.add_task)

        il.addWidget(self.task_input, stretch=1)
        il.addWidget(self.urgent_check)
        il.addWidget(self.important_check)
        il.addWidget(self.tag_input)
        il.addWidget(self.date_check)
        il.addWidget(self.due_date_edit)
        il.addWidget(add_btn)
        body_l.addWidget(input_card)

        grid = QGridLayout()
        grid.setSpacing(16)
        for key, row, col in [
            ("urgent_important", 0, 0),
            ("important_not_urgent", 0, 1),
            ("urgent_not_important", 1, 0),
            ("neither", 1, 1),
        ]:
            card = QuadrantCard(key)
            self._cards[key] = card
            grid.addWidget(card, row, col)

        body_l.addLayout(grid, stretch=1)
        root.addWidget(body)

    # ── File picker ──────────────────────────────────────────────────

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open tasks file", _base_dir, "JSON files (*.json)"
        )
        if not path:
            return
        self._save_file = path
        self.file_label.setText(self._short_path(path))
        self._clear_all()
        self.load_tasks()

    def delete_task(self, item: QListWidgetItem, key: str | None = None):
        text, due_date, tag, note = self.get_task_data(item)
        if text:
            self._deleted_tasks.insert(0, {
                "text": text,
                "due": due_date,
                "tag": tag,
                "note": note,
                "key": key or "neither",
            })
        self.save_tasks()
        self._update_deleted_button()

    def show_deleted_history(self):
        dialog = DeletedHistoryDialog(self, self._deleted_tasks)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task = dialog.selected_task()
            if not task:
                return
            target_key = task.get("key") or "neither"
            self.receive_task(task.get("text", ""), target_key, task.get("due"), task.get("tag"), task.get("note"))
            self._deleted_tasks.remove(task)
            self.save_tasks()
            self._update_deleted_button()

    def _toggle_maximize_restore(self):
        if self._is_maximized:
            self.showNormal()
            self._is_maximized = False
            self.maximize_btn.setText("☐")
        else:
            self.showMaximized()
            self._is_maximized = True
            self.maximize_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < 42:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton and not self._is_maximized:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _update_deleted_button(self):
        count = len(self._deleted_tasks)
        self.deleted_btn.setText(f"Deleted ({count})" if count else "Deleted")

    def _clear_all(self):
        for card in self._cards.values():
            card.list_widget.clear()

    @staticmethod
    def _short_path(path: str) -> str:
        parts = path.replace("\\", "/").split("/")
        return "/".join(parts[-2:]) if len(parts) > 2 else path

    def _format_task_label(self, text: str, due_date: str | None, tag: str | None, note: str | None) -> str:
        label = text
        if tag:
            label += f" [{tag}]"
        if due_date:
            label += f" [{due_date}]"
        if note:
            label += " 📝"
        return label

    def _create_task_item(self, text: str, due_date: str | None, tag: str | None = None, note: str | None = None) -> QListWidgetItem:
        item = QListWidgetItem(self._format_task_label(text, due_date, tag, note))
        item.setData(Qt.ItemDataRole.UserRole, {"text": text, "due": due_date, "tag": tag, "note": note})
        item.setToolTip(note or "")
        return item

    @staticmethod
    def get_task_data(item: QListWidgetItem) -> tuple[str, str | None, str | None, str | None]:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            return (
                data.get("text", ""),
                data.get("due"),
                data.get("tag"),
                data.get("note"),
            )

        text = item.text()
        note = None
        if text.endswith(" 📝"):
            text = text[:-2]
            note = ""

        due_date = None
        tag = None
        if " [" in text and text.endswith("]"):
            parts = text.split(" [")
            text = parts[0]
            values = [part[:-1] for part in parts[1:]]
            if values:
                due_date = values[-1]
                if len(values) > 1:
                    tag = values[0]
        return text, due_date, tag, note

    def update_task_item(self, item: QListWidgetItem, text: str, due_date: str | None, tag: str | None, note: str | None):
        item.setText(self._format_task_label(text, due_date, tag, note))
        item.setData(Qt.ItemDataRole.UserRole, {"text": text, "due": due_date, "tag": tag, "note": note})
        item.setToolTip(note or "")

    def edit_task_due_date(self, item: QListWidgetItem):
        text, due_date, tag, note = self.get_task_data(item)
        dialog = DueDateDialog(self, due_date)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_task_item(item, text, dialog.selected_date(), tag, note)
            self.save_tasks()

    def clear_task_due_date(self, item: QListWidgetItem):
        text, _, tag, note = self.get_task_data(item)
        self.update_task_item(item, text, None, tag, note)
        self.save_tasks()

    def edit_task_note(self, item: QListWidgetItem):
        text, due_date, tag, note = self.get_task_data(item)
        dialog = NoteDialog(self, note)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_note = dialog.selected_note()
            self.update_task_item(item, text, due_date, tag, new_note)
            self.save_tasks()

    def clear_task_note(self, item: QListWidgetItem):
        text, due_date, tag, _ = self.get_task_data(item)
        self.update_task_item(item, text, due_date, tag, None)
        self.save_tasks()

    def edit_task_tag(self, item: QListWidgetItem):
        text, due_date, tag, note = self.get_task_data(item)
        dialog = TagDialog(self, tag)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_tag = dialog.selected_tag()
            self.update_task_item(item, text, due_date, new_tag, note)
            self.save_tasks()

    def clear_task_tag(self, item: QListWidgetItem):
        text, due_date, _, note = self.get_task_data(item)
        self.update_task_item(item, text, due_date, None, note)
        self.save_tasks()

    # ── Task operations ──────────────────────────────────────────────

    def add_task(self):
        task = self.task_input.text().strip()
        if not task:
            return
        urgent = self.urgent_check.isChecked()
        important = self.important_check.isChecked()
        due_date = None
        if self.date_check.isChecked():
            due_date = self.due_date_edit.date().toString("yyyy-MM-dd")

        if urgent and important:
            key = "urgent_important"
        elif important:
            key = "important_not_urgent"
        elif urgent:
            key = "urgent_not_important"
        else:
            key = "neither"

        tag = self.tag_input.text().strip() or None
        self._cards[key].list_widget.addItem(self._create_task_item(task, due_date, tag))
        self.task_input.clear()
        self.urgent_check.setChecked(False)
        self.important_check.setChecked(False)
        self.tag_input.clear()
        self.date_check.setChecked(False)
        self.due_date_edit.setDate(QDate.currentDate())
        self.save_tasks()

    def receive_task(self, task: str, target_key: str, due_date: str | None = None, tag: str | None = None, note: str | None = None):
        self._cards[target_key].list_widget.addItem(self._create_task_item(task, due_date, tag, note))
        self.save_tasks()

    # ── Persistence ──────────────────────────────────────────────────

    def load_tasks(self):
        self._clear_all()
        self._deleted_tasks = []
        if not os.path.exists(self._save_file):
            self._update_deleted_button()
            return
        with open(self._save_file, "r") as f:
            data = json.load(f)
        self._deleted_tasks = data.get("deleted_history", []) or []
        for key, card in self._cards.items():
            for task in data.get(key, []):
                if isinstance(task, dict):
                    text = task.get("text", "")
                    due_date = task.get("due")
                    tag = task.get("tag")
                    note = task.get("note")
                else:
                    text = task
                    due_date = None
                    tag = None
                    note = None
                if text:
                    card.list_widget.addItem(self._create_task_item(text, due_date, tag, note))
        self._check_due_dates()
        self._update_deleted_button()
        self._update_deleted_button()

    def save_tasks(self):
        data = {
            key: [
                {
                    "text": self.get_task_data(card.list_widget.item(i))[0],
                    "due": self.get_task_data(card.list_widget.item(i))[1],
                    "tag": self.get_task_data(card.list_widget.item(i))[2],
                    "note": self.get_task_data(card.list_widget.item(i))[3],
                }
                for i in range(card.list_widget.count())
            ]
            for key, card in self._cards.items()
        }
        data["deleted_history"] = self._deleted_tasks
        with open(self._save_file, "w") as f:
            json.dump(data, f, indent=2)

    def _check_due_dates(self):
        source = self._cards["important_not_urgent"]
        moved = []
        today = QDate.currentDate()
        for i in range(source.list_widget.count() - 1, -1, -1):
            item = source.list_widget.item(i)
            text, due_date, tag, note = self.get_task_data(item)
            if not due_date:
                continue
            due = QDate.fromString(due_date, "yyyy-MM-dd")
            if due.isValid() and due <= today:
                source.list_widget.takeItem(i)
                moved.append((text, due_date, tag, note))
        if moved:
            for text, due_date, tag, note in moved:
                self._cards["urgent_important"].list_widget.addItem(
                    self._create_task_item(text, due_date, tag, note)
                )
            self.save_tasks()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(make_app_icon())
    window = EisenhowerApp()
    window.show()
    sys.exit(app.exec())
