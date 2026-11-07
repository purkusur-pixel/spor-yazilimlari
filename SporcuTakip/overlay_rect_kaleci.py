# overlay_rect.py
# 4 kale köşesi + 1 top noktasına göre:
# - Kale alanına perspektif ızgara (8×3)
# - Top noktasından kalenin 4 köşesine ışın çizgileri
#
# Kullanım:
#   python overlay_rect.py \
#       x1 y1 x2 y2 x3 y3 x4 y4 \
#       [ball_x ball_y] [thickness=6] [seconds=0] [--pass] [--silent] [--test]
#
# C# tarafındaki çağrı örneği:
#   overlay_rect.py x1 y1 x2 y2 x3 y3 x4 y4 ball_x ball_y thickness seconds --pass

import sys
import math
import time
import threading

from PyQt5 import QtCore, QtGui, QtWidgets


# ==================== Yardımcı fonksiyonlar ====================

def parse_int(s, default=None):
    try:
        return int(s)
    except Exception:
        return default


def sort_corners(points):
    """
    4 nokta verildiğinde (rastgele sırada olabilir),
    bunları kaba bir şekilde TL, TR, BR, BL olarak sırala.
    """
    if len(points) != 4:
        raise ValueError("4 nokta bekleniyor")

    pts = list(points)

    # Önce y'ye göre sırala (üst 2, alt 2)
    pts_sorted = sorted(pts, key=lambda p: p[1])
    top2 = pts_sorted[:2]
    bottom2 = pts_sorted[2:]

    # Her grup içinde x'e göre sol / sağ
    tl = min(top2, key=lambda p: p[0])
    tr = max(top2, key=lambda p: p[0])
    bl = min(bottom2, key=lambda p: p[0])
    br = max(bottom2, key=lambda p: p[0])

    return tl, tr, br, bl


def lerp(p0, p1, t):
    """İki nokta arasında doğrusal interpolasyon."""
    return (
        p0[0] + (p1[0] - p0[0]) * t,
        p0[1] + (p1[1] - p0[1]) * t,
    )


# ==================== Overlay Widget ====================

class Overlay(QtWidgets.QWidget):
    def __init__(self, points, ball=None,
                 thickness=6, seconds=0,
                 passthrough=False, test_mode=False):
        super().__init__()

        # Ayarlar
        self.th = max(1, int(thickness))
        self.sec = max(0, int(seconds))
        self.pass_through = bool(passthrough)
        self.test_mode = bool(test_mode)
        self.ball = ball  # (bx, by) ya da None
        self.silent = False  # --silent için dışarıdan set ediliyor

        # Ekran boyutunu al
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.geometry()
        else:
            geo = QtCore.QRect(0, 0, 1920, 1080)
        self.setGeometry(geo)

        # Köşeleri düzenle
        if self.test_mode:
            cx = geo.center().x()
            cy = geo.center().y()
            w, h = 800, 400
            raw_points = [
                (cx - w // 2, cy - h // 2),
                (cx + w // 2, cy - h // 2),
                (cx + w // 2, cy + h // 2),
                (cx - w // 2, cy + h // 2),
            ]
        else:
            raw_points = list(points)

        self.TL, self.TR, self.BR, self.BL = sort_corners(raw_points)

        # Pencere ayarları
        flags = (
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        if self.pass_through:
            # Mouse olaylarını ilet
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            self.setFocusPolicy(QtCore.Qt.NoFocus)
            self.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)

        if self.sec > 0:
            QtCore.QTimer.singleShot(self.sec * 1000, self.close)

        self.showFullScreen()
        self.raise_()

    # ESC ile pencereyi kapatmak için
    def keyPressEvent(self, ev: QtGui.QKeyEvent):
        if ev.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Q):
            self.close()
        else:
            super().keyPressEvent(ev)

    # Asıl çizim
    def paintEvent(self, ev: QtGui.QPaintEvent):
        if self.silent:
            return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Hafif karartma
       # p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 35))

        # --- Kale alanının çerçevesi ---
        border_pen = QtGui.QPen(QtGui.QColor(255, 255, 0))
        border_pen.setWidth(max(2, self.th))
        border_pen.setCosmetic(True)
        p.setPen(border_pen)

        quad = QtGui.QPolygonF([
            QtCore.QPointF(*self.TL),
            QtCore.QPointF(*self.TR),
            QtCore.QPointF(*self.BR),
            QtCore.QPointF(*self.BL),
        ])
        p.drawPolygon(quad)

        # --- Kale içinde perspektif ızgara (8×3) ---
        grid_pen = QtGui.QPen(QtGui.QColor(255, 255, 0, 160))
        grid_pen.setWidth(max(1, self.th - 1))
        grid_pen.setCosmetic(True)
        p.setPen(grid_pen)

        COLS = 8
        ROWS = 3

        # Dikey çizgiler (1..COLS-1)
        for c in range(1, COLS):
            t = c / COLS
            top = lerp(self.TL, self.TR, t)
            bot = lerp(self.BL, self.BR, t)
            p.drawLine(QtCore.QPointF(*top), QtCore.QPointF(*bot))

        # Yatay çizgiler (1..ROWS-1)
        for r in range(1, ROWS):
            t = r / ROWS
            left = lerp(self.TL, self.BL, t)
            right = lerp(self.TR, self.BR, t)
            p.drawLine(QtCore.QPointF(*left), QtCore.QPointF(*right))

        # --- Top noktasından 4 köşeye perspektif çizgileri ---
        if self.ball is not None:
            bx, by = self.ball

            ray_pen = QtGui.QPen(QtGui.QColor(255, 0, 0))
            ray_pen.setWidth(max(2, self.th))
            ray_pen.setCosmetic(True)
            p.setPen(ray_pen)

            for (x, y) in [self.TL, self.TR, self.BR, self.BL]:
                p.drawLine(
                    QtCore.QPointF(bx, by),
                    QtCore.QPointF(x, y)
                )

            # Topu hafif vurgula
            p.setBrush(QtGui.QColor(255, 255, 0, 120))
            p.drawEllipse(QtCore.QPointF(bx, by), self.th * 2.0, self.th * 2.0)
            p.setBrush(QtCore.Qt.NoBrush)


# ==================== main ====================

def main():
    args = sys.argv[1:]

    # Yüksek DPI düzeltmeleri
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    passthrough = ("--pass" in args)
    silent = ("--silent" in args)
    test = ("--test" in args)

    clean = [a for a in args if not a.startswith("--")]
    nums = [parse_int(a, None) for a in clean]
    nums = [n for n in nums if n is not None]

    ball = None

    if test:
        # Test modunda sahte noktalar
        points = [(0, 0), (0, 0), (0, 0), (0, 0)]
        th = nums[0] if len(nums) >= 1 else 6
        sec = nums[1] if len(nums) >= 2 else 0
    else:
        if len(nums) < 8:
            print(
                "Kullanım: python overlay_rect.py "
                "x1 y1 x2 y2 x3 y3 x4 y4 [ball_x ball_y] "
                "[thickness=6] [seconds=0] [--pass] [--silent] [--test]"
            )
            sys.exit(1)

        points = [
            (nums[0], nums[1]),
            (nums[2], nums[3]),
            (nums[4], nums[5]),
            (nums[6], nums[7]),
        ]

        if len(nums) >= 10:
            ball = (nums[8], nums[9])
            th = nums[10] if len(nums) >= 11 else 6
            sec = nums[11] if len(nums) >= 12 else 0
        else:
            ball = None
            th = nums[8] if len(nums) >= 9 else 6
            sec = nums[9] if len(nums) >= 10 else 0

    # Süre verilmişse, güvenlik için ek "öldürücü" thread
    if sec and sec > 0:
        def killer(t):
            time.sleep(t)
            # Her ihtimale karşı süreç tamamen kapansın
            sys.exit(0)

        threading.Thread(target=killer, args=(int(sec) + 2,), daemon=True).start()

    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setQuitOnLastWindowClosed(True)

    ov = Overlay(points, ball=ball,
                 thickness=th, seconds=sec,
                 passthrough=passthrough, test_mode=test)
    ov.silent = silent

    ov.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
