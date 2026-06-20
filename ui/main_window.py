"""Главное окно Fleet Manager."""
import os
import sys
import time
import uuid

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QComboBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QMessageBox, QApplication, QStyledItemDelegate,
)
from PySide6.QtGui import (
    QColor, QIntValidator, QPixmap, QPen, QFont, QFontMetrics, QMovie, QRegion, QPainter,
    QDesktopServices,
)

from collections import Counter

import config
import ui.styles as styles
from core.distribution import Member, compute_distribution, FLEET_LIMIT
from core.sorting import sort_members


ZKILL_URL = "https://zkillboard.com/character/2124139671/"


def _resource(name: str) -> str:
    """Путь к ресурсу рядом с этим модулем (или в распакованном PyInstaller-бандле)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "ui", name)
    return os.path.join(os.path.dirname(__file__), name)


class _ClickableLabel(QLabel):
    """QLabel, открывающий ссылку по клику (для логотипа)."""

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl(self._url))
        super().mousePressEvent(event)


class _HeaderRuleDelegate(QStyledItemDelegate):
    """Рисует горизонтальную разделительную полосу под строкой-итогом (row 0)."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = QColor(color)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.row() == 0:
            painter.save()
            pen = QPen(self._color)
            pen.setWidth(2)
            painter.setPen(pen)
            y = option.rect.bottom()
            painter.drawLine(option.rect.left(), y, option.rect.right(), y)
            painter.restore()


class SnakeFleetBar(QWidget):
    """Полоска флота. В обычных темах — простой прогресс-бар; в теме Uroborus
    по зелёной заливке слева направо ползёт анимированная змея (GIF)."""

    SNAKE_W, SNAKE_H = 104, 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self._max = 60
        self._value = 0
        self._over = False
        self._fill = styles.ACCENT
        self._snake_on = False
        self._x = float(-self.SNAKE_W)
        self.setMinimumHeight(self.SNAKE_H)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._movie = QMovie(_resource("snake.gif"))
        self._movie.setCacheMode(QMovie.CacheAll)
        self._snake = QLabel(self)
        self._snake.setMovie(self._movie)
        self._snake.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._snake.setStyleSheet("background: transparent;")
        self._snake.resize(self.SNAKE_W, self.SNAKE_H)
        self._snake.hide()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._crawl)

    # ── API в духе QProgressBar ──────────────────────────────────────────────
    def setRange(self, _lo, hi):
        self._max = max(1, int(hi))
        self.update()

    def setValue(self, v):
        self._value = max(0, min(int(v), self._max))
        self.update()

    def set_over(self, over: bool):
        self._over = bool(over)
        self.update()

    def set_fill(self, color: str):
        self._fill = color
        self.update()

    def set_snake(self, on: bool):
        self._snake_on = bool(on)
        if on:
            self._x = float(-self.SNAKE_W)
            self._snake.show()
            self._movie.start()
            self._timer.start(40)
        else:
            self._timer.stop()
            self._movie.stop()
            self._snake.hide()
        self.update()

    # ── внутреннее ────────────────────────────────────────────────────────────
    def _fill_edge(self) -> int:
        return int(self._value / self._max * self.width()) if self._max else 0

    def _crawl(self):
        edge = self._fill_edge()
        if edge <= 0:                           # флот пуст — змеи нет вовсе
            self._snake.setMask(QRegion())
            return
        self._x += 2.4
        if self._x > edge:                      # дошла до края заливки — заново слева
            self._x = float(-self.SNAKE_W)
        y = (self.height() - self.SNAKE_H) // 2
        xi = int(self._x)
        self._snake.move(xi, y)
        # Маска в координатах метки: показываем только часть змеи в пределах
        # зелёной заливки на ЭКРАНЕ, т.е. screen ∈ [0, edge].
        local_start = max(0, -xi)
        local_end = min(self.SNAKE_W, edge - xi)
        width = max(0, local_end - local_start)
        self._snake.setMask(QRegion(local_start, 0, width, self.SNAKE_H))

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        edge = self._fill_edge()
        fill_col = QColor(styles.RED if self._over else self._fill)

        if self._snake_on:
            # Тёмная труба во всю высоту + тонкая полоса-прогресс; сверху ползёт змея.
            p.setPen(QPen(QColor(styles.BORDER), 1))
            p.setBrush(QColor(styles.BG_DEEP))
            p.drawRoundedRect(0.5, 0.5, w - 1, h - 1, 4, 4)
            line_h = 5.0
            ly = (h - line_h) / 2.0
            if edge > 1:
                p.setPen(Qt.NoPen)
                p.setBrush(fill_col)
                p.drawRoundedRect(0, ly, edge, line_h, line_h / 2, line_h / 2)
        else:
            # Обычный тонкий прогресс-бар.
            band = 8.0
            y = (h - band) / 2.0
            r = band / 2.0
            p.setPen(QPen(QColor(styles.BORDER), 1))
            p.setBrush(QColor(styles.BG_DEEP))
            p.drawRoundedRect(0.5, y + 0.5, w - 1, band - 1, r, r)
            if edge > 1:
                p.setPen(Qt.NoPen)
                p.setBrush(fill_col)
                p.drawRoundedRect(0, y, edge, band, r, r)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fleet Manager")
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        self._members: list[Member] = self._load_fleet()
        self._sort_mode = "time-asc"
        self._targets: dict[str, int] = {}   # id -> целевое число (до скольки изменить)
        self._fleet_cache_sig = None         # снимок последнего записанного кэша

        self._on_top = bool(config.get("always_on_top", False))
        self._fleet_limit = int(config.get("fleet_limit", FLEET_LIMIT))

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
        logo = _ClickableLabel(ZKILL_URL)
        logo.setToolTip("Open on zKillboard")
        pix = QPixmap(_resource("logo.png"))
        if not pix.isNull():
            logo.setPixmap(pix.scaledToHeight(28, Qt.SmoothTransformation))

        # Кликабельный бренд: открывает страницу корпорации на zKillboard.
        self._brand = QLabel()
        self._brand.setObjectName("title")
        self._brand.setOpenExternalLinks(True)
        self._brand.setCursor(Qt.PointingHandCursor)
        self._brand.setToolTip("Open on zKillboard")
        self._set_brand_html()

        self._theme_combo = QComboBox()
        saved_theme = config.get("theme", "default")
        for preset in styles.THEME_PRESETS:
            self._theme_combo.addItem(preset["name"], preset["id"])
            if preset["id"] == saved_theme:
                self._theme_combo.setCurrentIndex(self._theme_combo.count() - 1)
        self._theme_combo.currentIndexChanged.connect(self._on_theme)

        self._btn_top = QPushButton("Always on top")
        self._btn_top.setObjectName("seg")
        self._btn_top.setCheckable(True)
        self._btn_top.setChecked(self._on_top)
        self._btn_top.setToolTip("Keep the window above all other windows")
        self._btn_top.clicked.connect(self._toggle_on_top)

        lay.addWidget(logo)
        lay.addWidget(self._brand)
        lay.addStretch(1)
        lay.addWidget(self._theme_combo)
        lay.addWidget(self._btn_top)
        return bar

    def _set_brand_html(self):
        """Бренд-ссылка с цветом текущей темы (accent)."""
        self._brand.setText(
            f'<a href="{ZKILL_URL}" '
            f'style="color:{styles.ACCENT}; text-decoration:none;">Invasion Force</a>'
        )

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
        self._slash = QLabel(f"/ {self._fleet_limit}")
        self._slash.setStyleSheet(f"color:{styles.TEXT_DIM}; font-size:16px;")

        self._bar = SnakeFleetBar()
        self._bar.setRange(0, self._fleet_limit)
        self._bar.set_fill(styles.ACCENT)
        self._bar.set_snake(config.get("theme", "default") == "uroborus")

        # Размер флота: 40 / 60 / 120 окон.
        self._size_combo = QComboBox()
        self._size_combo.setToolTip("Fleet size limit")
        for n in (40, 60, 120):
            self._size_combo.addItem(str(n), n)
        idx = self._size_combo.findData(self._fleet_limit)
        if idx >= 0:
            self._size_combo.setCurrentIndex(idx)
        self._size_combo.currentIndexChanged.connect(self._on_fleet_size)

        # Индикатор плюшек: сколько слотов под них свободно / сколько убрать.
        self._lbl_sponge = QLabel("")
        self._lbl_sponge.setAlignment(Qt.AlignCenter)

        lay.addWidget(cap)
        lay.addWidget(self._lbl_total)
        lay.addWidget(self._slash)
        lay.addWidget(self._bar, stretch=1)
        lay.addWidget(self._lbl_sponge)
        lay.addWidget(self._size_combo)
        return panel

    def _build_form(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QHBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        # Имя персонажа: подпись внутри поля (placeholder), ширина +30% (120 → 156).
        self._inp_name = QLineEdit()
        self._inp_name.setPlaceholderText("Character Name")
        self._inp_name.setFixedWidth(156)
        self._inp_name.returnPressed.connect(self._on_add)

        # Макс. окон: обычное числовое поле ввода с подсказкой «Max» внутри
        # (placeholder исчезает при вводе). Принимает только числа 1–99.
        self._inp_max = QLineEdit()
        self._inp_max.setPlaceholderText("Max")
        self._inp_max.setValidator(QIntValidator(1, 99, self))
        self._inp_max.setMaxLength(2)
        self._inp_max.setFixedWidth(110)
        self._inp_max.setAlignment(Qt.AlignCenter)
        self._inp_max.returnPressed.connect(self._on_add)

        # Кнопка ADD — компактная (половина прежней ширины).
        btn = QPushButton("ADD")
        btn.setObjectName("primary")
        btn.clicked.connect(self._on_add)
        btn.setFixedWidth(78)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        lay.addWidget(self._inp_name)
        lay.addWidget(self._inp_max)
        lay.addWidget(btn)
        lay.addStretch(1)
        return panel

    def _build_controls(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(6)
        lbl = QLabel("Sort:")
        lbl.setObjectName("dim")
        lay.addWidget(lbl)

        self._sort_group = QButtonGroup(self)
        self._sort_group.setExclusive(True)

        for key, label in (("name-asc", "Name A→Z"), ("name-desc", "Name Z→A")):
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

        # CHECK: копирует в буфер «имя — окон во флоте (+ плюшки)».
        self._btn_check = QPushButton("CHECK")
        self._btn_check.setObjectName("seg")
        self._btn_check.setToolTip("Copy fleet assignments to clipboard")
        self._btn_check.clicked.connect(self._on_check)
        lay.addSpacing(10)
        lay.addWidget(self._btn_check)

        # CHECK очищает весь список флота (с подтверждением).
        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setObjectName("danger")
        self._btn_clear.setToolTip("Remove all pilots from the fleet")
        self._btn_clear.clicked.connect(self._on_clear)
        lay.addWidget(self._btn_clear)

        lay.addStretch(1)
        return lay

    def _build_table(self) -> QWidget:
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Character", "Max", "Fleet", "Sponge", "UP/DOWN", "✓", ""]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setFocusPolicy(Qt.NoFocus)
        self._table.setShowGrid(False)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        # ✓ — по содержимому.
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        # Степперы Max/Sponge — фиксированная ширина под кнопки. In Fleet и UP/DOWN
        # сужаем РОВНО до их заголовков: ширину текста меряем реальным шрифтом
        # заголовка (Segoe UI 11px bold) в рантайме, так что на любой машине текст
        # «UP/DOWN» не режется, а лишнего места в «In Fleet» не остаётся.
        hfont = QFont("Segoe UI")
        hfont.setPixelSize(11)
        hfont.setBold(True)
        hfm = QFontMetrics(hfont)
        # Max/Sponge: ширина под степпер [−] число [+] (≈82px) + небольшой запас,
        # чтобы кнопки не обрезались. In Fleet/UP-DOWN — ровно по их заголовкам.
        widths = {
            1: 88,
            2: hfm.horizontalAdvance("Fleet") + 18,
            3: 88,
            4: hfm.horizontalAdvance("UP/DOWN") + 18,
        }
        for col, wdt in widths.items():
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self._table.setColumnWidth(col, wdt)
        # Разделительная полоса под строкой-итогом.
        self._table.setItemDelegate(_HeaderRuleDelegate(styles.BORDER_LT, self._table))
        # Колонка кнопки удаления — тоже фиксированная (cell-виджет без данных).
        hh.setSectionResizeMode(6, QHeaderView.Fixed)
        self._table.setColumnWidth(6, 44)
        # Цвета заголовков задаём через item (QSS секции цвет не задаёт):
        # Fleet — фиолетовый, Sponge — янтарный, остальные — dim.
        header_colors = {2: styles.PURPLE, 3: styles.AMBER}
        for c in range(self._table.columnCount()):
            item = self._table.horizontalHeaderItem(c)
            if item is not None:
                item.setForeground(QColor(header_colors.get(c, styles.TEXT_DIM)))
        return self._table

    # ── Действия ────────────────────────────────────────────────────────────────
    def _on_add(self):
        name = self._inp_name.text().strip()
        if not name:
            self._inp_name.setFocus()
            return
        max_txt = self._inp_max.text().strip()
        max_chars = int(max_txt) if max_txt else 1
        self._members.append(Member(
            id=uuid.uuid4().hex,
            name=name,
            max_chars=max_chars,
            created_at=time.time(),
            current_chars=0,
        ))
        self._inp_name.clear()
        self._inp_name.setFocus()
        self._refresh()

    def _remove(self, member_id: str):
        self._members = [m for m in self._members if m.id != member_id]
        self._refresh()

    def _member(self, member_id: str) -> Member | None:
        return next((m for m in self._members if m.id == member_id), None)

    # ── Кэш состава флота ─────────────────────────────────────────────────────────
    def _load_fleet(self) -> list[Member]:
        """Восстанавливает состав флота из кэша (на случай закрытия приложения)."""
        members: list[Member] = []
        for d in config.get("fleet", []) or []:
            try:
                members.append(Member(
                    id=str(d.get("id") or uuid.uuid4().hex),
                    name=str(d["name"]),
                    max_chars=int(d.get("max_chars", 1)),
                    created_at=float(d.get("created_at", time.time())),
                    current_chars=int(d.get("current_chars", 0)),
                    sponge=int(d.get("sponge", 0)),
                ))
            except (KeyError, ValueError, TypeError):
                continue
        return members

    def _persist_fleet(self):
        """Сохраняет состав флота в кэш — только если он изменился с прошлой записи
        (чтобы view-обновления вроде смены темы/сортировки не дёргали диск)."""
        data = [
            {"id": m.id, "name": m.name, "max_chars": m.max_chars,
             "created_at": m.created_at, "current_chars": m.current_chars,
             "sponge": m.sponge}
            for m in self._members
        ]
        if data == self._fleet_cache_sig:
            return
        self._fleet_cache_sig = data
        config.set_value("fleet", data)

    def _on_check(self):
        """Копирует в буфер по строке на пилота: «имя - <окон во флоте>[ + <плюшки>]»."""
        ordered = sort_members(self._members, self._sort_mode)
        result = compute_distribution(ordered, fleet_limit=self._fleet_limit)
        lines = []
        for m in ordered:
            target = result.assigned.get(m.id, 0)
            line = f"{m.name} - {target}"
            if m.sponge > 0:
                line += f" + {m.sponge}"
            lines.append(line)
        QApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage("Copied to clipboard", 3000)

    def _on_clear(self):
        """Полностью очищает список флота (с подтверждением)."""
        if not self._members:
            return
        ans = QMessageBox.question(
            self, "Clear fleet", "Remove all pilots from the fleet?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ans == QMessageBox.Yes:
            self._members = []
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
        self._btn_time.setText(f"By invite time {arrow}")

    def _on_theme(self, _index: int):
        theme_id = self._theme_combo.currentData()
        qss = styles.apply_theme(theme_id)
        QApplication.instance().setStyleSheet(qss)
        config.set_value("theme", theme_id)
        self._set_brand_html()   # ссылка перенимает accent новой темы
        self._bar.set_fill(styles.ACCENT)
        self._bar.set_snake(theme_id == "uroborus")
        self._refresh()

    def _on_fleet_size(self, _index: int):
        self._fleet_limit = self._size_combo.currentData()
        config.set_value("fleet_limit", self._fleet_limit)
        self._slash.setText(f"/ {self._fleet_limit}")
        self._bar.setRange(0, self._fleet_limit)
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
        m = self._member(member_id)
        if m is not None:
            m.current_chars = self._targets.get(member_id, 0) if checked else 0
        self._refresh()

    def _on_confirm_all(self):
        """Главная галочка: ТОЛЬКО подтверждает выбор у всех (Сейчас = цель)."""
        for m in self._members:
            m.current_chars = self._targets.get(m.id, 0)
        self._refresh()

    # ── Рендер ───────────────────────────────────────────────────────────────────
    def _refresh(self):
        ordered = sort_members(self._members, self._sort_mode)
        result = compute_distribution(ordered, fleet_limit=self._fleet_limit)
        self._targets = dict(result.assigned)

        fleet_used = self._fleet_used()   # реальные окна + плюшки занимают слоты
        over = fleet_used > self._fleet_limit
        color = styles.RED if over else styles.ACCENT

        # Сводка: занятые слоты (реальные окна + плюшки) / лимит, красное при превышении
        self._lbl_total.setText(str(fleet_used))
        self._lbl_total.setStyleSheet(f"font-size:22px; font-weight:bold; color:{color};")
        self._bar.set_over(over)
        self._bar.setValue(min(fleet_used, self._fleet_limit))

        # Индикатор плюшек: свободные слоты / требование убрать лишние.
        capacity, sponge_total, free = self._sponge_metrics(result)
        if free < 0:
            sp_text, sp_color = f"⚠ Remove {-free} sponge", styles.RED
        elif free == 0:
            sp_text, sp_color = ("Sponge slots: full" if sponge_total or capacity == 0
                                 else "Sponge slots: 0"), styles.AMBER
        else:
            sp_text, sp_color = f"Sponge slots free: {free}", styles.GREEN
        self._lbl_sponge.setText(sp_text)
        self._lbl_sponge.setStyleSheet(f"color:{sp_color}; font-weight:bold; font-size:11px;")

        # Сколько плюшек ОСТАЁТСЯ у каждого: честно раздаём capacity слотов по тем же
        # правилам (water-filling), потолок = текущее число плюшек пилота. Разница с
        # текущим числом = сколько убрать (плюшки уходят из флота в приоритете).
        # Это только подсказка ФК — авто-изменение плюшек не делаем.
        sponge_keep = compute_distribution(
            [Member(id=m.id, name=m.name, max_chars=m.sponge, created_at=m.created_at)
             for m in ordered],
            fleet_limit=capacity,
        ).assigned

        # Имена, встречающиеся более одного раза (без учёта регистра) — дубликаты.
        name_counts = Counter(m.name.casefold() for m in self._members)

        # Таблица: строка-итог (шапка) сверху + строки пилотов.
        total_windows = sum(m.max_chars for m in self._members)
        char_count = len(self._members)
        # Есть ли неподтверждённые изменения (Сейчас ≠ цель). Мастер-галочка видна
        # только когда есть что подтверждать; без изменений — её нет.
        pending = any(m.current_chars != self._targets.get(m.id, 0) for m in ordered)

        self._table.setRowCount(len(ordered) + 1)
        # Character → число персонажей, Max → суммарное число окон.
        self._table.setItem(0, 0, self._cell(f"{char_count} chars", styles.ACCENT,
                                             Qt.AlignLeft | Qt.AlignVCenter, bold=True,
                                             bg=styles.BG_HEADER))
        self._table.setItem(0, 1, self._cell(str(total_windows), styles.ACCENT,
                                             Qt.AlignCenter, bold=True, bg=styles.BG_HEADER))
        for c in (2, 3, 4, 6):
            self._table.setItem(0, c, self._cell("", styles.TEXT, Qt.AlignCenter,
                                                 bg=styles.BG_HEADER))
        # Главная галочка только подтверждает; показываем лишь при наличии изменений.
        self._table.removeCellWidget(0, 5)
        if pending:
            self._table.setCellWidget(0, 5, self._make_master_check())
        else:
            self._table.setItem(0, 5, self._cell("", styles.TEXT, Qt.AlignCenter,
                                                 bg=styles.BG_HEADER))
        self._table.setRowHeight(0, 32)

        for i, m in enumerate(ordered):
            row = i + 1
            target = result.assigned.get(m.id, 0)
            delta = target - m.current_chars

            is_dup = name_counts[m.name.casefold()] > 1
            name_text = f"⚠ {m.name}" if is_dup else m.name
            name_item = self._cell(name_text, styles.RED if is_dup else styles.TEXT,
                                   Qt.AlignLeft | Qt.AlignVCenter)
            if is_dup:
                name_item.setToolTip("Duplicate name — pilot added twice")
            self._table.setItem(row, 0, name_item)

            # Max со степпером −/+ (исправление ошибки ввода командиром).
            self._table.setCellWidget(row, 1, self._make_stepper(
                m.max_chars, styles.TEXT_DIM,
                on_minus=lambda mid=m.id: self._adjust_max(mid, -1),
                on_plus=lambda mid=m.id: self._adjust_max(mid, +1),
                minus_enabled=m.max_chars > 1, plus_enabled=m.max_chars < 99))

            # In Fleet — жирным.
            self._table.setItem(row, 2, self._cell(
                str(m.current_chars), styles.TEXT, Qt.AlignCenter, bold=True))

            # Sponge («плюшки») со степпером −/+; − выключен при 0,
            # + блокируется при заполненном флоте (ошибка в _adjust_sponge).
            self._table.setCellWidget(row, 3, self._make_stepper(
                m.sponge, styles.AMBER,
                on_minus=lambda mid=m.id: self._adjust_sponge(mid, -1),
                on_plus=lambda mid=m.id: self._adjust_sponge(mid, +1),
                minus_enabled=m.sponge > 0, plus_enabled=True))

            # UP/DOWN: команда по обычным персонажам (+ добавить / − убрать) и,
            # отдельным янтарным числом, сколько убрать плюшек у пилота.
            if delta > 0:
                cmd_text, cmd_color = f"+{delta}", styles.GREEN
            elif delta < 0:
                cmd_text, cmd_color = f"−{abs(delta)}", styles.RED
            else:
                cmd_text, cmd_color = "—", styles.TEXT_DIM
            sponge_remove = m.sponge - sponge_keep.get(m.id, 0)
            self._table.setCellWidget(row, 4, self._make_updown(cmd_text, cmd_color, sponge_remove))

            # Чекбокс подтверждения (отмечен, когда «In Fleet» == цель)
            self._table.setCellWidget(row, 5, self._make_check(m.id, delta == 0 and target > 0))

            # Кнопка удаления пилота из флота
            self._table.setCellWidget(row, 6, self._make_delete(m.id, m.name))

            self._table.setRowHeight(row, 38)

        # Кэшируем состав флота при каждом обновлении (= при каждом изменении).
        self._persist_fleet()

    # ── Слоты / плюшки ───────────────────────────────────────────────────────────
    def _fleet_used(self) -> int:
        """Занятые слоты флота: реальные окна + плюшки."""
        return sum(m.current_chars + m.sponge for m in self._members)

    def _adjust_max(self, member_id: str, delta: int):
        m = self._member(member_id)
        if m is not None:
            m.max_chars = max(1, min(99, m.max_chars + delta))
        self._refresh()

    def _sponge_metrics(self, result) -> tuple[int, int, int]:
        """(capacity, sponge_total, free) — слоты под плюшки vs цели игроков.

        capacity = лимит − суммарная цель реальных игроков (сколько слотов им
        НЕ нужно). free = capacity − уже выставленные плюшки (может быть < 0,
        если игрокам не хватает мест — плюшки надо убирать).
        """
        sponge_total = sum(m.sponge for m in self._members)
        capacity = max(0, self._fleet_limit - result.total_assigned)
        return capacity, sponge_total, capacity - sponge_total

    def _adjust_sponge(self, member_id: str, delta: int):
        # Добавление плюшки запрещено, если свободных слотов под плюшки нет.
        if delta > 0:
            result = compute_distribution(self._members, fleet_limit=self._fleet_limit)
            if self._sponge_metrics(result)[2] <= 0:
                QMessageBox.warning(
                    self, "Fleet is full",
                    "No room for sponges\nМест под плюшки нет",
                )
                return
        m = self._member(member_id)
        if m is not None:
            m.sponge = max(0, m.sponge + delta)
        self._refresh()

    def _make_updown(self, char_text: str, char_color: str, sponge_remove: int) -> QWidget:
        """UP/DOWN: команда по персонажам + (если есть) янтарное «−N» по плюшкам."""
        html = f'<span style="color:{char_color};">{char_text}</span>'
        if sponge_remove > 0:
            html += f' <span style="color:{styles.AMBER};">−{sponge_remove}</span>'
        lbl = QLabel(html)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def _make_stepper(self, value: int, color: str, on_minus, on_plus,
                      minus_enabled: bool, plus_enabled: bool) -> QWidget:
        """Ячейка вида  [−] число [+]  с кнопками по бокам."""
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(5)
        lay.setAlignment(Qt.AlignCenter)

        minus = QPushButton("−")
        minus.setObjectName("stepMinus")
        minus.setFixedSize(22, 22)
        minus.setEnabled(minus_enabled)
        minus.setCursor(Qt.PointingHandCursor)
        minus.clicked.connect(lambda _c: on_minus())

        num = QLabel(str(value))
        num.setAlignment(Qt.AlignCenter)
        num.setMinimumWidth(20)
        num.setStyleSheet(f"color:{color}; font-weight:bold;")

        plus = QPushButton("+")
        plus.setObjectName("stepPlus")
        plus.setFixedSize(22, 22)
        plus.setEnabled(plus_enabled)
        plus.setCursor(Qt.PointingHandCursor)
        plus.clicked.connect(lambda _c: on_plus())

        lay.addWidget(minus)
        lay.addWidget(num)
        lay.addWidget(plus)
        return cont

    def _make_delete(self, member_id: str, name: str) -> QWidget:
        """Кнопка удаления, отцентрированная в ячейке (надёжная отрисовка)."""
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        btn = QPushButton("✕")
        btn.setObjectName("del")
        btn.setToolTip(f"Remove {name} from the fleet")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(26, 26)
        btn.clicked.connect(lambda _c, mid=member_id: self._remove(mid))
        lay.addWidget(btn)
        return cont

    def _make_master_check(self) -> QWidget:
        """Главная галочка в строке-итоге — подтверждает изменения у всех пилотов."""
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        cb = QCheckBox()
        cb.setToolTip("Confirm changes for all pilots at once")
        cb.clicked.connect(lambda _c: self._on_confirm_all())
        lay.addWidget(cb)
        return cont

    def _make_check(self, member_id: str, checked: bool) -> QWidget:
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        cb = QCheckBox()
        cb.setChecked(checked)
        cb.setToolTip("Confirm the pilot changed their window count")
        cb.clicked.connect(lambda c, mid=member_id: self._on_confirm(mid, c))
        lay.addWidget(cb)
        return cont

    @staticmethod
    def _cell(text: str, color: str, align, bold: bool = False,
              bg: str | None = None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        item.setTextAlignment(align)
        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
        if bg:
            item.setBackground(QColor(bg))
        return item
