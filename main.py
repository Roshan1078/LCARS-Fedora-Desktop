import sys
import os
import re
import time
import socket
import shutil
import mimetypes
import subprocess
from datetime import datetime

import psutil

from PySide6.QtCore import Qt, QTimer, QProcess
from PySide6.QtGui import QPixmap
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
)


COLORS = {
    "orange": "#F59A67",
    "peach": "#F7C99A",
    "purple": "#C89AF7",
    "blue": "#8AA7FF",
    "pink": "#C96A9A",
    "red": "#D86A6A",
    "cyan": "#8FD3FF",
}


def lcars_button(text, color, align="right"):

    button = QPushButton(text)

    button.setMinimumHeight(58)

    button.setCursor(
        Qt.PointingHandCursor
    )

    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: black;
            border: 0;
            border-radius: 27px;
            padding: 12px 20px;
            font-size: 18px;
            font-weight: 800;
            text-align: {align};
        }}

        QPushButton:hover {{
            border: 3px solid white;
        }}

        QPushButton[active="true"] {{
            border: 4px solid white;
        }}

        QPushButton:pressed {{
            background-color: white;
        }}

        QPushButton:disabled {{
            background-color: #4A4A4A;
            color: #9A9A9A;
        }}
    """)

    return button


def info_card(title, value_widget, accent):

    card = QFrame()

    card.setStyleSheet(f"""
        QFrame {{
            background-color: #0A0A0A;
            border: 2px solid {accent};
            border-radius: 18px;
        }}
    """)

    layout = QVBoxLayout(card)

    layout.setContentsMargins(
        18,
        14,
        18,
        14
    )

    title_label = QLabel(title)

    title_label.setStyleSheet(
        f"""
        color: {accent};
        font-size: 14px;
        font-weight: 800;
        """
    )

    value_widget.setStyleSheet(
        """
        color: white;
        font-size: 25px;
        font-weight: 800;
        """
    )

    layout.addWidget(
        title_label
    )

    layout.addWidget(
        value_widget
    )

    return card


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

        self.current_directory = (
            os.path.expanduser("~")
        )

        self.selected_file = None

        self.nav_buttons = []

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: white;
                font-family: Arial;
            }

            QLabel#brand {
                color: #F7C99A;
                font-size: 30px;
                font-weight: 900;
            }

            QLabel#subbrand {
                color: #C89AF7;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#clock {
                color: #F7C99A;
                font-size: 21px;
                font-weight: 900;
            }

            QLabel#pageTitle {
                color: #F7C99A;
                font-size: 31px;
                font-weight: 900;
            }

            QLabel#sectionLabel {
                color: #C89AF7;
                font-size: 14px;
                font-weight: 800;
            }

            QLabel#path {
                color: #8FD3FF;
                font-size: 15px;
                padding: 4px;
            }

            QFrame#topbar {
                background-color: #0B0B0B;
                border: 2px solid #F59A67;
                border-radius: 24px;
            }

            QFrame#display {
                background-color: #050505;
                border: 3px solid #C89AF7;
                border-radius: 30px;
            }

            QFrame#rail {
                background-color: #070707;
                border: 2px solid #F59A67;
                border-radius: 30px;
            }

            QFrame#metadata {
                background-color: #080808;
                border: 2px solid #8AA7FF;
                border-radius: 18px;
            }

            QLineEdit {
                background-color: #0A0A0A;
                color: white;
                border: 2px solid #C89AF7;
                border-radius: 15px;
                padding: 13px;
                font-size: 18px;
            }

            QTextEdit {
                background-color: #050505;
                color: #8FD3FF;
                border: 2px solid #8AA7FF;
                border-radius: 16px;
                padding: 12px;
                font-family: monospace;
                font-size: 15px;
            }

            QListWidget {
                background-color: #050505;
                color: white;
                border: 2px solid #F59A67;
                border-radius: 16px;
                font-size: 17px;
                padding: 7px;
            }

            QListWidget::item {
                padding: 9px;
            }

            QListWidget::item:selected {
                background-color: #C89AF7;
                color: black;
            }
        """)

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            16,
            16,
            16,
            16
        )

        root.setSpacing(
            10
        )

        # =================================================
        # TOP BAR
        # =================================================

        top_frame = QFrame()

        top_frame.setObjectName(
            "topbar"
        )

        top = QHBoxLayout(
            top_frame
        )

        top.setContentsMargins(
            20,
            12,
            20,
            12
        )

        brand_box = QVBoxLayout()

        brand = QLabel(
            "LCARS // FEDORA"
        )

        brand.setObjectName(
            "brand"
        )

        subbrand = QLabel(
            "UNIFIED SYSTEM CONTROL ENVIRONMENT"
        )

        subbrand.setObjectName(
            "subbrand"
        )

        brand_box.addWidget(
            brand
        )

        brand_box.addWidget(
            subbrand
        )

        top.addLayout(
            brand_box
        )

        top.addStretch()

        self.top_cpu = QLabel(
            "CPU --"
        )

        self.top_mem = QLabel(
            "MEM --"
        )

        self.top_net = QLabel(
            "NET --"
        )

        indicators = [
            (
                self.top_cpu,
                COLORS["orange"]
            ),
            (
                self.top_mem,
                COLORS["purple"]
            ),
            (
                self.top_net,
                COLORS["blue"]
            )
        ]

        for widget, color in indicators:

            widget.setStyleSheet(
                f"""
                background: {color};
                color: black;
                border-radius: 15px;
                padding: 8px 14px;
                font-weight: 900;
                """
            )

            top.addWidget(
                widget
            )

        self.clock = QLabel()

        self.clock.setObjectName(
            "clock"
        )

        top.addSpacing(
            12
        )

        top.addWidget(
            self.clock
        )

        root.addWidget(
            top_frame
        )

        # =================================================
        # BODY
        # =================================================

        body = QHBoxLayout()

        body.setSpacing(
            12
        )

        # =================================================
        # NAVIGATION RAIL
        # =================================================

        rail = QFrame()

        rail.setObjectName(
            "rail"
        )

        nav = QVBoxLayout(
            rail
        )

        nav.setContentsMargins(
            12,
            14,
            12,
            14
        )

        nav.setSpacing(
            8
        )

        nav_title = QLabel(
            "LCARS 47"
        )

        nav_title.setStyleSheet(
            """
            color: #F7C99A;
            font-size: 18px;
            font-weight: 900;
            padding: 8px;
            """
        )

        nav.addWidget(
            nav_title
        )

        self.home_btn = lcars_button(
            "HOME",
            COLORS["orange"]
        )

        self.system_btn = lcars_button(
            "SYSTEM",
            COLORS["peach"]
        )

        self.network_btn = lcars_button(
            "NETWORK",
            COLORS["purple"]
        )

        self.files_btn = lcars_button(
            "FILES",
            COLORS["blue"]
        )

        self.browser_btn = lcars_button(
            "FIREFOX",
            COLORS["orange"]
        )

        self.terminal_btn = lcars_button(
            "TERMINAL",
            COLORS["pink"]
        )

        self.power_btn = lcars_button(
            "POWER",
            COLORS["red"]
        )

        self.nav_buttons = [
            self.home_btn,
            self.system_btn,
            self.network_btn,
            self.files_btn,
            self.browser_btn,
            self.terminal_btn,
            self.power_btn
        ]

        for button in self.nav_buttons:

            nav.addWidget(
                button
            )

        nav.addStretch()

        emergency = QLabel(
            "SUPER+1  HOME\n"
            "SUPER+ENTER  TERMINAL\n"
            "SUPER+SHIFT+ESC  LOGOUT"
        )

        emergency.setStyleSheet(
            """
            color: #8A8A94;
            font-size: 11px;
            padding: 6px;
            """
        )

        nav.addWidget(
            emergency
        )

        body.addWidget(
            rail,
            1
        )

        # =================================================
        # DISPLAY AREA
        # =================================================

        display_frame = QFrame()

        display_frame.setObjectName(
            "display"
        )

        display_layout = QVBoxLayout(
            display_frame
        )

        display_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.pages = QStackedWidget()

        display_layout.addWidget(
            self.pages
        )

        body.addWidget(
            display_frame,
            5
        )

        root.addLayout(
            body,
            1
        )

        # =================================================
        # BUILD PAGES
        # =================================================

        self.build_home_page()

        self.build_system_page()

        self.build_network_page()

        self.build_files_page()

        self.build_power_page()

        # =================================================
        # NAVIGATION CONNECTIONS
        # =================================================

        self.home_btn.clicked.connect(
            lambda:
            self.show_page(
                0,
                self.home_btn
            )
        )

        self.system_btn.clicked.connect(
            lambda:
            self.show_page(
                1,
                self.system_btn
            )
        )

        self.network_btn.clicked.connect(
            lambda:
            self.show_page(
                2,
                self.network_btn
            )
        )

        self.files_btn.clicked.connect(
            self.open_files_page
        )

        self.browser_btn.clicked.connect(
            self.open_firefox
        )

        self.terminal_btn.clicked.connect(
            self.open_terminal
        )

        self.power_btn.clicked.connect(
            lambda:
            self.show_page(
                4,
                self.power_btn
            )
        )

        # =================================================
        # PING PROCESS
        # =================================================

        self.ping_process = QProcess(
            self
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

        self.ping_button.clicked.connect(
            self.start_ping
        )

        self.ping_target.returnPressed.connect(
            self.start_ping
        )

        # =================================================
        # FILE EVENTS
        # =================================================

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

        # =================================================
        # SYSTEM UPDATE TIMER
        # =================================================

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.update_information
        )

        self.timer.start(
            1000
        )

        self.load_directory(
            self.current_directory
        )

        self.show_page(
            0,
            self.home_btn
        )

        self.update_information()

    # =====================================================
    # HOME PAGE
    # =====================================================

    def build_home_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        title = QLabel(
            "FEDERATION COMPUTER SYSTEM"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "FEDORA NODE // LCARS DESKTOP SESSION"
        )

        subtitle.setStyleSheet(
            """
            color: #8FD3FF;
            font-size: 16px;
            font-weight: 700;
            """
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            16
        )

        grid = QGridLayout()

        self.home_cpu = QLabel(
            "--"
        )

        self.home_mem = QLabel(
            "--"
        )

        self.home_uptime = QLabel(
            "--"
        )

        self.home_ip = QLabel(
            "--"
        )

        grid.addWidget(
            info_card(
                "PROCESSOR",
                self.home_cpu,
                COLORS["orange"]
            ),
            0,
            0
        )

        grid.addWidget(
            info_card(
                "MEMORY",
                self.home_mem,
                COLORS["purple"]
            ),
            0,
            1
        )

        grid.addWidget(
            info_card(
                "UPTIME",
                self.home_uptime,
                COLORS["peach"]
            ),
            1,
            0
        )

        grid.addWidget(
            info_card(
                "NETWORK",
                self.home_ip,
                COLORS["blue"]
            ),
            1,
            1
        )

        layout.addLayout(
            grid
        )

        layout.addSpacing(
            18
        )

        self.home_message = QLabel(
            "SYSTEM OPERATIONAL"
        )

        self.home_message.setAlignment(
            Qt.AlignCenter
        )

        self.home_message.setStyleSheet(
            """
            color: #F7C99A;
            font-size: 28px;
            font-weight: 900;
            padding: 18px;
            """
        )

        layout.addWidget(
            self.home_message
        )

        layout.addStretch()

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

        title = QLabel(
            "SYSTEM STATUS"
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        grid = QGridLayout()

        self.cpu_value = QLabel()
        self.ram_value = QLabel()
        self.uptime_value = QLabel()
        self.cores_value = QLabel()
        self.fedora_value = QLabel()
        self.boot_value = QLabel()

        cards = [
            (
                "PROCESSOR ACTIVITY",
                self.cpu_value,
                COLORS["orange"]
            ),
            (
                "MEMORY ALLOCATION",
                self.ram_value,
                COLORS["purple"]
            ),
            (
                "SYSTEM UPTIME",
                self.uptime_value,
                COLORS["peach"]
            ),
            (
                "PROCESSOR CORES",
                self.cores_value,
                COLORS["blue"]
            ),
            (
                "OPERATING SYSTEM",
                self.fedora_value,
                COLORS["orange"]
            ),
            (
                "BOOT SEQUENCE",
                self.boot_value,
                COLORS["purple"]
            )
        ]

        for i, (
            name,
            value,
            color
        ) in enumerate(cards):

            grid.addWidget(
                info_card(
                    name,
                    value,
                    color
                ),
                i // 2,
                i % 2
            )

        layout.addSpacing(
            12
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

        title = QLabel(
            "NETWORK OPERATIONS"
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        self.network_status = QLabel()

        self.network_status.setStyleSheet(
            """
            color: #8FD3FF;
            font-size: 18px;
            font-weight: 700;
            padding: 8px;
            """
        )

        layout.addWidget(
            self.network_status
        )

        ping_label = QLabel(
            "PING DESTINATION"
        )

        ping_label.setObjectName(
            "sectionLabel"
        )

        layout.addWidget(
            ping_label
        )

        self.ping_target = QLineEdit()

        self.ping_target.setPlaceholderText(
            "google.com or 8.8.8.8"
        )

        self.ping_button = lcars_button(
            "EXECUTE PING",
            COLORS["purple"],
            "center"
        )

        self.ping_output = QTextEdit()

        self.ping_output.setReadOnly(
            True
        )

        self.ping_output.setPlaceholderText(
            "NETWORK RESPONSE WILL APPEAR HERE"
        )

        layout.addWidget(
            self.ping_target
        )

        layout.addWidget(
            self.ping_button
        )

        layout.addWidget(
            self.ping_output,
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

        title = QLabel(
            "FILE SYSTEM"
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        self.path_label = QLabel()

        self.path_label.setObjectName(
            "path"
        )

        layout.addWidget(
            self.path_label
        )

        file_area = QHBoxLayout()

        # FILE LIST

        self.file_list = QListWidget()

        file_area.addWidget(
            self.file_list,
            2
        )

        # PREVIEW

        preview_box = QVBoxLayout()

        preview_title = QLabel(
            "VISUAL PREVIEW"
        )

        preview_title.setObjectName(
            "sectionLabel"
        )

        self.image_preview = QLabel(
            "NO FILE SELECTED"
        )

        self.image_preview.setAlignment(
            Qt.AlignCenter
        )

        self.image_preview.setMinimumSize(
            300,
            280
        )

        self.image_preview.setStyleSheet(
            """
            background: #070707;
            border: 2px solid #F59A67;
            border-radius: 18px;
            font-size: 16px;
            """
        )

        preview_box.addWidget(
            preview_title
        )

        preview_box.addWidget(
            self.image_preview,
            1
        )

        file_area.addLayout(
            preview_box,
            3
        )

        # METADATA

        metadata_frame = QFrame()

        metadata_frame.setObjectName(
            "metadata"
        )

        metadata_layout = QVBoxLayout(
            metadata_frame
        )

        metadata_title = QLabel(
            "FILE DATA"
        )

        metadata_title.setObjectName(
            "sectionLabel"
        )

        self.metadata_label = QLabel(
            "SELECT A FILE"
        )

        self.metadata_label.setWordWrap(
            True
        )

        self.metadata_label.setStyleSheet(
            """
            font-size: 15px;
            padding: 8px;
            """
        )

        metadata_layout.addWidget(
            metadata_title
        )

        metadata_layout.addWidget(
            self.metadata_label
        )

        metadata_layout.addStretch()

        file_area.addWidget(
            metadata_frame,
            2
        )

        layout.addLayout(
            file_area,
            1
        )

        controls = QHBoxLayout()

        self.back_button = lcars_button(
            "BACK",
            COLORS["purple"],
            "center"
        )

        self.open_button = lcars_button(
            "OPEN",
            COLORS["peach"],
            "center"
        )

        self.delete_button = lcars_button(
            "DELETE FILE",
            COLORS["red"],
            "center"
        )

        controls.addWidget(
            self.back_button
        )

        controls.addWidget(
            self.open_button
        )

        controls.addWidget(
            self.delete_button
        )

        layout.addLayout(
            controls
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

        title = QLabel(
            "SESSION CONTROL"
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        message = QLabel(
            "SELECT A SYSTEM ACTION"
        )

        message.setAlignment(
            Qt.AlignCenter
        )

        message.setStyleSheet(
            """
            color: #8FD3FF;
            font-size: 20px;
            font-weight: 800;
            padding: 20px;
            """
        )

        layout.addWidget(
            message
        )

        layout.addStretch()

        logout = lcars_button(
            "LOG OUT",
            COLORS["purple"],
            "center"
        )

        restart = lcars_button(
            "RESTART FEDORA",
            COLORS["orange"],
            "center"
        )

        shutdown = lcars_button(
            "SHUT DOWN",
            COLORS["red"],
            "center"
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
    # NAVIGATION
    # =====================================================

    def show_page(
        self,
        index,
        active_button=None
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

        if active_button:

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
    # SYSTEM INFORMATION
    # =====================================================

    def update_information(self):

        now = datetime.now()

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory()

        uptime_seconds = (
            time.time()
            - psutil.boot_time()
        )

        hours = int(
            uptime_seconds
            // 3600
        )

        minutes = int(
            (
                uptime_seconds
                % 3600
            )
            // 60
        )

        interface, ip = (
            self.get_network_info()
        )

        self.clock.setText(
            now.strftime(
                "%Y.%m.%d // %H:%M:%S"
            )
        )

        self.top_cpu.setText(
            f"CPU {cpu:.0f}%"
        )

        self.top_mem.setText(
            f"MEM {ram.percent:.0f}%"
        )

        self.top_net.setText(
            "NET ON"
            if interface
            else "NET OFF"
        )

        self.home_cpu.setText(
            f"{cpu:.1f}%"
        )

        self.home_mem.setText(
            f"{ram.percent:.1f}%"
        )

        self.home_uptime.setText(
            f"{hours}H {minutes}M"
        )

        self.home_ip.setText(
            ip
            if ip
            else "OFFLINE"
        )

        self.cpu_value.setText(
            f"{cpu:.1f}%"
        )

        self.ram_value.setText(
            f"{ram.percent:.1f}%"
        )

        self.uptime_value.setText(
            f"{hours} H {minutes} M"
        )

        self.cores_value.setText(
            str(
                psutil.cpu_count()
            )
        )

        self.boot_value.setText(
            datetime.fromtimestamp(
                psutil.boot_time()
            ).strftime(
                "%Y-%m-%d %H:%M"
            )
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

            fedora = "Fedora Linux"

        self.fedora_value.setText(
            fedora
        )

        if interface:

            self.network_status.setText(
                f"""
STATUS      ONLINE
INTERFACE   {interface}
LOCAL IP    {ip}
"""
            )

            self.home_message.setText(
                "SYSTEM OPERATIONAL // NETWORK LINK ACTIVE"
            )

        else:

            self.network_status.setText(
                "STATUS      OFFLINE"
            )

            self.home_message.setText(
                "SYSTEM OPERATIONAL // NETWORK OFFLINE"
            )

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

    # =====================================================
    # PING
    # =====================================================

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
LCARS NETWORK TEST
TARGET: {target}
---------------------------
"""
        )

        self.ping_button.setEnabled(
            False
        )

        self.ping_button.setText(
            "PING ACTIVE..."
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
---------------------------
NETWORK TEST COMPLETE
"""
        )

        self.ping_button.setText(
            "EXECUTE PING"
        )

        self.ping_button.setEnabled(
            True
        )

    # =====================================================
    # FILE SYSTEM
    # =====================================================

    def open_files_page(self):

        self.show_page(
            3,
            self.files_btn
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
            "CURRENT LOCATION // "
            + directory
        )

        self.file_list.clear()

        self.selected_file = None

        self.image_preview.clear()

        self.image_preview.setText(
            "SELECT FILE"
        )

        self.metadata_label.setText(
            "SELECT A FILE"
        )

        try:

            entries = os.listdir(
                directory
            )

        except PermissionError:

            self.metadata_label.setText(
                "ACCESS DENIED"
            )

            return

        except OSError as error:

            self.metadata_label.setText(
                f"ERROR\n\n{error}"
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

            if name.startswith("."):
                continue

            full_path = os.path.join(
                directory,
                name
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

        self.selected_file = path

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

            self.selected_file = path

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
                    "%Y-%m-%d\n%H:%M:%S"
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
                f"ERROR\n\n{error}"
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

        image_types = (
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".gif",
            ".webp"
        )

        if path.lower().endswith(
            image_types
        ):

            pixmap = QPixmap(
                path
            )

            if pixmap.isNull():

                self.image_preview.setText(
                    "PREVIEW UNAVAILABLE"
                )

                return

            scaled = pixmap.scaled(
                self.image_preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_preview.setPixmap(
                scaled
            )

        else:

            self.image_preview.setText(
                "NO IMAGE PREVIEW\n\n"
                + os.path.basename(
                    path
                )
            )

    @staticmethod
    def format_size(size):

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

        parent = os.path.dirname(
            self.current_directory
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

        if os.environ.get(
            "SWAYSOCK"
        ):

            subprocess.run(
                [
                    "swaymsg",
                    "workspace",
                    "number",
                    "4"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        subprocess.Popen(
            [
                "xdg-open",
                self.selected_file
            ]
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

        filename = os.path.basename(
            self.selected_file
        )

        answer = QMessageBox.question(
            self,
            "DELETE CONFIRMATION",
            f"""
DELETE SELECTED FILE?

{filename}

Are you sure you want to permanently delete this file?
""",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if answer == QMessageBox.Yes:

            try:

                os.remove(
                    self.selected_file
                )

                self.selected_file = None

                self.load_directory(
                    self.current_directory
                )

            except Exception as error:

                QMessageBox.critical(
                    self,
                    "DELETE FAILED",
                    str(error)
                )

    # =====================================================
    # APPLICATION LAUNCHERS
    # =====================================================

    def open_firefox(self):

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

        if shutil.which(
            "firefox"
        ):

            subprocess.Popen(
                ["firefox"]
            )

        else:

            QMessageBox.warning(
                self,
                "FIREFOX",
                "Firefox was not found."
            )

    def open_terminal(self):

        if os.environ.get(
            "SWAYSOCK"
        ):

            subprocess.run(
                [
                    "swaymsg",
                    "workspace",
                    "number",
                    "3"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        terminals = [
            "ptyxis",
            "kgx",
            "gnome-terminal",
            "foot",
            "konsole",
            "alacritty",
            "kitty"
        ]

        for terminal in terminals:

            if shutil.which(
                terminal
            ):

                subprocess.Popen(
                    [terminal]
                )

                return

        QMessageBox.warning(
            self,
            "TERMINAL",
            "No supported terminal application was found."
        )

    # =====================================================
    # POWER / SESSION
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

        answer = QMessageBox.question(
            self,
            "RESTART",
            "Restart Fedora now?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if answer == QMessageBox.Yes:

            subprocess.Popen(
                [
                    "systemctl",
                    "reboot"
                ]
            )

    def shutdown_system(self):

        answer = QMessageBox.question(
            self,
            "SHUT DOWN",
            "Shut down Fedora now?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if answer == QMessageBox.Yes:

            subprocess.Popen(
                [
                    "systemctl",
                    "poweroff"
                ]
            )


app = QApplication(
    sys.argv
)

window = LCARS()

window.showFullScreen()

sys.exit(
    app.exec()
)
