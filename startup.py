import sys
import os
import random
import subprocess

from PySide6.QtCore import (
    Qt,
    QTimer,
    QRectF
)

from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QRadialGradient
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget
)


class StartupScreen(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "LCARS Startup"
        )

        self.setStyleSheet(
            "background:black;"
        )

        self.showFullScreen()

        self.frame = 0

        self.stage = 0

        self.planet_size = 980.0

        self.stars = [
            (
                random.random(),
                random.random(),
                random.randint(1, 3),
                random.randint(150, 255)
            )
            for _ in range(150)
        ]

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(
            33
        )

    def animate(self):

        self.frame += 1

        # Planet zooms outward

        if self.stage == 0:

            self.planet_size *= (
                0.975
            )

            if self.planet_size <= 300:

                self.planet_size = 300

                self.stage = 1

                self.frame = 0

        # Initialization pause

        elif self.stage == 1:

            if self.frame > 55:

                self.stage = 2

                self.frame = 0

        # Launch LCARS

        elif self.stage == 2:

            if self.frame > 30:

                self.timer.stop()

                self.launch_lcars()

                return

        self.update()

    def launch_lcars(self):

        subprocess.Popen(
            [
                "python3",
                os.path.expanduser(
                    "~/lcars-shell/main.py"
                )
            ]
        )

        self.close()

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

        painter.fillRect(
            self.rect(),
            QColor(
                0,
                0,
                0
            )
        )

        # =================================================
        # STAR FIELD
        # =================================================

        for (
            x_ratio,
            y_ratio,
            radius,
            brightness
        ) in self.stars:

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor(
                    brightness,
                    brightness,
                    255
                )
            )

            painter.drawEllipse(
                QRectF(
                    x_ratio
                    * width,
                    y_ratio
                    * height,
                    radius,
                    radius
                )
            )

        # =================================================
        # TOP LCARS BARS
        # =================================================

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                "#F59A67"
            )
        )

        painter.drawRoundedRect(
            QRectF(
                35,
                28,
                width * 0.30,
                32
            ),
            16,
            16
        )

        painter.setBrush(
            QColor(
                "#C89AF7"
            )
        )

        painter.drawRoundedRect(
            QRectF(
                width * 0.33,
                28,
                width * 0.24,
                32
            ),
            16,
            16
        )

        painter.setBrush(
            QColor(
                "#8AA7FF"
            )
        )

        painter.drawRoundedRect(
            QRectF(
                width * 0.58,
                28,
                width * 0.18,
                32
            ),
            16,
            16
        )

        # =================================================
        # PLANET
        # =================================================

        size = self.planet_size

        center_x = (
            width / 2
        )

        center_y = (
            height / 2
            - 15
        )

        left = (
            center_x
            - size / 2
        )

        top = (
            center_y
            - size / 2
        )

        gradient = QRadialGradient(
            center_x
            - size * 0.18,
            center_y
            - size * 0.20,
            size * 0.58
        )

        gradient.setColorAt(
            0.0,
            QColor(
                150,
                215,
                255
            )
        )

        gradient.setColorAt(
            0.42,
            QColor(
                55,
                125,
                205
            )
        )

        gradient.setColorAt(
            0.78,
            QColor(
                18,
                55,
                115
            )
        )

        gradient.setColorAt(
            1.0,
            QColor(
                3,
                10,
                35
            )
        )

        painter.setBrush(
            gradient
        )

        painter.setPen(
            QColor(
                115,
                195,
                255
            )
        )

        painter.drawEllipse(
            QRectF(
                left,
                top,
                size,
                size
            )
        )

        # =================================================
        # PLANET LAND
        # =================================================

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                45,
                125,
                92,
                210
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - size * 0.22,
                center_y
                - size * 0.10,
                size * 0.24,
                size * 0.11
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                + size * 0.05,
                center_y
                + size * 0.08,
                size * 0.20,
                size * 0.09
            )
        )

        painter.drawEllipse(
            QRectF(
                center_x
                - size * 0.05,
                center_y
                - size * 0.30,
                size * 0.16,
                size * 0.07
            )
        )

        # =================================================
        # TITLE
        # =================================================

        painter.setPen(
            QColor(
                "#F7C99A"
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                28,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                0,
                75,
                width,
                55
            ),
            Qt.AlignCenter,
            "LCARS // FEDORA"
        )

        painter.setPen(
            QColor(
                "#8FD3FF"
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
                0,
                120,
                width,
                35
            ),
            Qt.AlignCenter,
            "FEDERATION COMPUTER SYSTEM // NODE 47"
        )

        # =================================================
        # STATUS TEXT
        # =================================================

        if self.stage == 0:

            message = (
                "PLANETARY LINK ESTABLISHED // "
                "LCARS INTERFACE INITIALIZING"
            )

        elif self.stage == 1:

            message = (
                "FEDORA SYSTEM ONLINE // "
                "LOADING CONTROL ENVIRONMENT"
            )

        else:

            message = (
                "SYSTEM READY"
            )

        painter.setPen(
            QColor(
                "#C89AF7"
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                17,
                QFont.Bold
            )
        )

        painter.drawText(
            QRectF(
                0,
                height - 165,
                width,
                50
            ),
            Qt.AlignCenter,
            message
        )

        # =================================================
        # PROGRESS BAR
        # =================================================

        if self.stage == 0:

            progress = 0.62

        elif self.stage == 1:

            progress = min(
                1.0,
                self.frame / 55.0
            )

        else:

            progress = 1.0

        bar_y = (
            height - 88
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                "#202020"
            )
        )

        painter.drawRoundedRect(
            QRectF(
                width * 0.15,
                bar_y,
                width * 0.70,
                20
            ),
            10,
            10
        )

        painter.setBrush(
            QColor(
                "#F59A67"
            )
        )

        painter.drawRoundedRect(
            QRectF(
                width * 0.15,
                bar_y,
                width
                * 0.70
                * progress,
                20
            ),
            10,
            10
        )

        painter.setPen(
            QColor(
                "#8A8A94"
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                10
            )
        )

        painter.drawText(
            QRectF(
                0,
                height - 52,
                width,
                25
            ),
            Qt.AlignCenter,
            "FEDORA // WAYLAND // LCARS DESKTOP"
        )


app = QApplication(
    sys.argv
)

startup = StartupScreen()

startup.show()

sys.exit(
    app.exec()
)
