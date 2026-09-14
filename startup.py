import sys
import os
import math
import random
import socket
import subprocess

import psutil

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QPen,
    QPainterPath,
    QLinearGradient,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget


# =========================================================
# CINEMATIC LCARS STARTUP
# =========================================================

class StartupScreen(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LCARS Cinematic Startup")
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()

        self.frame = 0
        self.time = 0.0

        # Main animation values
        self.planet_scale = 1.35
        self.hud_alpha = 0.0
        self.crew_alpha = 0.0
        self.ship_progress = 0.0
        self.progress = 0.0
        self.fade_out = 0.0
        self.orbit_angle = 0.0

        self.stage = 0
        self.launched = False

        # Real Fedora information
        self.system_data = self.get_system_data()

        # Star layers
        self.stars_far = self.create_stars(
            110,
            1,
            2,
            100,
            170
        )

        self.stars_mid = self.create_stars(
            80,
            1,
            3,
            130,
            220
        )

        self.stars_near = self.create_stars(
            45,
            2,
            4,
            170,
            255
        )

        # 60-ish FPS
        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(16)

    # =====================================================
    # SYSTEM DATA
    # =====================================================

    def get_system_data(self):

        try:
            with open(
                "/etc/fedora-release",
                "r"
            ) as file:
                fedora = file.read().strip()

        except Exception:
            fedora = "Fedora Linux"

        memory_gb = (
            psutil.virtual_memory().total
            / (1024 ** 3)
        )

        ip_address = "OFFLINE"
        interface_name = "NONE"

        try:

            stats = psutil.net_if_stats()
            addresses = psutil.net_if_addrs()

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

                            interface_name = interface
                            ip_address = address.address
                            break

                    if ip_address != "OFFLINE":
                        break

        except Exception:
            pass

        return {
            "fedora": fedora,
            "hostname": socket.gethostname(),
            "cores": psutil.cpu_count(),
            "memory": f"{memory_gb:.1f} GB",
            "interface": interface_name,
            "ip": ip_address,
        }

    # =====================================================
    # STAR GENERATOR
    # =====================================================

    def create_stars(
        self,
        amount,
        minimum_size,
        maximum_size,
        minimum_alpha,
        maximum_alpha
    ):

        stars = []

        for _ in range(amount):

            stars.append({
                "x": random.random(),
                "y": random.random(),
                "size": random.randint(
                    minimum_size,
                    maximum_size
                ),
                "alpha": random.randint(
                    minimum_alpha,
                    maximum_alpha
                ),
                "phase": random.uniform(
                    0,
                    math.pi * 2
                ),
            })

        return stars

    # =====================================================
    # ANIMATION TIMELINE
    # =====================================================

    def animate(self):

        self.frame += 1
        self.time += 0.016
        self.orbit_angle += 0.55

        # ---------------------------------------------
        # STAGE 0
        # Planet reveal
        # ---------------------------------------------

        if self.stage == 0:

            self.planet_scale += (
                0.74 - self.planet_scale
            ) * 0.025

            self.progress = min(
                0.25,
                self.progress + 0.0028
            )

            self.hud_alpha = min(
                0.35,
                self.hud_alpha + 0.005
            )

            if self.frame > 120:

                self.stage = 1
                self.frame = 0

        # ---------------------------------------------
        # STAGE 1
        # Ship enters + planet zoom-out
        # ---------------------------------------------

        elif self.stage == 1:

            self.planet_scale += (
                0.52 - self.planet_scale
            ) * 0.018

            self.ship_progress = min(
                1.0,
                self.ship_progress + 0.0065
            )

            self.hud_alpha = min(
                1.0,
                self.hud_alpha + 0.01
            )

            self.progress = min(
                0.60,
                self.progress + 0.0035
            )

            if self.frame > 165:

                self.stage = 2
                self.frame = 0

        # ---------------------------------------------
        # STAGE 2
        # Crew holograms + telemetry
        # ---------------------------------------------

        elif self.stage == 2:

            self.crew_alpha = min(
                1.0,
                self.crew_alpha + 0.018
            )

            self.progress = min(
                0.90,
                self.progress + 0.004
            )

            if self.frame > 135:

                self.stage = 3
                self.frame = 0

        # ---------------------------------------------
        # STAGE 3
        # System ready
        # ---------------------------------------------

        elif self.stage == 3:

            self.progress = min(
                1.0,
                self.progress + 0.01
            )

            if self.frame > 70:

                self.stage = 4
                self.frame = 0

        # ---------------------------------------------
        # STAGE 4
        # Cinematic fade into desktop
        # ---------------------------------------------

        elif self.stage == 4:

            self.fade_out = min(
                1.0,
                self.fade_out + 0.022
            )

            if (
                self.fade_out >= 1.0
                and not self.launched
            ):
                self.launch_lcars()
                return

        self.update()

    # =====================================================
    # LAUNCH MAIN DESKTOP
    # =====================================================

    def launch_lcars(self):

        self.launched = True

        subprocess.Popen([
            "python3",
            os.path.expanduser(
                "~/lcars-shell/main.py"
            )
        ])

        self.close()

    # =====================================================
    # STARS
    # =====================================================

    def draw_stars(
        self,
        painter,
        stars,
        width,
        height,
        speed
    ):

        painter.setPen(Qt.NoPen)

        for star in stars:

            twinkle = (
                0.70
                + 0.30
                * math.sin(
                    self.time * speed
                    + star["phase"]
                )
            )

            alpha = int(
                star["alpha"]
                * twinkle
            )

            painter.setBrush(
                QColor(
                    220,
                    232,
                    255,
                    alpha
                )
            )

            x = (
                star["x"] * width
                + math.sin(
                    self.time * 0.25
                    + star["phase"]
                ) * 4
            )

            y = (
                star["y"] * height
            )

            painter.drawEllipse(
                QRectF(
                    x,
                    y,
                    star["size"],
                    star["size"]
                )
            )

    # =====================================================
    # NEBULA BACKGROUND
    # =====================================================

    def draw_nebula(
        self,
        painter,
        width,
        height
    ):

        painter.setPen(Qt.NoPen)

        nebula1 = QRadialGradient(
            width * 0.16,
            height * 0.25,
            width * 0.28
        )

        nebula1.setColorAt(
            0,
            QColor(
                120,
                60,
                180,
                48
            )
        )

        nebula1.setColorAt(
            1,
            QColor(
                120,
                60,
                180,
                0
            )
        )

        painter.setBrush(
            nebula1
        )

        painter.drawEllipse(
            QRectF(
                -width * 0.05,
                -height * 0.05,
                width * 0.45,
                width * 0.45
            )
        )

        nebula2 = QRadialGradient(
            width * 0.85,
            height * 0.32,
            width * 0.24
        )

        nebula2.setColorAt(
            0,
            QColor(
                20,
                105,
                230,
                45
            )
        )

        nebula2.setColorAt(
            1,
            QColor(
                20,
                105,
                230,
                0
            )
        )

        painter.setBrush(
            nebula2
        )

        painter.drawEllipse(
            QRectF(
                width * 0.66,
                height * 0.06,
                width * 0.38,
                width * 0.38
            )
        )

    # =====================================================
    # PLANET
    # =====================================================

    def draw_planet(
        self,
        painter,
        width,
        height
    ):

        dimension = min(
            width,
            height
        )

        diameter = (
            dimension
            * self.planet_scale
        )

        radius = diameter / 2

        center_x = width * 0.50
        center_y = height * 0.50

        planet_rect = QRectF(
            center_x - radius,
            center_y - radius,
            diameter,
            diameter
        )

        # ---------------------------------------------
        # Atmosphere glow
        # ---------------------------------------------

        atmosphere = QRadialGradient(
            center_x,
            center_y,
            radius * 1.20
        )

        atmosphere.setColorAt(
            0.65,
            QColor(
                80,
                170,
                255,
                0
            )
        )

        atmosphere.setColorAt(
            0.82,
            QColor(
                80,
                170,
                255,
                72
            )
        )

        atmosphere.setColorAt(
            1.0,
            QColor(
                80,
                170,
                255,
                0
            )
        )

        painter.setBrush(
            atmosphere
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - radius * 1.22,
                center_y
                - radius * 1.22,
                diameter * 1.22,
                diameter * 1.22
            )
        )

        # ---------------------------------------------
        # Planet body
        # ---------------------------------------------

        planet = QRadialGradient(
            center_x - radius * 0.28,
            center_y - radius * 0.30,
            radius * 1.05
        )

        planet.setColorAt(
            0.0,
            QColor(
                170,
                225,
                255
            )
        )

        planet.setColorAt(
            0.25,
            QColor(
                70,
                155,
                230
            )
        )

        planet.setColorAt(
            0.60,
            QColor(
                30,
                95,
                175
            )
        )

        planet.setColorAt(
            1.0,
            QColor(
                3,
                13,
                50
            )
        )

        painter.setBrush(
            planet
        )

        painter.setPen(
            QPen(
                QColor(
                    120,
                    200,
                    255,
                    170
                ),
                2
            )
        )

        painter.drawEllipse(
            planet_rect
        )

        # Planet clip
        clip = QPainterPath()

        clip.addEllipse(
            planet_rect
        )

        painter.save()

        painter.setClipPath(
            clip
        )

        # ---------------------------------------------
        # Rotating continents
        # ---------------------------------------------

        rotation = (
            math.sin(
                self.time * 0.35
            )
            * radius * 0.10
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                48,
                138,
                95,
                205
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - radius * 0.42
                + rotation,
                center_y
                - radius * 0.16,
                radius * 0.48,
                radius * 0.22
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                + radius * 0.08
                + rotation,
                center_y
                + radius * 0.11,
                radius * 0.38,
                radius * 0.18
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - radius * 0.12
                + rotation,
                center_y
                - radius * 0.40,
                radius * 0.28,
                radius * 0.13
            )
        )

        # ---------------------------------------------
        # Clouds
        # ---------------------------------------------

        cloud_shift = (
            math.sin(
                self.time * 0.52
            )
            * radius * 0.08
        )

        painter.setBrush(
            QColor(
                255,
                255,
                255,
                35
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - radius * 0.52
                + cloud_shift,
                center_y
                - radius * 0.27,
                radius * 0.92,
                radius * 0.09
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - radius * 0.18
                + cloud_shift,
                center_y
                + radius * 0.08,
                radius * 0.68,
                radius * 0.07
            )
        )

        # ---------------------------------------------
        # Planet scan beam
        # ---------------------------------------------

        scan_position = (
            (
                math.sin(
                    self.time * 1.2
                )
                + 1
            )
            / 2
        )

        scan_x = (
            center_x
            - radius
            + scan_position
            * diameter
        )

        scan_gradient = QLinearGradient(
            scan_x - 35,
            center_y,
            scan_x + 35,
            center_y
        )

        scan_gradient.setColorAt(
            0,
            QColor(
                150,
                235,
                255,
                0
            )
        )

        scan_gradient.setColorAt(
            0.5,
            QColor(
                170,
                245,
                255,
                90
            )
        )

        scan_gradient.setColorAt(
            1,
            QColor(
                150,
                235,
                255,
                0
            )
        )

        painter.setBrush(
            scan_gradient
        )

        painter.drawRect(
            QRectF(
                scan_x - 35,
                center_y - radius,
                70,
                diameter
            )
        )

        painter.restore()

        # ---------------------------------------------
        # Orbit ring
        # ---------------------------------------------

        painter.save()

        painter.translate(
            center_x,
            center_y
        )

        painter.rotate(
            -18
        )

        painter.setBrush(
            Qt.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    125,
                    215,
                    255,
                    int(
                        150
                        * self.hud_alpha
                    )
                ),
                2
            )
        )

        painter.rotate(
            self.orbit_angle
        )

        painter.drawEllipse(
            QRectF(
                -radius * 1.22,
                -radius * 0.35,
                radius * 2.44,
                radius * 0.70
            )
        )

        painter.restore()

    # =====================================================
    # STARSHIP
    # =====================================================

    def draw_spaceship(
        self,
        painter,
        width,
        height
    ):

        if self.ship_progress <= 0:
            return

        p = self.ship_progress

        # Ship flies from left to right,
        # dipping around the planet.
        x = (
            -260
            + p
            * (width + 520)
        )

        y = (
            height * 0.30
            + math.sin(
                p
                * math.pi
                * 1.7
            ) * 90
        )

        # Perspective scale
        scale = (
            0.75
            + 0.38
            * math.sin(
                p * math.pi
            )
        )

        painter.save()

        painter.translate(
            x,
            y
        )

        painter.rotate(
            -8
            + math.sin(
                p * math.pi
            ) * 6
        )

        painter.scale(
            scale,
            scale
        )

        # ---------------------------------------------
        # Engine glow
        # ---------------------------------------------

        engine_glow = QRadialGradient(
            -118,
            25,
            80
        )

        engine_glow.setColorAt(
            0,
            QColor(
                100,
                210,
                255,
                150
            )
        )

        engine_glow.setColorAt(
            1,
            QColor(
                100,
                210,
                255,
                0
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            engine_glow
        )

        painter.drawEllipse(
            QRectF(
                -190,
                -45,
                145,
                145
            )
        )

        # ---------------------------------------------
        # Saucer section
        # ---------------------------------------------

        saucer = QPainterPath()

        saucer.moveTo(
            25,
            -34
        )

        saucer.cubicTo(
            95,
            -37,
            135,
            -20,
            138,
            0
        )

        saucer.cubicTo(
            135,
            23,
            88,
            38,
            20,
            30
        )

        saucer.cubicTo(
            -18,
            27,
            -42,
            15,
            -48,
            0
        )

        saucer.cubicTo(
            -42,
            -15,
            -15,
            -28,
            25,
            -34
        )

        ship_gradient = QLinearGradient(
            -60,
            -30,
            130,
            35
        )

        ship_gradient.setColorAt(
            0,
            QColor(
                210,
                220,
                235
            )
        )

        ship_gradient.setColorAt(
            0.55,
            QColor(
                115,
                135,
                165
            )
        )

        ship_gradient.setColorAt(
            1,
            QColor(
                50,
                65,
                95
            )
        )

        painter.setBrush(
            ship_gradient
        )

        painter.setPen(
            QPen(
                QColor(
                    165,
                    215,
                    255
                ),
                2
            )
        )

        painter.drawPath(
            saucer
        )

        # ---------------------------------------------
        # Neck / central hull
        # ---------------------------------------------

        painter.setBrush(
            QColor(
                100,
                120,
                150
            )
        )

        painter.drawRoundedRect(
            QRectF(
                -68,
                -12,
                80,
                25
            ),
            10,
            10
        )

        # ---------------------------------------------
        # Engineering hull
        # ---------------------------------------------

        painter.drawEllipse(
            QRectF(
                -130,
                -23,
                85,
                46
            )
        )

        # ---------------------------------------------
        # Nacelles
        # ---------------------------------------------

        painter.setBrush(
            QColor(
                80,
                100,
                130
            )
        )

        painter.drawRoundedRect(
            QRectF(
                -145,
                -56,
                100,
                18
            ),
            9,
            9
        )

        painter.drawRoundedRect(
            QRectF(
                -145,
                38,
                100,
                18
            ),
            9,
            9
        )

        # Engine strips
        painter.setBrush(
            QColor(
                95,
                225,
                255
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.drawRoundedRect(
            QRectF(
                -139,
                -52,
                78,
                8
            ),
            4,
            4
        )

        painter.drawRoundedRect(
            QRectF(
                -139,
                42,
                78,
                8
            ),
            4,
            4
        )

        # Bridge light
        painter.setBrush(
            QColor(
                255,
                220,
                150
            )
        )

        painter.drawEllipse(
            QRectF(
                55,
                -6,
                11,
                11
            )
        )

        painter.restore()

    # =====================================================
    # GENERIC CREW HOLOGRAM
    # =====================================================

    def draw_person(
        self,
        painter,
        center_x,
        center_y,
        scale
    ):

        painter.setPen(
            QPen(
                QColor(
                    145,
                    225,
                    255,
                    int(
                        215
                        * self.crew_alpha
                    )
                ),
                2
            )
        )

        painter.setBrush(
            QColor(
                85,
                190,
                235,
                int(
                    55
                    * self.crew_alpha
                )
            )
        )

        # Head
        painter.drawEllipse(
            QRectF(
                center_x
                - 18 * scale,
                center_y
                - 50 * scale,
                36 * scale,
                36 * scale
            )
        )

        # Shoulders/body
        body = QPainterPath()

        body.moveTo(
            center_x,
            center_y - 10 * scale
        )

        body.cubicTo(
            center_x - 45 * scale,
            center_y - 5 * scale,
            center_x - 55 * scale,
            center_y + 35 * scale,
            center_x - 55 * scale,
            center_y + 60 * scale
        )

        body.lineTo(
            center_x + 55 * scale,
            center_y + 60 * scale
        )

        body.cubicTo(
            center_x + 55 * scale,
            center_y + 35 * scale,
            center_x + 45 * scale,
            center_y - 5 * scale,
            center_x,
            center_y - 10 * scale
        )

        painter.drawPath(
            body
        )

    # =====================================================
    # CREW PANELS
    # =====================================================

    def draw_crew_panel(
        self,
        painter,
        rect,
        role,
        code,
        color
    ):

        if self.crew_alpha <= 0:
            return

        panel_color = QColor(
            color
        )

        panel_color.setAlpha(
            int(
                210
                * self.crew_alpha
            )
        )

        fill = QColor(
            5,
            14,
            20,
            int(
                150
                * self.crew_alpha
            )
        )

        painter.setBrush(
            fill
        )

        painter.setPen(
            QPen(
                panel_color,
                2
            )
        )

        painter.drawRoundedRect(
            rect,
            18,
            18
        )

        # Accent
        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            panel_color
        )

        painter.drawRoundedRect(
            QRectF(
                rect.x() + 10,
                rect.y() + 10,
                rect.width() - 20,
                10
            ),
            5,
            5
        )

        # Generic holographic crew
        self.draw_person(
            painter,
            rect.center().x(),
            rect.y()
            + rect.height() * 0.43,
            0.75
        )

        # Scan line
        scan = (
            (
                math.sin(
                    self.time * 2.2
                )
                + 1
            )
            / 2
        )

        scan_y = (
            rect.y()
            + 30
            + scan
            * (
                rect.height()
                - 75
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    140,
                    235,
                    255,
                    int(
                        120
                        * self.crew_alpha
                    )
                ),
                1
            )
        )

        painter.drawLine(
            QPointF(
                rect.x() + 15,
                scan_y
            ),
            QPointF(
                rect.right() - 15,
                scan_y
            )
        )

        painter.setPen(
            QColor(
                230,
                235,
                245,
                int(
                    245
                    * self.crew_alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                rect.x(),
                rect.bottom() - 55,
                rect.width(),
                22
            ),
            Qt.AlignCenter,
            role
        )

        painter.setPen(
            QColor(
                140,
                210,
                255,
                int(
                    210
                    * self.crew_alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Consolas",
                9
            )
        )

        painter.drawText(
            QRectF(
                rect.x(),
                rect.bottom() - 30,
                rect.width(),
                18
            ),
            Qt.AlignCenter,
            code
        )

    # =====================================================
    # MAIN HUD
    # =====================================================

    def draw_hud(
        self,
        painter,
        width,
        height
    ):

        alpha = self.hud_alpha

        # ---------------------------------------------
        # Top bars
        # ---------------------------------------------

        painter.setPen(
            Qt.NoPen
        )

        top_colors = [
            "#F59A67",
            "#C89AF7",
            "#8AA7FF",
            "#F7C99A"
        ]

        positions = [
            (
                30,
                width * 0.28
            ),
            (
                width * 0.31,
                width * 0.18
            ),
            (
                width * 0.51,
                width * 0.15
            ),
            (
                width * 0.68,
                width * 0.12
            )
        ]

        for color, (
            x,
            bar_width
        ) in zip(
            top_colors,
            positions
        ):

            c = QColor(color)

            c.setAlpha(
                int(
                    255
                    * alpha
                )
            )

            painter.setBrush(
                c
            )

            painter.drawRoundedRect(
                QRectF(
                    x,
                    24,
                    bar_width,
                    29
                ),
                14,
                14
            )

        # ---------------------------------------------
        # Title
        # ---------------------------------------------

        painter.setPen(
            QColor(
                247,
                201,
                154,
                int(
                    255
                    * alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                27,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                0,
                69,
                width,
                44
            ),
            Qt.AlignCenter,
            "LCARS // FEDORA"
        )

        painter.setPen(
            QColor(
                143,
                211,
                255,
                int(
                    220
                    * alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                0,
                108,
                width,
                28
            ),
            Qt.AlignCenter,
            "FEDERATION-INSPIRED COMMAND INTERFACE // NODE 47"
        )

        # ---------------------------------------------
        # Real Fedora telemetry
        # ---------------------------------------------

        telemetry_rect = QRectF(
            35,
            height * 0.18,
            width * 0.235,
            height * 0.30
        )

        painter.setBrush(
            QColor(
                6,
                8,
                14,
                int(
                    135
                    * alpha
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    245,
                    154,
                    103,
                    int(
                        210
                        * alpha
                    )
                ),
                2
            )
        )

        painter.drawRoundedRect(
            telemetry_rect,
            18,
            18
        )

        painter.setPen(
            QColor(
                247,
                201,
                154,
                int(
                    240
                    * alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Bold
            )
        )

        painter.drawText(
            telemetry_rect.adjusted(
                15,
                14,
                -15,
                -15
            ),
            Qt.AlignTop
            | Qt.AlignLeft,
            "SYSTEM TELEMETRY"
        )

        telemetry = (
            f"HOST        {self.system_data['hostname']}\n"
            f"CPU CORES   {self.system_data['cores']}\n"
            f"MEMORY      {self.system_data['memory']}\n"
            f"NETWORK     {self.system_data['interface']}\n"
            f"LOCAL IP    {self.system_data['ip']}\n"
            f"STATUS      OPERATIONAL"
        )

        painter.setPen(
            QColor(
                143,
                211,
                255,
                int(
                    220
                    * alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Consolas",
                9
            )
        )

        painter.drawText(
            telemetry_rect.adjusted(
                15,
                44,
                -12,
                -12
            ),
            Qt.AlignTop
            | Qt.AlignLeft,
            telemetry
        )

        # ---------------------------------------------
        # Crew hologram panels
        # ---------------------------------------------

        panel_width = (
            width * 0.125
        )

        panel_height = (
            height * 0.25
        )

        right_x = (
            width
            - panel_width
            - 35
        )

        self.draw_crew_panel(
            painter,
            QRectF(
                right_x,
                height * 0.18,
                panel_width,
                panel_height
            ),
            "COMMAND",
            "CREW 01 // ACTIVE",
            "#F59A67"
        )

        self.draw_crew_panel(
            painter,
            QRectF(
                right_x,
                height * 0.46,
                panel_width,
                panel_height
            ),
            "SCIENCE",
            "CREW 02 // ACTIVE",
            "#8AA7FF"
        )

        self.draw_crew_panel(
            painter,
            QRectF(
                35,
                height * 0.52,
                panel_width,
                panel_height
            ),
            "ENGINEERING",
            "CREW 03 // ACTIVE",
            "#C89AF7"
        )

        # ---------------------------------------------
        # Status message
        # ---------------------------------------------

        if self.stage == 0:

            status = (
                "ESTABLISHING PLANETARY LINK"
            )

        elif self.stage == 1:

            status = (
                "STARSHIP APPROACH DETECTED // "
                "LCARS UPLINK ACTIVE"
            )

        elif self.stage == 2:

            status = (
                "CREW STATIONS VERIFIED // "
                "FEDORA CONTROL MODULES ONLINE"
            )

        elif self.stage == 3:

            status = (
                "SYSTEM READY"
            )

        else:

            status = (
                "TRANSFERRING CONTROL TO LCARS DESKTOP"
            )

        painter.setPen(
            QColor(
                200,
                154,
                247,
                int(
                    255
                    * alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                16,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                0,
                height - 150,
                width,
                34
            ),
            Qt.AlignCenter,
            status
        )

        # ---------------------------------------------
        # Progress
        # ---------------------------------------------

        bar_width = (
            width * 0.56
        )

        bar_x = (
            width - bar_width
        ) / 2

        bar_y = (
            height - 98
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                25,
                25,
                30,
                230
            )
        )

        painter.drawRoundedRect(
            QRectF(
                bar_x,
                bar_y,
                bar_width,
                19
            ),
            9,
            9
        )

        progress_gradient = QLinearGradient(
            bar_x,
            bar_y,
            bar_x + bar_width,
            bar_y
        )

        progress_gradient.setColorAt(
            0,
            QColor(
                "#F59A67"
            )
        )

        progress_gradient.setColorAt(
            0.5,
            QColor(
                "#C89AF7"
            )
        )

        progress_gradient.setColorAt(
            1,
            QColor(
                "#8AA7FF"
            )
        )

        painter.setBrush(
            progress_gradient
        )

        painter.drawRoundedRect(
            QRectF(
                bar_x,
                bar_y,
                bar_width
                * self.progress,
                19
            ),
            9,
            9
        )

        painter.setPen(
            QColor(
                235,
                235,
                245,
                int(
                    240
                    * alpha
                )
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                10,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                bar_x,
                bar_y - 25,
                bar_width,
                19
            ),
            Qt.AlignCenter,
            f"BOOT SEQUENCE // {int(self.progress * 100)}%"
        )

    # =====================================================
    # PAINT EVENT
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

        # ---------------------------------------------
        # Deep-space background
        # ---------------------------------------------

        background = QLinearGradient(
            0,
            0,
            0,
            height
        )

        background.setColorAt(
            0,
            QColor(
                3,
                4,
                12
            )
        )

        background.setColorAt(
            0.7,
            QColor(
                0,
                0,
                3
            )
        )

        background.setColorAt(
            1,
            QColor(
                0,
                0,
                0
            )
        )

        painter.fillRect(
            self.rect(),
            background
        )

        self.draw_nebula(
            painter,
            width,
            height
        )

        self.draw_stars(
            painter,
            self.stars_far,
            width,
            height,
            1.0
        )

        self.draw_stars(
            painter,
            self.stars_mid,
            width,
            height,
            1.8
        )

        self.draw_stars(
            painter,
            self.stars_near,
            width,
            height,
            2.7
        )

        self.draw_planet(
            painter,
            width,
            height
        )

        self.draw_spaceship(
            painter,
            width,
            height
        )

        self.draw_hud(
            painter,
            width,
            height
        )

        # ---------------------------------------------
        # Final cinematic transition
        # ---------------------------------------------

        if self.fade_out > 0:

            alpha = int(
                255
                * self.fade_out
            )

            transition = QLinearGradient(
                0,
                0,
                width,
                height
            )

            transition.setColorAt(
                0,
                QColor(
                    120,
                    200,
                    255,
                    int(
                        alpha * 0.18
                    )
                )
            )

            transition.setColorAt(
                0.45,
                QColor(
                    20,
                    30,
                    60,
                    int(
                        alpha * 0.50
                    )
                )
            )

            transition.setColorAt(
                1,
                QColor(
                    0,
                    0,
                    0,
                    alpha
                )
            )

            painter.fillRect(
                self.rect(),
                transition
            )

            painter.setPen(
                QColor(
                    255,
                    255,
                    255,
                    min(
                        255,
                        int(
                            alpha * 1.15
                        )
                    )
                )
            )

            painter.setFont(
                QFont(
                    "Arial",
                    15,
                    QFont.Bold
                )
            )

            painter.drawText(
                QRectF(
                    0,
                    height * 0.78,
                    width,
                    38
                ),
                Qt.AlignCenter,
                "LCARS CONTROL TRANSFER IN PROGRESS"
            )


# =========================================================
# START APPLICATION
# =========================================================

app = QApplication(
    sys.argv
)

startup = StartupScreen()

startup.show()

sys.exit(
    app.exec()
)
