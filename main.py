import sys
import os
import re
import json
import time
import math
import socket
import shutil
import mimetypes
import subprocess

from collections import deque
from datetime import datetime

import psutil

from PySide6.QtCore import (
    Qt,
    QTimer,
    QProcess,
    QRectF,
    QPointF
)

from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
    QPixmap,
    QPainterPath,
    QLinearGradient,
    QRadialGradient
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QLineEdit,
    QTextEdit,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QCheckBox
)


# =========================================================
# LCARS COLORS
# =========================================================

ORANGE = "#F59A67"
PEACH = "#F7C99A"
PURPLE = "#C89AF7"
BLUE = "#7AA7FF"
CYAN = "#8FD3FF"
PINK = "#D16B9C"
RED = "#E46D70"
GREEN = "#77D6A0"
YELLOW = "#E8D879"

THEMES = {
    "COMMAND GOLD": ORANGE,
    "SCIENCE BLUE": CYAN,
    "TACTICAL CRIMSON": RED,
    "DEEP SPACE PURPLE": PURPLE
}


# =========================================================
# BUTTON
# =========================================================

def lcars_button(text, color=ORANGE):

    button = QPushButton(text)

    button.setMinimumHeight(54)

    button.setCursor(
        Qt.PointingHandCursor
    )

    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: black;
            border: none;
            border-radius: 25px;
            padding: 11px 18px;
            font-size: 17px;
            font-weight: 900;
            text-align: right;
        }}

        QPushButton:hover {{
            border: 3px solid white;
        }}

        QPushButton:pressed {{
            background-color: white;
        }}

        QPushButton[active="true"] {{
            border: 4px solid white;
        }}

        QPushButton:disabled {{
            background-color: #444444;
            color: #888888;
        }}
    """)

    return button


# =========================================================
# LIVE GRAPH
# =========================================================

class LiveGraph(QWidget):

    def __init__(
        self,
        title,
        color
    ):

        super().__init__()

        self.title = title
        self.color = QColor(color)

        self.values = deque(
            [0.0] * 60,
            maxlen=60
        )

        self.setMinimumHeight(
            145
        )

    def add_value(
        self,
        value
    ):

        self.values.append(
            max(
                0,
                float(value)
            )
        )

        self.update()

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        w = self.width()
        h = self.height()

        painter.fillRect(
            self.rect(),
            QColor(
                6,
                7,
                10
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    40,
                    45,
                    55
                ),
                1
            )
        )

        for i in range(
            1,
            5
        ):

            y = (
                h
                * i
                / 5
            )

            painter.drawLine(
                QPointF(
                    0,
                    y
                ),
                QPointF(
                    w,
                    y
                )
            )

        painter.setPen(
            self.color
        )

        painter.setFont(
            QFont(
                "Arial",
                10,
                QFont.Bold
            )
        )

        painter.drawText(
            12,
            22,
            self.title
        )

        values = list(
            self.values
        )

        maximum = max(
            100.0,
            max(values)
            if values
            else 100.0
        )

        path = QPainterPath()

        graph_top = 35
        graph_height = (
            h - 48
        )

        for index, value in enumerate(
            values
        ):

            x = (
                index
                / max(
                    1,
                    len(values) - 1
                )
                * w
            )

            y = (
                graph_top
                + graph_height
                - (
                    min(
                        value,
                        maximum
                    )
                    / maximum
                    * graph_height
                )
            )

            if index == 0:

                path.moveTo(
                    x,
                    y
                )

            else:

                path.lineTo(
                    x,
                    y
                )

        painter.setPen(
            QPen(
                self.color,
                3
            )
        )

        painter.drawPath(
            path
        )

        if values:

            painter.setPen(
                QColor(
                    230,
                    230,
                    240
                )
            )

            painter.setFont(
                QFont(
                    "Arial",
                    14,
                    QFont.Bold
                )
            )

            painter.drawText(
                QRectF(
                    w - 110,
                    7,
                    95,
                    25
                ),
                Qt.AlignRight,
                f"{values[-1]:.1f}"
            )


# =========================================================
# STARSHIP SENSOR DISPLAY
# =========================================================

class StarshipDisplay(QWidget):

    def __init__(self):

        super().__init__()

        self.angle = 0.0
        self.pulse = 0.0
        self.animated = True

        self.contacts = []
        self.last_scan_text = "AWAITING SENSOR DATA"

        self.stars = [
            (0.07, 0.20),
            (0.15, 0.66),
            (0.22, 0.35),
            (0.32, 0.78),
            (0.42, 0.16),
            (0.53, 0.70),
            (0.64, 0.27),
            (0.75, 0.80),
            (0.87, 0.38),
            (0.94, 0.68),
        ]

        self.accent = QColor(
            CYAN
        )

        self.setMinimumHeight(
            300
        )

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(
            40
        )

    # =====================================================
    # PUBLIC SENSOR CONTROLS
    # =====================================================

    def set_accent(
        self,
        color
    ):

        self.accent = QColor(
            color
        )

        self.update()

    def set_animation(
        self,
        enabled
    ):

        self.animated = enabled

    def set_contacts(
        self,
        contacts
    ):

        self.contacts = contacts[:24]

        self.last_scan_text = (
            datetime.now()
            .strftime(
                "SCAN %H:%M:%S"
            )
        )

        self.update()

    def animate(self):

        if self.animated:

            self.angle = (
                self.angle
                + 2.0
            ) % 360

            self.pulse += 0.08

            self.update()

    # =====================================================
    # CONTACT COLORS
    # =====================================================

    def contact_color(
        self,
        kind
    ):

        colors = {
            "connection":
                QColor(CYAN),

            "neighbor":
                QColor(PURPLE),

            "gateway":
                QColor(PEACH),

            "ping":
                QColor(GREEN),

            "alert":
                QColor(RED),
        }

        return colors.get(
            kind,
            QColor(CYAN)
        )

    # =====================================================
    # CONTACT POSITION
    # =====================================================

    def contact_position(
        self,
        contact,
        index,
        cx,
        cy,
        radius
    ):

        label = contact.get(
            "label",
            "UNKNOWN"
        )

        kind = contact.get(
            "kind",
            "connection"
        )

        seed = sum(
            (
                position + 1
            )
            * ord(character)

            for position, character
            in enumerate(label)
        )

        angle = (
            seed * 1.71
            + index * 31
        ) % 360

        if kind == "ping":

            radial_factor = 0.30

        elif kind == "alert":

            radial_factor = 0.40

        elif kind == "gateway":

            radial_factor = 0.56

        elif kind == "neighbor":

            radial_factor = (
                0.63
                + (
                    seed % 23
                ) / 100
            )

        else:

            radial_factor = (
                0.48
                + (
                    seed % 35
                ) / 100
            )

        radians = math.radians(
            angle
        )

        x = (
            cx
            + math.cos(
                radians
            )
            * radius
            * radial_factor
        )

        y = (
            cy
            + math.sin(
                radians
            )
            * radius
            * radial_factor
        )

        return (
            x,
            y
        )

    # =====================================================
    # CONTACT DRAWING
    # =====================================================

    def draw_contact(
        self,
        painter,
        contact,
        index,
        cx,
        cy,
        radius
    ):

        kind = contact.get(
            "kind",
            "connection"
        )

        label = contact.get(
            "label",
            "UNKNOWN"
        )

        x, y = self.contact_position(
            contact,
            index,
            cx,
            cy,
            radius
        )

        color = self.contact_color(
            kind
        )

        pulse = (
            0.5
            + 0.5
            * math.sin(
                self.pulse
                + index * 0.75
            )
        )

        # Outer glow

        glow = QColor(
            color
        )

        glow.setAlpha(
            int(
                35
                + pulse * 35
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            glow
        )

        painter.drawEllipse(
            QPointF(
                x,
                y
            ),
            11 + pulse * 3,
            11 + pulse * 3
        )

        # Main contact

        solid = QColor(
            color
        )

        solid.setAlpha(
            235
        )

        painter.setBrush(
            solid
        )

        painter.drawEllipse(
            QPointF(
                x,
                y
            ),
            4.5,
            4.5
        )

        # Alert contact gets targeting box

        if kind == "alert":

            painter.setBrush(
                Qt.NoBrush
            )

            painter.setPen(
                QPen(
                    QColor(RED),
                    2
                )
            )

            painter.drawRect(
                QRectF(
                    x - 11,
                    y - 11,
                    22,
                    22
                )
            )

        # Ping target gets target circles

        if kind == "ping":

            painter.setBrush(
                Qt.NoBrush
            )

            painter.setPen(
                QPen(
                    QColor(GREEN),
                    2
                )
            )

            painter.drawEllipse(
                QPointF(
                    x,
                    y
                ),
                13,
                13
            )

        # Labels - only enough to stay readable

        if index < 12:

            painter.setPen(
                color
            )

            painter.setFont(
                QFont(
                    "Consolas",
                    7,
                    QFont.Bold
                )
            )

            display = label

            if len(display) > 21:

                display = (
                    display[:18]
                    + "..."
                )

            painter.drawText(
                QRectF(
                    x + 8,
                    y - 10,
                    150,
                    20
                ),
                Qt.AlignLeft
                | Qt.AlignVCenter,
                display
            )

    # =====================================================
    # PAINT
    # =====================================================

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        width = self.width()
        height = self.height()

        # Background

        background = QRadialGradient(
            width * 0.52,
            height * 0.53,
            max(
                width,
                height
            )
        )

        background.setColorAt(
            0,
            QColor(
                8,
                18,
                27
            )
        )

        background.setColorAt(
            1,
            QColor(
                2,
                4,
                8
            )
        )

        painter.fillRect(
            self.rect(),
            background
        )

        # Stars

        painter.setPen(
            Qt.NoPen
        )

        for x_ratio, y_ratio in self.stars:

            painter.setBrush(
                QColor(
                    215,
                    230,
                    255,
                    145
                )
            )

            painter.drawEllipse(
                QPointF(
                    x_ratio * width,
                    y_ratio * height
                ),
                2,
                2
            )

        cx = width * 0.50
        cy = height * 0.54

        radius = (
            min(
                width,
                height
            )
            * 0.36
        )

        # ---------------------------------------------
        # SENSOR RANGE RINGS
        # ---------------------------------------------

        painter.setBrush(
            Qt.NoBrush
        )

        for scale, alpha in [
            (1.00, 95),
            (0.75, 72),
            (0.50, 55),
            (0.25, 38)
        ]:

            ring_color = QColor(
                self.accent
            )

            ring_color.setAlpha(
                alpha
            )

            painter.setPen(
                QPen(
                    ring_color,
                    1.5
                )
            )

            painter.drawEllipse(
                QPointF(
                    cx,
                    cy
                ),
                radius * scale,
                radius * scale
            )

        # ---------------------------------------------
        # SENSOR CROSS GRID
        # ---------------------------------------------

        grid_color = QColor(
            self.accent
        )

        grid_color.setAlpha(
            45
        )

        painter.setPen(
            QPen(
                grid_color,
                1
            )
        )

        painter.drawLine(
            QPointF(
                cx - radius,
                cy
            ),
            QPointF(
                cx + radius,
                cy
            )
        )

        painter.drawLine(
            QPointF(
                cx,
                cy - radius
            ),
            QPointF(
                cx,
                cy + radius
            )
        )

        # Diagonal tactical grid

        diagonal = radius * 0.70

        painter.drawLine(
            QPointF(
                cx - diagonal,
                cy - diagonal
            ),
            QPointF(
                cx + diagonal,
                cy + diagonal
            )
        )

        painter.drawLine(
            QPointF(
                cx + diagonal,
                cy - diagonal
            ),
            QPointF(
                cx - diagonal,
                cy + diagonal
            )
        )

        # ---------------------------------------------
        # ROTATING SENSOR SWEEP
        # ---------------------------------------------

        painter.save()

        painter.translate(
            cx,
            cy
        )

        painter.rotate(
            self.angle
        )

        sweep_color = QColor(
            self.accent
        )

        sweep_color.setAlpha(
            190
        )

        painter.setPen(
            QPen(
                sweep_color,
                3
            )
        )

        painter.drawLine(
            QPointF(
                0,
                0
            ),
            QPointF(
                radius,
                0
            )
        )

        painter.restore()

        # ---------------------------------------------
        # CENTER STARSHIP
        # ---------------------------------------------

        painter.save()

        painter.translate(
            cx,
            cy
        )

        ship_color = QColor(
            CYAN
        )

        painter.setPen(
            QPen(
                ship_color,
                2
            )
        )

        painter.setBrush(
            QColor(
                95,
                165,
                205,
                32
            )
        )

        # Saucer

        painter.drawEllipse(
            QRectF(
                -42,
                -26,
                84,
                52
            )
        )

        # Bridge

        painter.drawEllipse(
            QRectF(
                -7,
                -6,
                14,
                12
            )
        )

        # Neck

        painter.drawRoundedRect(
            QRectF(
                -10,
                20,
                20,
                31
            ),
            7,
            7
        )

        # Engineering hull

        painter.drawEllipse(
            QRectF(
                -18,
                44,
                36,
                58
            )
        )

        # Pylons

        painter.drawLine(
            QPointF(
                -12,
                62
            ),
            QPointF(
                -43,
                75
            )
        )

        painter.drawLine(
            QPointF(
                12,
                62
            ),
            QPointF(
                43,
                75
            )
        )

        # Nacelles

        painter.drawRoundedRect(
            QRectF(
                -55,
                67,
                17,
                58
            ),
            7,
            7
        )

        painter.drawRoundedRect(
            QRectF(
                38,
                67,
                17,
                58
            ),
            7,
            7
        )

        engine_alpha = int(
            150
            + 70
            * (
                0.5
                + 0.5
                * math.sin(
                    self.pulse
                )
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                100,
                225,
                255,
                engine_alpha
            )
        )

        painter.drawRoundedRect(
            QRectF(
                -51,
                77,
                9,
                38
            ),
            4,
            4
        )

        painter.drawRoundedRect(
            QRectF(
                42,
                77,
                9,
                38
            ),
            4,
            4
        )

        painter.restore()

        # ---------------------------------------------
        # REAL SENSOR CONTACTS
        # ---------------------------------------------

        for index, contact in enumerate(
            self.contacts
        ):

            self.draw_contact(
                painter,
                contact,
                index,
                cx,
                cy,
                radius
            )

        # ---------------------------------------------
        # TITLE
        # ---------------------------------------------

        painter.setPen(
            QColor(
                PEACH
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                12,
                9,
                width - 24,
                24
            ),
            Qt.AlignLeft,
            "NX-47 // LIVE SYSTEM SENSOR ARRAY"
        )

        # ---------------------------------------------
        # LEGEND
        # ---------------------------------------------

        legend_x = (
            width - 190
        )

        legend_y = 42

        legend_items = [
            (
                CYAN,
                "ACTIVE CONNECTION"
            ),
            (
                PURPLE,
                "KNOWN NEIGHBOR"
            ),
            (
                PEACH,
                "GATEWAY"
            ),
            (
                GREEN,
                "PING TARGET"
            ),
            (
                RED,
                "SYSTEM ALERT"
            ),
        ]

        painter.setFont(
            QFont(
                "Consolas",
                7,
                QFont.Bold
            )
        )

        for index, (
            color,
            text
        ) in enumerate(
            legend_items
        ):

            y = (
                legend_y
                + index * 18
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor(color)
            )

            painter.drawEllipse(
                QPointF(
                    legend_x,
                    y + 5
                ),
                4,
                4
            )

            painter.setPen(
                QColor(color)
            )

            painter.drawText(
                QRectF(
                    legend_x + 10,
                    y - 3,
                    165,
                    16
                ),
                Qt.AlignLeft
                | Qt.AlignVCenter,
                text
            )

        # ---------------------------------------------
        # CONTACT COUNTERS
        # ---------------------------------------------

        counts = {
            "connection": 0,
            "neighbor": 0,
            "gateway": 0,
            "ping": 0,
            "alert": 0,
        }

        for contact in self.contacts:

            kind = contact.get(
                "kind"
            )

            if kind in counts:

                counts[kind] += 1

        painter.setPen(
            QColor(
                CYAN
            )
        )

        painter.setFont(
            QFont(
                "Consolas",
                8
            )
        )

        count_text = (
            f"CONN {counts['connection']:02d}  //  "
            f"NEIGH {counts['neighbor']:02d}  //  "
            f"ALERT {counts['alert']:02d}"
        )

        painter.drawText(
            QRectF(
                12,
                height - 42,
                width - 24,
                16
            ),
            Qt.AlignLeft,
            count_text
        )

        painter.setPen(
            QColor(
                125,
                140,
                160
            )
        )

        painter.drawText(
            QRectF(
                12,
                height - 24,
                width - 24,
                16
            ),
            Qt.AlignLeft,
            self.last_scan_text
            + " // REAL FEDORA TELEMETRY"
        )


# =========================================================
# MAIN DESKTOP
# =========================================================

class LCARS(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "LCARS Fedora Desktop"
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.config_dir = (
            os.path.expanduser(
                "~/.config/lcars-shell"
            )
        )

        self.settings_file = (
            os.path.join(
                self.config_dir,
                "settings.json"
            )
        )

        os.makedirs(
            self.config_dir,
            exist_ok=True
        )

        self.settings = (
            self.load_settings()
        )

        self.current_directory = (
            os.path.expanduser("~")
        )

        self.selected_file = None

        self.sensor_ping_target = None
        self.last_sensor_scan = 0.0

        self.accent = THEMES.get(
            self.settings.get(
                "theme",
                "COMMAND GOLD"
            ),
            ORANGE
        )

        self.animations_enabled = (
            self.settings.get(
                "animations",
                True
            )
        )

        self.previous_net = (
            psutil.net_io_counters()
        )

        self.previous_net_time = (
            time.time()
        )

        self.net_speed = 0.0

        self.nav_buttons = []

        self.setup_styles()

        self.build_interface()

        self.setup_processes()

        self.setup_timers()

        self.load_directory(
            self.current_directory
        )

        self.show_page(
            0,
            self.home_button
        )

        self.update_system()

        self.notify(
            "LCARS CONTROL ENVIRONMENT ONLINE"
        )

    # =====================================================
    # SETTINGS STORAGE
    # =====================================================

    def load_settings(self):

        try:

            with open(
                self.settings_file,
                "r"
            ) as file:

                return json.load(
                    file
                )

        except Exception:

            return {
                "theme":
                "COMMAND GOLD",

                "animations":
                True
            }

    def save_settings(self):

        try:

            with open(
                self.settings_file,
                "w"
            ) as file:

                json.dump(
                    self.settings,
                    file,
                    indent=2
                )

        except Exception:
            pass

    # =====================================================
    # GLOBAL STYLE
    # =====================================================

    def setup_styles(self):

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #F2F2F2;
                font-family: Arial;
            }

            QLabel#title {
                color: #F7C99A;
                font-size: 29px;
                font-weight: 900;
            }

            QLabel#subtitle {
                color: #8FD3FF;
                font-size: 12px;
                font-weight: 700;
            }

            QLabel#pageTitle {
                color: #F7C99A;
                font-size: 29px;
                font-weight: 900;
            }

            QLabel#section {
                color: #C89AF7;
                font-size: 14px;
                font-weight: 900;
            }

            QLabel#path {
                color: #8FD3FF;
                font-size: 14px;
                padding: 4px;
            }

            QFrame#topBar {
                background-color: #08090D;
                border: 2px solid #F59A67;
                border-radius: 24px;
            }

            QFrame#navRail {
                background-color: #06070A;
                border: 2px solid #F59A67;
                border-radius: 28px;
            }

            QFrame#mainDisplay {
                background-color: #040508;
                border: 3px solid #C89AF7;
                border-radius: 28px;
            }

            QFrame#card {
                background-color: #080A0F;
                border: 2px solid #303642;
                border-radius: 18px;
            }

            QFrame#footer {
                background-color: #08090D;
                border-radius: 18px;
            }

            QLineEdit {
                background-color: #07090D;
                color: white;
                border: 2px solid #C89AF7;
                border-radius: 14px;
                padding: 12px;
                font-size: 17px;
            }

            QTextEdit {
                background-color: #05070A;
                color: #8FD3FF;
                border: 2px solid #7AA7FF;
                border-radius: 14px;
                padding: 10px;
                font-family: monospace;
                font-size: 14px;
            }

            QListWidget {
                background-color: #05070A;
                color: white;
                border: 2px solid #F59A67;
                border-radius: 15px;
                font-size: 16px;
                padding: 6px;
            }

            QListWidget::item {
                padding: 8px;
            }

            QListWidget::item:selected {
                background-color: #C89AF7;
                color: black;
            }

            QTableWidget {
                background-color: #05070A;
                color: white;
                border: 2px solid #7AA7FF;
                border-radius: 14px;
                gridline-color: #202530;
                font-size: 13px;
            }

            QHeaderView::section {
                background-color: #C89AF7;
                color: black;
                padding: 8px;
                border: none;
                font-weight: 900;
            }

            QComboBox {
                background-color: #10131A;
                color: white;
                border: 2px solid #C89AF7;
                border-radius: 12px;
                padding: 10px;
                font-size: 15px;
            }

            QCheckBox {
                color: white;
                font-size: 16px;
                padding: 10px;
            }
        """)

    # =====================================================
    # INTERFACE
    # =====================================================

    def build_interface(self):

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            14,
            14,
            14,
            14
        )

        root.setSpacing(
            9
        )

        # -------------------------------------------------
        # TOP BAR
        # -------------------------------------------------

        top_frame = QFrame()

        top_frame.setObjectName(
            "topBar"
        )

        top = QHBoxLayout(
            top_frame
        )

        top.setContentsMargins(
            18,
            9,
            18,
            9
        )

        brand_layout = QVBoxLayout()

        title = QLabel(
            "LCARS // FEDORA 47-A"
        )

        title.setObjectName(
            "title"
        )

        subtitle = QLabel(
            "FEDERATION-INSPIRED UNIFIED CONTROL ENVIRONMENT"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        brand_layout.addWidget(
            title
        )

        brand_layout.addWidget(
            subtitle
        )

        top.addLayout(
            brand_layout
        )

        top.addStretch()

        self.top_cpu = (
            self.top_indicator(
                "CPU --",
                ORANGE
            )
        )

        self.top_ram = (
            self.top_indicator(
                "MEM --",
                PURPLE
            )
        )

        self.top_net = (
            self.top_indicator(
                "NET --",
                BLUE
            )
        )

        self.top_disk = (
            self.top_indicator(
                "DSK --",
                PEACH
            )
        )

        top.addWidget(
            self.top_cpu
        )

        top.addWidget(
            self.top_ram
        )

        top.addWidget(
            self.top_net
        )

        top.addWidget(
            self.top_disk
        )

        self.clock = QLabel()

        self.clock.setStyleSheet("""
            color: #F7C99A;
            font-size: 18px;
            font-weight: 900;
            padding-left: 10px;
        """)

        top.addWidget(
            self.clock
        )

        root.addWidget(
            top_frame
        )

        # -------------------------------------------------
        # BODY
        # -------------------------------------------------

        body = QHBoxLayout()

        body.setSpacing(
            10
        )

        # -------------------------------------------------
        # NAVIGATION
        # -------------------------------------------------

        nav_frame = QFrame()

        nav_frame.setObjectName(
            "navRail"
        )

        nav = QVBoxLayout(
            nav_frame
        )

        nav.setContentsMargins(
            10,
            12,
            10,
            12
        )

        nav.setSpacing(
            7
        )

        node_label = QLabel(
            "LCARS NODE 47"
        )

        node_label.setStyleSheet("""
            color: #F7C99A;
            font-size: 16px;
            font-weight: 900;
            padding: 6px;
        """)

        nav.addWidget(
            node_label
        )

        self.home_button = (
            lcars_button(
                "COMMAND",
                ORANGE
            )
        )

        self.system_button = (
            lcars_button(
                "SYSTEM",
                PEACH
            )
        )

        self.network_button = (
            lcars_button(
                "NETWORK",
                PURPLE
            )
        )

        self.files_button = (
            lcars_button(
                "FILES",
                BLUE
            )
        )

        self.apps_button = (
            lcars_button(
                "APPLICATIONS",
                CYAN
            )
        )

        self.process_button = (
            lcars_button(
                "PROCESSES",
                GREEN
            )
        )

        self.settings_button = (
            lcars_button(
                "SETTINGS",
                YELLOW
            )
        )

        self.power_button = (
            lcars_button(
                "POWER",
                RED
            )
        )

        self.nav_buttons = [
            self.home_button,
            self.system_button,
            self.network_button,
            self.files_button,
            self.apps_button,
            self.process_button,
            self.settings_button,
            self.power_button
        ]

        for button in self.nav_buttons:

            nav.addWidget(
                button
            )

        nav.addStretch()

        nav_footer = QLabel(
            "SUPER+1  COMMAND\n"
            "SUPER+ENTER  TERMINAL\n"
            "SUPER+SHIFT+ESC  LOGOUT"
        )

        nav_footer.setStyleSheet("""
            color: #727986;
            font-size: 10px;
            padding: 6px;
        """)

        nav.addWidget(
            nav_footer
        )

        body.addWidget(
            nav_frame,
            1
        )

        # -------------------------------------------------
        # MAIN DISPLAY
        # -------------------------------------------------

        self.display_frame = QFrame()

        self.display_frame.setObjectName(
            "mainDisplay"
        )

        display_layout = QVBoxLayout(
            self.display_frame
        )

        display_layout.setContentsMargins(
            16,
            16,
            16,
            16
        )

        self.pages = (
            QStackedWidget()
        )

        display_layout.addWidget(
            self.pages
        )

        body.addWidget(
            self.display_frame,
            5
        )

        root.addLayout(
            body,
            1
        )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        footer = QFrame()

        footer.setObjectName(
            "footer"
        )

        footer_layout = QHBoxLayout(
            footer
        )

        footer_layout.setContentsMargins(
            14,
            5,
            14,
            5
        )

        self.footer_status = QLabel(
            "SYSTEM INITIALIZED"
        )

        self.footer_status.setStyleSheet("""
            color: #8FD3FF;
            font-size: 11px;
            font-weight: 800;
        """)

        self.stardate_label = QLabel()

        self.stardate_label.setStyleSheet("""
            color: #C89AF7;
            font-size: 11px;
            font-weight: 800;
        """)

        footer_layout.addWidget(
            self.footer_status
        )

        footer_layout.addStretch()

        footer_layout.addWidget(
            self.stardate_label
        )

        root.addWidget(
            footer
        )

        # Pages

        self.build_command_page()
        self.build_system_page()
        self.build_network_page()
        self.build_files_page()
        self.build_apps_page()
        self.build_process_page()
        self.build_settings_page()
        self.build_power_page()

        # Navigation

        self.home_button.clicked.connect(
            lambda:
            self.show_page(
                0,
                self.home_button
            )
        )

        self.system_button.clicked.connect(
            lambda:
            self.show_page(
                1,
                self.system_button
            )
        )

        self.network_button.clicked.connect(
            lambda:
            self.show_page(
                2,
                self.network_button
            )
        )

        self.files_button.clicked.connect(
            self.open_files_page
        )

        self.apps_button.clicked.connect(
            lambda:
            self.show_page(
                4,
                self.apps_button
            )
        )

        self.process_button.clicked.connect(
            self.open_process_page
        )

        self.settings_button.clicked.connect(
            lambda:
            self.show_page(
                6,
                self.settings_button
            )
        )

        self.power_button.clicked.connect(
            lambda:
            self.show_page(
                7,
                self.power_button
            )
        )

    # =====================================================
    # SMALL UI HELPERS
    # =====================================================

    def top_indicator(
        self,
        text,
        color
    ):

        label = QLabel(
            text
        )

        label.setStyleSheet(
            f"""
            background-color: {color};
            color: black;
            border-radius: 13px;
            padding: 7px 11px;
            font-weight: 900;
            """
        )

        return label

    def card(
        self,
        title,
        value_widget,
        color=CYAN
    ):

        frame = QFrame()

        frame.setObjectName(
            "card"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            14,
            11,
            14,
            11
        )

        heading = QLabel(
            title
        )

        heading.setStyleSheet(
            f"""
            color: {color};
            font-size: 12px;
            font-weight: 900;
            """
        )

        value_widget.setStyleSheet("""
            color: white;
            font-size: 22px;
            font-weight: 900;
        """)

        layout.addWidget(
            heading
        )

        layout.addWidget(
            value_widget
        )

        return frame

    def page_title(
        self,
        title,
        subtitle
    ):

        container = QVBoxLayout()

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "pageTitle"
        )

        sub = QLabel(
            subtitle
        )

        sub.setStyleSheet("""
            color: #8FD3FF;
            font-size: 12px;
            font-weight: 700;
        """)

        container.addWidget(
            heading
        )

        container.addWidget(
            sub
        )

        return container

    # =====================================================
    # COMMAND PAGE
    # =====================================================

    def build_command_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "COMMAND CORE",
                "TACTICAL / NAVIGATION / SYSTEM TELEMETRY"
            )
        )

        top = QHBoxLayout()

        self.starship_display = (
            StarshipDisplay()
        )

        self.starship_display.set_animation(
            self.animations_enabled
        )

        self.starship_display.set_accent(
            self.accent
        )

        top.addWidget(
            self.starship_display,
            3
        )

        status_grid = QGridLayout()

        self.command_cpu = QLabel(
            "--"
        )

        self.command_ram = QLabel(
            "--"
        )

        self.command_disk = QLabel(
            "--"
        )

        self.command_network = QLabel(
            "--"
        )

        status_grid.addWidget(
            self.card(
                "PROCESSOR",
                self.command_cpu,
                ORANGE
            ),
            0,
            0
        )

        status_grid.addWidget(
            self.card(
                "MEMORY",
                self.command_ram,
                PURPLE
            ),
            0,
            1
        )

        status_grid.addWidget(
            self.card(
                "STORAGE",
                self.command_disk,
                PEACH
            ),
            1,
            0
        )

        status_grid.addWidget(
            self.card(
                "NETWORK",
                self.command_network,
                BLUE
            ),
            1,
            1
        )

        top.addLayout(
            status_grid,
            2
        )

        layout.addLayout(
            top
        )

        # Graphs

        graph_layout = QHBoxLayout()

        self.cpu_graph = LiveGraph(
            "CPU // %",
            ORANGE
        )

        self.ram_graph = LiveGraph(
            "MEMORY // %",
            PURPLE
        )

        self.net_graph = LiveGraph(
            "NETWORK // KB/S",
            CYAN
        )

        graph_layout.addWidget(
            self.cpu_graph
        )

        graph_layout.addWidget(
            self.ram_graph
        )

        graph_layout.addWidget(
            self.net_graph
        )

        layout.addLayout(
            graph_layout
        )

        lower = QHBoxLayout()

        # Crew stations

        crew_frame = QFrame()

        crew_frame.setObjectName(
            "card"
        )

        crew_layout = QVBoxLayout(
            crew_frame
        )

        crew_title = QLabel(
            "CREW / STATION MATRIX"
        )

        crew_title.setObjectName(
            "section"
        )

        crew_layout.addWidget(
            crew_title
        )

        for role, code, color in [
            (
                "COMMAND",
                "STATION 01 // READY",
                ORANGE
            ),
            (
                "SCIENCE",
                "STATION 02 // ACTIVE",
                BLUE
            ),
            (
                "ENGINEERING",
                "STATION 03 // NOMINAL",
                PURPLE
            ),
            (
                "OPERATIONS",
                "STATION 04 // ONLINE",
                GREEN
            )
        ]:

            row = QLabel(
                f"{role:<14} {code}"
            )

            row.setStyleSheet(
                f"""
                color: {color};
                font-family: monospace;
                font-size: 12px;
                padding: 4px;
                """
            )

            crew_layout.addWidget(
                row
            )

        lower.addWidget(
            crew_frame,
            2
        )

        # Alerts

        alert_frame = QFrame()

        alert_frame.setObjectName(
            "card"
        )

        alert_layout = QVBoxLayout(
            alert_frame
        )

        alert_title = QLabel(
            "LCARS EVENT STREAM"
        )

        alert_title.setObjectName(
            "section"
        )

        self.alert_list = (
            QListWidget()
        )

        alert_layout.addWidget(
            alert_title
        )

        alert_layout.addWidget(
            self.alert_list
        )

        lower.addWidget(
            alert_frame,
            3
        )

        layout.addLayout(
            lower
        )

        self.pages.addWidget(
            page
        )

    # =====================================================
    # SYSTEM PAGE
    # =====================================================

    def build_system_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "SYSTEM ENGINEERING",
                "LIVE FEDORA HARDWARE / OPERATING ENVIRONMENT"
            )
        )

        grid = QGridLayout()

        self.sys_cpu = QLabel()
        self.sys_ram = QLabel()
        self.sys_uptime = QLabel()
        self.sys_disk = QLabel()
        self.sys_cores = QLabel()
        self.sys_host = QLabel()
        self.sys_fedora = QLabel()
        self.sys_load = QLabel()

        cards = [
            (
                "CPU ACTIVITY",
                self.sys_cpu,
                ORANGE
            ),
            (
                "MEMORY",
                self.sys_ram,
                PURPLE
            ),
            (
                "UPTIME",
                self.sys_uptime,
                PEACH
            ),
            (
                "STORAGE",
                self.sys_disk,
                BLUE
            ),
            (
                "CPU CORES",
                self.sys_cores,
                CYAN
            ),
            (
                "HOST NODE",
                self.sys_host,
                GREEN
            ),
            (
                "OPERATING SYSTEM",
                self.sys_fedora,
                ORANGE
            ),
            (
                "LOAD AVERAGE",
                self.sys_load,
                PURPLE
            ),
        ]

        for index, (
            title,
            widget,
            color
        ) in enumerate(cards):

            grid.addWidget(
                self.card(
                    title,
                    widget,
                    color
                ),
                index // 2,
                index % 2
            )

        layout.addLayout(
            grid
        )

        layout.addStretch()

        self.pages.addWidget(
            page
        )

    # =====================================================
    # NETWORK PAGE
    # =====================================================

    def build_network_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "SUBSPACE NETWORK CONTROL",
                "FEDORA NETWORK INTERFACE / DIAGNOSTICS / WI-FI"
            )
        )

        self.network_status = QLabel()

        self.network_status.setStyleSheet("""
            color: #8FD3FF;
            font-family: monospace;
            font-size: 15px;
            padding: 8px;
        """)

        layout.addWidget(
            self.network_status
        )

        ping_row = QHBoxLayout()

        self.ping_target = (
            QLineEdit()
        )

        self.ping_target.setPlaceholderText(
            "Destination: google.com or 8.8.8.8"
        )

        self.ping_button = (
            lcars_button(
                "EXECUTE PING",
                PURPLE
            )
        )

        ping_row.addWidget(
            self.ping_target,
            4
        )

        ping_row.addWidget(
            self.ping_button,
            1
        )

        layout.addLayout(
            ping_row
        )

        self.ping_output = (
            QTextEdit()
        )

        self.ping_output.setReadOnly(
            True
        )

        self.ping_output.setPlaceholderText(
            "NETWORK RESPONSE STREAM"
        )

        layout.addWidget(
            self.ping_output,
            2
        )

        wifi_row = QHBoxLayout()

        wifi_title = QLabel(
            "WI-FI SENSOR SCAN"
        )

        wifi_title.setObjectName(
            "section"
        )

        self.wifi_button = (
            lcars_button(
                "SCAN WI-FI",
                BLUE
            )
        )

        wifi_row.addWidget(
            wifi_title
        )

        wifi_row.addStretch()

        wifi_row.addWidget(
            self.wifi_button
        )

        layout.addLayout(
            wifi_row
        )

        self.wifi_list = (
            QListWidget()
        )

        layout.addWidget(
            self.wifi_list,
            1
        )

        self.pages.addWidget(
            page
        )

    # =====================================================
    # FILES PAGE
    # =====================================================

    def build_files_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "DATA ARCHIVE",
                "FEDORA FILE ACCESS / VISUAL PREVIEW / METADATA"
            )
        )

        self.path_label = QLabel()

        self.path_label.setObjectName(
            "path"
        )

        layout.addWidget(
            self.path_label
        )

        body = QHBoxLayout()

        self.file_list = (
            QListWidget()
        )

        body.addWidget(
            self.file_list,
            2
        )

        preview_layout = QVBoxLayout()

        preview_title = QLabel(
            "VISUAL SENSOR PREVIEW"
        )

        preview_title.setObjectName(
            "section"
        )

        self.image_preview = QLabel(
            "NO DATA SELECTED"
        )

        self.image_preview.setAlignment(
            Qt.AlignCenter
        )

        self.image_preview.setMinimumSize(
            270,
            270
        )

        self.image_preview.setStyleSheet("""
            background-color: #05070A;
            border: 2px solid #F59A67;
            border-radius: 17px;
            font-size: 15px;
        """)

        preview_layout.addWidget(
            preview_title
        )

        preview_layout.addWidget(
            self.image_preview,
            1
        )

        body.addLayout(
            preview_layout,
            3
        )

        metadata = QFrame()

        metadata.setObjectName(
            "card"
        )

        metadata_layout = QVBoxLayout(
            metadata
        )

        metadata_title = QLabel(
            "DATA RECORD"
        )

        metadata_title.setObjectName(
            "section"
        )

        self.metadata_label = QLabel(
            "SELECT DATA OBJECT"
        )

        self.metadata_label.setWordWrap(
            True
        )

        self.metadata_label.setStyleSheet("""
            font-family: monospace;
            font-size: 13px;
            color: #DDE6F5;
        """)

        metadata_layout.addWidget(
            metadata_title
        )

        metadata_layout.addWidget(
            self.metadata_label
        )

        metadata_layout.addStretch()

        body.addWidget(
            metadata,
            2
        )

        layout.addLayout(
            body,
            1
        )

        buttons = QHBoxLayout()

        self.back_button = (
            lcars_button(
                "BACK",
                PURPLE
            )
        )

        self.open_button = (
            lcars_button(
                "OPEN",
                PEACH
            )
        )

        self.delete_button = (
            lcars_button(
                "DELETE",
                RED
            )
        )

        buttons.addWidget(
            self.back_button
        )

        buttons.addWidget(
            self.open_button
        )

        buttons.addWidget(
            self.delete_button
        )

        layout.addLayout(
            buttons
        )

        self.pages.addWidget(
            page
        )

    # =====================================================
    # APPLICATIONS PAGE
    # =====================================================

    def build_apps_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "APPLICATION MATRIX",
                "LAUNCH FEDORA APPLICATIONS FROM LCARS"
            )
        )

        grid = QGridLayout()

        apps = [
            (
                "FIREFOX",
                ORANGE,
                lambda:
                self.launch_external(
                    ["firefox"],
                    "FIREFOX"
                )
            ),
            (
                "TERMINAL",
                PURPLE,
                self.launch_terminal
            ),
            (
                "CALCULATOR",
                BLUE,
                lambda:
                self.launch_first(
                    [
                        "gnome-calculator",
                        "kcalc"
                    ],
                    "CALCULATOR"
                )
            ),
            (
                "TEXT EDITOR",
                CYAN,
                lambda:
                self.launch_first(
                    [
                        "gnome-text-editor",
                        "gedit",
                        "kate"
                    ],
                    "TEXT EDITOR"
                )
            ),
            (
                "FEDORA SETTINGS",
                PEACH,
                lambda:
                self.launch_first(
                    [
                        "gnome-control-center"
                    ],
                    "SETTINGS"
                )
            ),
            (
                "FILES",
                GREEN,
                lambda:
                self.show_page(
                    3,
                    self.files_button
                )
            ),
        ]

        for index, (
            name,
            color,
            callback
        ) in enumerate(apps):

            button = lcars_button(
                name,
                color
            )

            button.setMinimumHeight(
                95
            )

            button.clicked.connect(
                callback
            )

            grid.addWidget(
                button,
                index // 2,
                index % 2
            )

        layout.addSpacing(
            25
        )

        layout.addLayout(
            grid
        )

        hint = QLabel(
            "EXTERNAL APPLICATIONS OPEN ON SWAY WORKSPACE 2\n"
            "PRESS SUPER + 1 TO RETURN TO COMMAND CORE"
        )

        hint.setAlignment(
            Qt.AlignCenter
        )

        hint.setStyleSheet("""
            color: #8FD3FF;
            font-size: 13px;
            padding: 18px;
        """)

        layout.addWidget(
            hint
        )

        layout.addStretch()

        self.pages.addWidget(
            page
        )

    # =====================================================
    # PROCESS MANAGER
    # =====================================================

    def build_process_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "PROCESS CONTROL",
                "RUNNING FEDORA PROCESSES / RESOURCE USAGE"
            )
        )

        controls = QHBoxLayout()

        refresh = lcars_button(
            "REFRESH",
            BLUE
        )

        terminate = lcars_button(
            "END PROCESS",
            RED
        )

        refresh.clicked.connect(
            self.refresh_processes
        )

        terminate.clicked.connect(
            self.terminate_process
        )

        controls.addWidget(
            refresh
        )

        controls.addWidget(
            terminate
        )

        controls.addStretch()

        layout.addLayout(
            controls
        )

        self.process_table = (
            QTableWidget()
        )

        self.process_table.setColumnCount(
            4
        )

        self.process_table.setHorizontalHeaderLabels([
            "PID",
            "PROCESS",
            "CPU %",
            "MEM %"
        ])

        self.process_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )

        self.process_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.process_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.process_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        layout.addWidget(
            self.process_table
        )

        self.pages.addWidget(
            page
        )

    # =====================================================
    # SETTINGS PAGE
    # =====================================================

    def build_settings_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "LCARS CONFIGURATION",
                "VISUAL / ANIMATION / DESKTOP ENVIRONMENT SETTINGS"
            )
        )

        theme_frame = QFrame()

        theme_frame.setObjectName(
            "card"
        )

        theme_layout = QVBoxLayout(
            theme_frame
        )

        theme_label = QLabel(
            "INTERFACE MODE"
        )

        theme_label.setObjectName(
            "section"
        )

        self.theme_combo = (
            QComboBox()
        )

        self.theme_combo.addItems(
            list(
                THEMES.keys()
            )
        )

        self.theme_combo.setCurrentText(
            self.settings.get(
                "theme",
                "COMMAND GOLD"
            )
        )

        theme_layout.addWidget(
            theme_label
        )

        theme_layout.addWidget(
            self.theme_combo
        )

        layout.addWidget(
            theme_frame
        )

        animation_frame = QFrame()

        animation_frame.setObjectName(
            "card"
        )

        animation_layout = QVBoxLayout(
            animation_frame
        )

        animation_label = QLabel(
            "DISPLAY EFFECTS"
        )

        animation_label.setObjectName(
            "section"
        )

        self.animation_checkbox = (
            QCheckBox(
                "Enable animated sensor sweeps"
            )
        )

        self.animation_checkbox.setChecked(
            self.animations_enabled
        )

        animation_layout.addWidget(
            animation_label
        )

        animation_layout.addWidget(
            self.animation_checkbox
        )

        layout.addWidget(
            animation_frame
        )

        system_frame = QFrame()

        system_frame.setObjectName(
            "card"
        )

        system_layout = QVBoxLayout(
            system_frame
        )

        system_title = QLabel(
            "DESKTOP ARCHITECTURE"
        )

        system_title.setObjectName(
            "section"
        )

        system_description = QLabel(
            "FEDORA LINUX\n"
            "→ WAYLAND\n"
            "→ SWAY COMPOSITOR\n"
            "→ LCARS PYTHON / PYSIDE6 SHELL"
        )

        system_description.setStyleSheet("""
            color: #8FD3FF;
            font-family: monospace;
            font-size: 15px;
            padding: 12px;
        """)

        system_layout.addWidget(
            system_title
        )

        system_layout.addWidget(
            system_description
        )

        layout.addWidget(
            system_frame
        )

        layout.addStretch()

        self.theme_combo.currentTextChanged.connect(
            self.change_theme
        )

        self.animation_checkbox.toggled.connect(
            self.change_animation_setting
        )

        self.pages.addWidget(
            page
        )

    # =====================================================
    # POWER PAGE
    # =====================================================

    def build_power_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.addLayout(
            self.page_title(
                "SESSION CONTROL",
                "FEDORA POWER / LCARS SESSION MANAGEMENT"
            )
        )

        layout.addStretch()

        logout = lcars_button(
            "LOG OUT OF LCARS",
            PURPLE
        )

        restart = lcars_button(
            "RESTART FEDORA",
            ORANGE
        )

        shutdown = lcars_button(
            "SHUT DOWN FEDORA",
            RED
        )

        logout.setMinimumHeight(
            75
        )

        restart.setMinimumHeight(
            75
        )

        shutdown.setMinimumHeight(
            75
        )

        logout.clicked.connect(
            self.logout_lcars
        )

        restart.clicked.connect(
            self.restart_system
        )

        shutdown.clicked.connect(
            self.shutdown_system
        )

        layout.addWidget(
            logout
        )

        layout.addWidget(
            restart
        )

        layout.addWidget(
            shutdown
        )

        layout.addStretch()

        self.pages.addWidget(
            page
        )

    # =====================================================
    # PROCESS OBJECTS
    # =====================================================

    def setup_processes(self):

        self.ping_process = (
            QProcess(
                self
            )
        )

        self.ping_process.readyReadStandardOutput.connect(
            self.read_ping_output
        )

        self.ping_process.readyReadStandardError.connect(
            self.read_ping_error
        )

        self.ping_process.finished.connect(
            self.ping_finished
        )

        self.wifi_process = (
            QProcess(
                self
            )
        )

        self.wifi_process.finished.connect(
            self.wifi_scan_finished
        )

        self.ping_button.clicked.connect(
            self.start_ping
        )

        self.ping_target.returnPressed.connect(
            self.start_ping
        )

        self.wifi_button.clicked.connect(
            self.scan_wifi
        )

        self.file_list.itemClicked.connect(
            self.file_selected
        )

        self.file_list.itemDoubleClicked.connect(
            self.file_double_clicked
        )

        self.back_button.clicked.connect(
            self.go_back_directory
        )

        self.open_button.clicked.connect(
            self.open_selected_file
        )

        self.delete_button.clicked.connect(
            self.delete_selected_file
        )

    # =====================================================
    # TIMERS
    # =====================================================

    def setup_timers(self):

        self.system_timer = (
            QTimer(
                self
            )
        )

        self.system_timer.timeout.connect(
            self.update_system
        )

        self.system_timer.start(
            1000
        )

        self.process_timer = (
            QTimer(
                self
            )
        )

        self.process_timer.timeout.connect(
            self.refresh_process_if_visible
        )

        self.process_timer.start(
            5000
        )

    # =====================================================
    # NAVIGATION
    # =====================================================

    def show_page(
        self,
        index,
        active_button
    ):

        self.pages.setCurrentIndex(
            index
        )

        for button in self.nav_buttons:

            button.setProperty(
                "active",
                False
            )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

        active_button.setProperty(
            "active",
            True
        )

        active_button.style().unpolish(
            active_button
        )

        active_button.style().polish(
            active_button
        )

    # =====================================================
    # SYSTEM UPDATE
    # =====================================================

    def update_system(self):

        now = datetime.now()

        cpu = psutil.cpu_percent()

        ram = (
            psutil.virtual_memory()
        )

        disk = (
            psutil.disk_usage("/")
        )

        uptime = (
            time.time()
            - psutil.boot_time()
        )

        hours = int(
            uptime // 3600
        )

        minutes = int(
            (
                uptime % 3600
            )
            // 60
        )

        # Network speed

        current_net = (
            psutil.net_io_counters()
        )

        current_time = (
            time.time()
        )

        elapsed = max(
            0.01,
            current_time
            - self.previous_net_time
        )

        bytes_delta = (
            current_net.bytes_sent
            + current_net.bytes_recv
            - self.previous_net.bytes_sent
            - self.previous_net.bytes_recv
        )

        self.net_speed = (
            bytes_delta
            / elapsed
            / 1024
        )

        self.previous_net = (
            current_net
        )

        self.previous_net_time = (
            current_time
        )

        interface, ip = (
            self.get_network_info()
        )

        if (
            time.time()
            - self.last_sensor_scan
            >= 3.0
        ):

            contacts = (
                self.get_sensor_contacts(
                    cpu,
                    ram.percent,
                    disk.percent,
                    interface
                )
            )

            self.starship_display.set_contacts(
                contacts
            )

            self.last_sensor_scan = (
                time.time()
            )

        # Header

        self.clock.setText(
            now.strftime(
                "%H:%M:%S"
            )
        )

        self.stardate_label.setText(
            "STARDATE "
            + now.strftime(
                "%y.%j"
            )
            + " // "
            + now.strftime(
                "%Y-%m-%d"
            )
        )

        self.top_cpu.setText(
            f"CPU {cpu:.0f}%"
        )

        self.top_ram.setText(
            f"MEM {ram.percent:.0f}%"
        )

        self.top_net.setText(
            "NET ON"
            if interface
            else "NET OFF"
        )

        self.top_disk.setText(
            f"DSK {disk.percent:.0f}%"
        )

        # Command

        self.command_cpu.setText(
            f"{cpu:.1f}%"
        )

        self.command_ram.setText(
            f"{ram.percent:.1f}%"
        )

        self.command_disk.setText(
            f"{disk.percent:.1f}%"
        )

        self.command_network.setText(
            ip
            if ip
            else "OFFLINE"
        )

        self.cpu_graph.add_value(
            cpu
        )

        self.ram_graph.add_value(
            ram.percent
        )

        self.net_graph.add_value(
            self.net_speed
        )

        # System

        self.sys_cpu.setText(
            f"{cpu:.1f}%"
        )

        self.sys_ram.setText(
            f"{ram.percent:.1f}%"
        )

        self.sys_uptime.setText(
            f"{hours}H {minutes}M"
        )

        self.sys_disk.setText(
            f"{disk.percent:.1f}%"
        )

        self.sys_cores.setText(
            str(
                psutil.cpu_count()
            )
        )

        self.sys_host.setText(
            socket.gethostname()
        )

        try:

            with open(
                "/etc/fedora-release",
                "r"
            ) as file:

                fedora = (
                    file.read().strip()
                )

        except Exception:

            fedora = (
                "Fedora Linux"
            )

        self.sys_fedora.setText(
            fedora
        )

        try:

            load = os.getloadavg()

            self.sys_load.setText(
                f"{load[0]:.2f}"
            )

        except Exception:

            self.sys_load.setText(
                "N/A"
            )

        # Network page

        if interface:

            self.network_status.setText(
                f"""
LINK STATUS      ONLINE
INTERFACE        {interface}
LOCAL IP         {ip}
TRANSFER RATE    {self.net_speed:.1f} KB/S
"""
            )

        else:

            self.network_status.setText(
                "LINK STATUS      OFFLINE"
            )

    # =====================================================
    # NOTIFICATION SYSTEM
    # =====================================================

    def notify(
        self,
        message
    ):

        timestamp = (
            datetime.now()
            .strftime(
                "%H:%M:%S"
            )
        )

        item = QListWidgetItem(
            f"{timestamp}  //  {message}"
        )

        self.alert_list.insertItem(
            0,
            item
        )

        while (
            self.alert_list.count()
            > 8
        ):

            self.alert_list.takeItem(
                self.alert_list.count()
                - 1
            )

        self.footer_status.setText(
            message
        )

    # =====================================================
    # LIVE SENSOR CONTACTS
    # =====================================================

    def get_sensor_contacts(
        self,
        cpu,
        memory_percent,
        disk_percent,
        interface
    ):

        contacts = []
        seen = set()

        def add_contact(
            kind,
            label
        ):

            key = (
                kind,
                label
            )

            if key in seen:
                return

            seen.add(
                key
            )

            contacts.append({
                "kind": kind,
                "label": label
            })

        # ---------------------------------------------
        # Active remote connections
        # ---------------------------------------------

        connection_count = 0

        try:

            connections = (
                psutil.net_connections(
                    kind="inet"
                )
            )

            for connection in connections:

                if not connection.raddr:
                    continue

                try:

                    remote_ip = (
                        connection.raddr.ip
                    )

                    remote_port = (
                        connection.raddr.port
                    )

                except AttributeError:

                    remote_ip = (
                        connection.raddr[0]
                    )

                    remote_port = (
                        connection.raddr[1]
                    )

                if remote_ip in (
                    "127.0.0.1",
                    "::1",
                    "0.0.0.0"
                ):
                    continue

                label = (
                    f"{remote_ip}:{remote_port}"
                )

                add_contact(
                    "connection",
                    label
                )

                connection_count += 1

                if connection_count >= 10:
                    break

        except Exception:
            pass

        # ---------------------------------------------
        # Default gateway
        # ---------------------------------------------

        if shutil.which(
            "ip"
        ):

            try:

                result = subprocess.run(
                    [
                        "ip",
                        "route",
                        "show",
                        "default"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1
                )

                for line in (
                    result.stdout
                    .splitlines()
                ):

                    pieces = (
                        line.split()
                    )

                    if (
                        "via"
                        in pieces
                    ):

                        gateway_index = (
                            pieces.index(
                                "via"
                            )
                        )

                        if (
                            gateway_index + 1
                            < len(pieces)
                        ):

                            gateway = (
                                pieces[
                                    gateway_index
                                    + 1
                                ]
                            )

                            add_contact(
                                "gateway",
                                gateway
                            )

                            break

            except Exception:
                pass

        # ---------------------------------------------
        # Known local network neighbors
        #
        # This is Fedora's current neighbor/ARP cache.
        # It is NOT an aggressive LAN scan.
        # ---------------------------------------------

        neighbor_count = 0

        if shutil.which(
            "ip"
        ):

            try:

                result = subprocess.run(
                    [
                        "ip",
                        "neigh",
                        "show"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1
                )

                for line in (
                    result.stdout
                    .splitlines()
                ):

                    pieces = (
                        line.split()
                    )

                    if not pieces:
                        continue

                    upper_line = (
                        line.upper()
                    )

                    if (
                        "FAILED"
                        in upper_line
                        or "INCOMPLETE"
                        in upper_line
                    ):
                        continue

                    neighbor_ip = (
                        pieces[0]
                    )

                    add_contact(
                        "neighbor",
                        neighbor_ip
                    )

                    neighbor_count += 1

                    if neighbor_count >= 8:
                        break

            except Exception:
                pass

        # ---------------------------------------------
        # Last ping target
        # ---------------------------------------------

        if self.sensor_ping_target:

            add_contact(
                "ping",
                self.sensor_ping_target
            )

        # ---------------------------------------------
        # Real system alerts
        # ---------------------------------------------

        if cpu >= 85:

            add_contact(
                "alert",
                f"CPU HIGH {cpu:.0f}%"
            )

        if memory_percent >= 85:

            add_contact(
                "alert",
                f"MEM HIGH {memory_percent:.0f}%"
            )

        if disk_percent >= 90:

            add_contact(
                "alert",
                f"DISK HIGH {disk_percent:.0f}%"
            )

        if not interface:

            add_contact(
                "alert",
                "NETWORK OFFLINE"
            )

        return contacts


    # =====================================================
    # NETWORK
    # =====================================================

    def get_network_info(self):

        stats = (
            psutil.net_if_stats()
        )

        addresses = (
            psutil.net_if_addrs()
        )

        for interface, state in stats.items():

            if (
                state.isup
                and interface != "lo"
            ):

                for address in addresses.get(
                    interface,
                    []
                ):

                    if (
                        address.family
                        == socket.AF_INET
                        and address.address
                        != "127.0.0.1"
                    ):

                        return (
                            interface,
                            address.address
                        )

        return None, None

    def start_ping(self):

        target = (
            self.ping_target
            .text()
            .strip()
        )

        if not target:

            self.ping_output.setText(
                "ENTER A DESTINATION."
            )

            return

        if (
            not re.fullmatch(
                r"[A-Za-z0-9._:-]+",
                target
            )
            or target.startswith("-")
        ):

            self.ping_output.setText(
                "INVALID DESTINATION."
            )

            return

        self.ping_output.clear()

        self.ping_output.append(
            f"""
LCARS SUBSPACE DIAGNOSTIC
DESTINATION: {target}
--------------------------------
"""
        )

        self.ping_button.setEnabled(
            False
        )

        self.ping_button.setText(
            "PING ACTIVE"
        )

        self.sensor_ping_target = target

        self.notify(
            f"PING STARTED // {target}"
        )

        self.ping_process.start(
            "ping",
            [
                "-c",
                "4",
                "-W",
                "2",
                target
            ]
        )

    def read_ping_output(self):

        data = bytes(
            self.ping_process
            .readAllStandardOutput()
        ).decode(
            errors="replace"
        )

        self.ping_output.insertPlainText(
            data
        )

    def read_ping_error(self):

        data = bytes(
            self.ping_process
            .readAllStandardError()
        ).decode(
            errors="replace"
        )

        self.ping_output.insertPlainText(
            data
        )

    def ping_finished(
        self,
        *args
    ):

        self.ping_output.append(
            """
--------------------------------
NETWORK TEST COMPLETE
"""
        )

        self.ping_button.setEnabled(
            True
        )

        self.ping_button.setText(
            "EXECUTE PING"
        )

        self.notify(
            "NETWORK DIAGNOSTIC COMPLETE"
        )

    # =====================================================
    # WI-FI
    # =====================================================

    def scan_wifi(self):

        self.wifi_list.clear()

        if not shutil.which(
            "nmcli"
        ):

            self.wifi_list.addItem(
                "NetworkManager nmcli not available."
            )

            return

        self.wifi_button.setEnabled(
            False
        )

        self.wifi_button.setText(
            "SCANNING..."
        )

        self.wifi_process.start(
            "nmcli",
            [
                "-t",
                "-f",
                "SSID,SIGNAL,SECURITY",
                "device",
                "wifi",
                "list",
                "--rescan",
                "yes"
            ]
        )

    def wifi_scan_finished(
        self,
        *args
    ):

        data = bytes(
            self.wifi_process
            .readAllStandardOutput()
        ).decode(
            errors="replace"
        )

        self.wifi_button.setEnabled(
            True
        )

        self.wifi_button.setText(
            "SCAN WI-FI"
        )

        self.wifi_list.clear()

        lines = [
            line
            for line in data.splitlines()
            if line.strip()
        ]

        if not lines:

            self.wifi_list.addItem(
                "No Wi-Fi networks detected.\n"
                "A virtual machine may expose only a virtual Ethernet adapter."
            )

        else:

            for line in lines:

                self.wifi_list.addItem(
                    line.replace(
                        ":",
                        "   //   "
                    )
                )

        self.notify(
            "WI-FI SENSOR SCAN COMPLETE"
        )

    # =====================================================
    # FILES
    # =====================================================

    def open_files_page(self):

        self.show_page(
            3,
            self.files_button
        )

        self.load_directory(
            self.current_directory
        )

    def load_directory(
        self,
        directory
    ):

        self.current_directory = (
            directory
        )

        self.path_label.setText(
            "CURRENT ARCHIVE // "
            + directory
        )

        self.file_list.clear()

        self.selected_file = None

        self.image_preview.clear()

        self.image_preview.setText(
            "SELECT DATA OBJECT"
        )

        self.metadata_label.setText(
            "SELECT DATA OBJECT"
        )

        try:

            entries = (
                os.listdir(
                    directory
                )
            )

        except Exception as error:

            self.metadata_label.setText(
                str(
                    error
                )
            )

            return

        entries.sort(
            key=lambda item: (
                not os.path.isdir(
                    os.path.join(
                        directory,
                        item
                    )
                ),
                item.lower()
            )
        )

        for name in entries:

            if name.startswith(
                "."
            ):
                continue

            full_path = (
                os.path.join(
                    directory,
                    name
                )
            )

            display_name = (
                "▸ " + name
                if os.path.isdir(
                    full_path
                )
                else name
            )

            item = QListWidgetItem(
                display_name
            )

            item.setData(
                Qt.UserRole,
                full_path
            )

            self.file_list.addItem(
                item
            )

    def file_selected(
        self,
        item
    ):

        path = item.data(
            Qt.UserRole
        )

        self.selected_file = (
            path
        )

        self.show_metadata(
            path
        )

        self.show_preview(
            path
        )

    def file_double_clicked(
        self,
        item
    ):

        path = item.data(
            Qt.UserRole
        )

        if os.path.isdir(
            path
        ):

            self.load_directory(
                path
            )

        else:

            self.selected_file = (
                path
            )

            self.open_selected_file()

    def show_metadata(
        self,
        path
    ):

        try:

            stat = os.stat(
                path
            )

            modified = (
                datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            if os.path.isdir(
                path
            ):

                file_type = (
                    "DIRECTORY"
                )

                size_text = "--"

            else:

                mime, _ = (
                    mimetypes.guess_type(
                        path
                    )
                )

                file_type = (
                    mime
                    if mime
                    else "UNKNOWN"
                )

                size_text = (
                    self.format_size(
                        stat.st_size
                    )
                )

            self.metadata_label.setText(
                f"""
NAME
{os.path.basename(path)}

TYPE
{file_type}

SIZE
{size_text}

MODIFIED
{modified}

LOCATION
{os.path.dirname(path)}
"""
            )

        except Exception as error:

            self.metadata_label.setText(
                str(
                    error
                )
            )

    def show_preview(
        self,
        path
    ):

        self.image_preview.clear()

        if os.path.isdir(
            path
        ):

            self.image_preview.setText(
                "DIRECTORY"
            )

            return

        extensions = (
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".gif",
            ".webp"
        )

        if path.lower().endswith(
            extensions
        ):

            pixmap = QPixmap(
                path
            )

            if pixmap.isNull():

                self.image_preview.setText(
                    "PREVIEW UNAVAILABLE"
                )

                return

            self.image_preview.setPixmap(
                pixmap.scaled(
                    self.image_preview.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        else:

            self.image_preview.setText(
                "NO IMAGE PREVIEW\n\n"
                + os.path.basename(
                    path
                )
            )

    @staticmethod
    def format_size(
        size
    ):

        for unit in [
            "B",
            "KB",
            "MB",
            "GB",
            "TB"
        ]:

            if size < 1024:

                return (
                    f"{size:.1f} {unit}"
                )

            size /= 1024

        return (
            f"{size:.1f} PB"
        )

    def go_back_directory(self):

        parent = (
            os.path.dirname(
                self.current_directory
            )
        )

        if parent:

            self.load_directory(
                parent
            )

    def open_selected_file(self):

        if not self.selected_file:

            return

        if os.path.isdir(
            self.selected_file
        ):

            self.load_directory(
                self.selected_file
            )

            return

        self.switch_external_workspace()

        subprocess.Popen(
            [
                "xdg-open",
                self.selected_file
            ]
        )

        self.notify(
            "DATA OBJECT OPENED // "
            + os.path.basename(
                self.selected_file
            )
        )

    def delete_selected_file(self):

        if not self.selected_file:

            return

        if os.path.isdir(
            self.selected_file
        ):

            QMessageBox.information(
                self,
                "LCARS",
                "Directory deletion is disabled."
            )

            return

        filename = (
            os.path.basename(
                self.selected_file
            )
        )

        answer = (
            QMessageBox.question(
                self,
                "DELETE CONFIRMATION",
                f"""
DELETE DATA OBJECT?

{filename}

This operation permanently deletes the selected file.
""",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No
            )
        )

        if answer == (
            QMessageBox.Yes
        ):

            try:

                os.remove(
                    self.selected_file
                )

                self.notify(
                    "DATA OBJECT DELETED // "
                    + filename
                )

                self.selected_file = None

                self.load_directory(
                    self.current_directory
                )

            except Exception as error:

                QMessageBox.critical(
                    self,
                    "DELETE FAILED",
                    str(
                        error
                    )
                )

    # =====================================================
    # APPLICATION LAUNCHER
    # =====================================================

    def switch_external_workspace(self):

        if os.environ.get(
            "SWAYSOCK"
        ):

            subprocess.run(
                [
                    "swaymsg",
                    "workspace",
                    "number",
                    "2"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def launch_external(
        self,
        command,
        label
    ):

        executable = command[0]

        if not shutil.which(
            executable
        ):

            QMessageBox.warning(
                self,
                "APPLICATION",
                f"{label} is not installed."
            )

            return

        self.switch_external_workspace()

        subprocess.Popen(
            command
        )

        self.notify(
            f"APPLICATION LAUNCHED // {label}"
        )

    def launch_first(
        self,
        commands,
        label
    ):

        for command in commands:

            if shutil.which(
                command
            ):

                self.launch_external(
                    [command],
                    label
                )

                return

        QMessageBox.warning(
            self,
            "APPLICATION",
            f"{label} is not available."
        )

    def launch_terminal(self):

        commands = [
            "ptyxis",
            "kgx",
            "gnome-terminal",
            "foot",
            "konsole",
            "alacritty"
        ]

        self.launch_first(
            commands,
            "TERMINAL"
        )

    # =====================================================
    # PROCESSES
    # =====================================================

    def open_process_page(self):

        self.show_page(
            5,
            self.process_button
        )

        self.refresh_processes()

    def refresh_process_if_visible(self):

        if (
            self.pages.currentIndex()
            == 5
        ):

            self.refresh_processes()

    def refresh_processes(self):

        processes = []

        for process in (
            psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cpu_percent",
                    "memory_percent"
                ]
            )
        ):

            try:

                info = (
                    process.info
                )

                processes.append(
                    (
                        info["pid"],
                        info["name"]
                        or "unknown",
                        info["cpu_percent"]
                        or 0,
                        info["memory_percent"]
                        or 0
                    )
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):
                pass

        processes.sort(
            key=lambda row:
            row[3],
            reverse=True
        )

        processes = (
            processes[:80]
        )

        self.process_table.setRowCount(
            len(
                processes
            )
        )

        for row, (
            pid,
            name,
            cpu,
            memory
        ) in enumerate(processes):

            values = [
                str(
                    pid
                ),
                name,
                f"{cpu:.1f}",
                f"{memory:.1f}"
            ]

            for column, value in enumerate(
                values
            ):

                self.process_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        value
                    )
                )

    def terminate_process(self):

        row = (
            self.process_table
            .currentRow()
        )

        if row < 0:

            return

        pid_item = (
            self.process_table.item(
                row,
                0
            )
        )

        name_item = (
            self.process_table.item(
                row,
                1
            )
        )

        if (
            not pid_item
            or not name_item
        ):
            return

        pid = int(
            pid_item.text()
        )

        name = (
            name_item.text()
        )

        if pid in [
            1,
            os.getpid()
        ]:

            QMessageBox.warning(
                self,
                "PROCESS CONTROL",
                "LCARS will not terminate this critical process."
            )

            return

        answer = (
            QMessageBox.question(
                self,
                "PROCESS CONTROL",
                f"Terminate process?\n\n{name}\nPID {pid}",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No
            )
        )

        if answer != (
            QMessageBox.Yes
        ):
            return

        try:

            process = (
                psutil.Process(
                    pid
                )
            )

            process.terminate()

            self.notify(
                f"PROCESS TERMINATED // {name}"
            )

            QTimer.singleShot(
                800,
                self.refresh_processes
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "PROCESS CONTROL",
                str(
                    error
                )
            )

    # =====================================================
    # SETTINGS
    # =====================================================

    def change_theme(
        self,
        name
    ):

        self.settings[
            "theme"
        ] = name

        self.accent = THEMES.get(
            name,
            ORANGE
        )

        self.starship_display.set_accent(
            self.accent
        )

        self.display_frame.setStyleSheet(
            f"""
            QFrame#mainDisplay {{
                background-color: #040508;
                border: 3px solid {self.accent};
                border-radius: 28px;
            }}
            """
        )

        self.save_settings()

        self.notify(
            f"INTERFACE MODE // {name}"
        )

    def change_animation_setting(
        self,
        enabled
    ):

        self.animations_enabled = (
            enabled
        )

        self.settings[
            "animations"
        ] = enabled

        self.starship_display.set_animation(
            enabled
        )

        self.save_settings()

        self.notify(
            "DISPLAY ANIMATIONS "
            + (
                "ENABLED"
                if enabled
                else "DISABLED"
            )
        )

    # =====================================================
    # POWER
    # =====================================================

    def logout_lcars(self):

        if os.environ.get(
            "SWAYSOCK"
        ):

            subprocess.Popen(
                [
                    "swaymsg",
                    "exit"
                ]
            )

        else:

            self.close()

    def restart_system(self):

        answer = (
            QMessageBox.question(
                self,
                "RESTART",
                "Restart Fedora?",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No
            )
        )

        if answer == (
            QMessageBox.Yes
        ):

            subprocess.Popen(
                [
                    "systemctl",
                    "reboot"
                ]
            )

    def shutdown_system(self):

        answer = (
            QMessageBox.question(
                self,
                "SHUT DOWN",
                "Shut down Fedora?",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No
            )
        )

        if answer == (
            QMessageBox.Yes
        ):

            subprocess.Popen(
                [
                    "systemctl",
                    "poweroff"
                ]
            )


# =========================================================
# APPLICATION START
# =========================================================

app = QApplication(
    sys.argv
)

window = LCARS()

window.showFullScreen()

sys.exit(
    app.exec()
)
