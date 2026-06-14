"""Главное окно Fleet Manager."""
import time
import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QSpinBox, QPushButton, QButtonGroup, QComboBox,
    QCheckBox, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy,
)
from PySide6.QtGui import QColor

from collections import Counter

import config
import ui.styles as styles
from core.distribution import Member, compute_distribution, FLEET_LIMIT
from core.sorting import sort_members


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fleet Manager")
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        self._members: list[Member] = []
        self._sort_mode = "time-asc"
        self._targets: dict[str, int] = {}   # id -> целевое число (до скольки изменить)
        self._on_top = bool(config.get("always_on_top", False))

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(14)

        root.addWidget(self._build_header())
        root.addWidget(self._build_summary())
        root.addWidget(self._build_form())
        root.addLayout(self._build_controls())
        root.addWidget(self._build_table(), stretch=1)

        self._refresh()

        # Восстанавливаем размер/позицию окна и режим «поверх всех» из настроек.
        config.restore_window_geometry(self)
        if self._on_top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

    # ── Секции UI ─────────────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("header_bar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 6, 14, 6)
        title = QLabel("FLEET  MANAGER")
        title.setObjectName("title")
        self._btn_top = QPushButton("Поверх всех окон")
        self._btn_top.setObjectName("seg")
        self._btn_top.setCheckable(True)
        self._btn_top.setChecked(self._on_top)
        self._btn_top.setToolTip("Держать окно поверх всех окон")
        self._btn_top.clicked.connect(self._toggle_on_top)
        lay.addWidget(title)
        lay.addStretch(1)
        lay.addWidget(self._btn_top)
        return bar

    def _build_summary(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QHBoxLayout(panel)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)

        cap = QLabel("FLEET")
        cap.setObjectName("dim")
        self._lbl_total = QLabel("0")
        self._lbl_total.setObjectName("bignum")
        slash = QLabel(f"/ {FLEET_LIMIT}")
        slash.setStyleSheet(f"color:{styles.TEXT_DIM}; font-size:16px;")

        self._bar = QProgressBar()
        self._bar.setRange(0, FLEET_LIMIT)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)

        lay.addWidget(cap)
        lay.addWidget(self._lbl_total)
        lay.addWidget(slash)
        lay.addWidget(self._bar, stretch=1)
        return panel

    def _build_form(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QHBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        name_box = QVBoxLayout()
        name_box.setSpacing(4)
        lbl_n = QLabel("ИМЯ ПОЛЬЗОВАТЕЛЯ")
        lbl_n.setObjectName("dim")
        self._inp_name = QLineEdit()
        self._inp_name.setPlaceholderText("Pilot Name")
        self._inp_name.setMaximumWidth(240)
        self._inp_name.returnPressed.connect(self._on_add)
        name_box.addWidget(lbl_n)
        name_box.addWidget(self._inp_name)

        max_box = QVBoxLayout()
        max_box.setSpacing(4)
        lbl_m = QLabel("МАКС. ОКОН")
        lbl_m.setObjectName("dim")
        self._inp_max = QSpinBox()
        self._inp_max.setRange(1, 99)
        self._inp_max.setValue(10)
        self._inp_max.setFixedWidth(90)
        self._inp_max.setAlignment(Qt.AlignCenter)
        max_box.addWidget(lbl_m)
        max_box.addWidget(self._inp_max)

        btn = QPushButton("ДОБАВИТЬ")
        btn.setObjectName("primary")
        btn.clicked.connect(self._on_add)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        lay.addLayout(name_box, stretch=1)
        lay.addLayout(max_box)
        lay.addWidget(btn)
        return panel

    def _build_controls(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(6)
        lbl = QLabel("Сортировка:")
        lbl.setObjectName("dim")
        lay.addWidget(lbl)

        self._sort_group = QButtonGroup(self)
        self._sort_group.setExclusive(True)

        for key, label in (("name-asc", "Имя A→Z"), ("name-desc", "Имя Z→A")):
            b = QPushButton(label)
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setChecked(key == self._sort_mode)
            b.clicked.connect(lambda _checked, k=key: self._set_sort(k))
            self._sort_group.addButton(b)
            lay.addWidget(b)

        # Одна кнопка сортировки по времени приглашения; повторный клик меняет направление.
        self._btn_time = QPushButton()
        self._btn_time.setObjectName("seg")
        self._btn_time.setCheckable(True)
        self._btn_time.setChecked(self._sort_mode.startswith("time"))
        self._btn_time.clicked.connect(self._on_time_clicked)
        self._sort_group.addButton(self._btn_time)
        lay.addWidget(self._btn_time)
        self._update_time_label()

        lay.addStretch(1)

        theme_lbl = QLabel("Тема:")
        theme_lbl.setObjectName("dim")
        lay.addWidget(theme_lbl)
        self._theme_combo = QComboBox()
        saved_theme = config.get("theme", "default")
        for preset in styles.THEME_PRESETS:
            self._theme_combo.addItem(preset["name"], preset["id"])
            if preset["id"] == saved_theme:
                self._theme_combo.setCurrentIndex(self._theme_combo.count() - 1)
        self._theme_combo.currentIndexChanged.connect(self._on_theme)
        lay.addWidget(self._theme_combo)
        return lay

    def _build_table(self) -> QWidget:
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            ["#", "Имя", "Макс", "Сейчас", "Надо", "Команда", "✓", ""]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setFocusPolicy(Qt.NoFocus)
        self._table.setShowGrid(False)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in (2, 3, 4, 5, 6, 7):
            hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        return self._table

    # ── Действия ────────────────────────────────────────────────────────────────
    def _on_add(self):
        name = self._inp_name.text().strip()
        if not name:
            self._inp_name.setFocus()
            return
        self._members.append(Member(
            id=uuid.uuid4().hex,
            name=name,
            max_chars=self._inp_max.value(),
            created_at=time.time(),
            current_chars=0,
        ))
        self._inp_name.clear()
        self._inp_name.setFocus()
        self._refresh()

    def _remove(self, member_id: str):
        self._members = [m for m in self._members if m.id != member_id]
        self._refresh()

    def _set_sort(self, mode: str):
        self._sort_mode = mode
        self._update_time_label()
        self._refresh()

    def _on_time_clicked(self):
        # Уже сортируем по времени — переключаем направление; иначе включаем.
        if self._sort_mode.startswith("time"):
            self._sort_mode = "time-desc" if self._sort_mode == "time-asc" else "time-asc"
        else:
            self._sort_mode = "time-asc"
        self._update_time_label()
        self._refresh()

    def _update_time_label(self):
        arrow = "↓" if self._sort_mode == "time-desc" else "↑"
        self._btn_time.setText(f"По времени приглашения {arrow}")

    def _on_theme(self, _index: int):
        from PySide6.QtWidgets import QApplication
        theme_id = self._theme_combo.currentData()
        qss = styles.apply_theme(theme_id)
        QApplication.instance().setStyleSheet(qss)
        config.set_value("theme", theme_id)
        self._refresh()

    def _toggle_on_top(self, checked: bool):
        self._on_top = checked
        config.set_value("always_on_top", checked)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()   # смена флага требует повторного show()

    def closeEvent(self, event):
        config.save_window_geometry(self)
        super().closeEvent(event)

    def _on_confirm(self, member_id: str, checked: bool):
        """Командир подтвердил/снял подтверждение, что пилот изменил число окон.
        Подтверждение → факт «Сейчас» приравнивается к цели «Надо»; снятие → 0."""
        for m in self._members:
            if m.id == member_id:
                m.current_chars = self._targets.get(member_id, 0) if checked else 0
                break
        self._refresh()

    # ── Рендер ───────────────────────────────────────────────────────────────────
    def _refresh(self):
        ordered = sort_members(self._members, self._sort_mode)
        result = compute_distribution(ordered)
        self._targets = dict(result.assigned)

        current_total = sum(m.current_chars for m in self._members)
        over = current_total > FLEET_LIMIT
        color = styles.RED if over else styles.ACCENT

        # Сводка: фактическое число окон / 60 (красное при превышении)
        self._lbl_total.setText(str(current_total))
        self._lbl_total.setStyleSheet(f"font-size:22px; font-weight:bold; color:{color};")
        self._bar.setValue(min(current_total, FLEET_LIMIT))
        self._bar.setStyleSheet(
            "QProgressBar::chunk { background: %s; border-radius:2px; }" % color
        )

        # Имена, встречающиеся более одного раза (без учёта регистра) — дубликаты.
        name_counts = Counter(m.name.casefold() for m in self._members)

        # Таблица
        self._table.setRowCount(len(ordered))
        for row, m in enumerate(ordered):
            target = result.assigned.get(m.id, 0)
            delta = target - m.current_chars

            self._table.setItem(row, 0, self._cell(str(row + 1), styles.TEXT_DIM, Qt.AlignCenter))

            is_dup = name_counts[m.name.casefold()] > 1
            name_text = f"⚠ {m.name}" if is_dup else m.name
            name_item = self._cell(name_text, styles.RED if is_dup else styles.TEXT,
                                   Qt.AlignLeft | Qt.AlignVCenter)
            if is_dup:
                name_item.setToolTip("Совпадающее имя — пилот добавлен дважды")
            self._table.setItem(row, 1, name_item)
            self._table.setItem(row, 2, self._cell(str(m.max_chars), styles.TEXT_DIM, Qt.AlignCenter))
            self._table.setItem(row, 3, self._cell(str(m.current_chars), styles.TEXT, Qt.AlignCenter))
            self._table.setItem(row, 4, self._cell(str(target), styles.ACCENT, Qt.AlignCenter))

            # Команда командиру: на сколько изменить (+ добавить / − убрать)
            if delta > 0:
                cmd_text, cmd_color = f"+{delta}", styles.GREEN
            elif delta < 0:
                cmd_text, cmd_color = f"−{abs(delta)}", styles.RED
            else:
                cmd_text, cmd_color = "—", styles.TEXT_DIM
            self._table.setItem(row, 5, self._cell(cmd_text, cmd_color, Qt.AlignCenter))

            # Чекбокс подтверждения (отмечен, когда «Сейчас» == «Надо»)
            self._table.setCellWidget(row, 6, self._make_check(m.id, delta == 0 and target > 0))

            # Кнопка удаления пилота из флота
            del_btn = QPushButton("✕")
            del_btn.setObjectName("del")
            del_btn.setToolTip(f"Удалить {m.name} из флота")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _c, mid=m.id: self._remove(mid))
            self._table.setCellWidget(row, 7, del_btn)

            self._table.setRowHeight(row, 38)

    def _make_check(self, member_id: str, checked: bool) -> QWidget:
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        cb = QCheckBox()
        cb.setChecked(checked)
        cb.setToolTip("Подтвердить, что пилот изменил число окон")
        cb.clicked.connect(lambda c, mid=member_id: self._on_confirm(mid, c))
        lay.addWidget(cb)
        return cont

    @staticmethod
    def _cell(text: str, color: str, align) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        item.setTextAlignment(align)
        return item
