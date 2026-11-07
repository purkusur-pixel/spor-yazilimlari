# overlay_half10.py
# Kullanım:
# python overlay_half10.py x3 y3 x4 y4 [thickness=3] [seconds=0] [--pass]
#
# Merkez = (x3,y3) ile (x4,y4) orta noktası
# Yarım daire: kale çizgisine dik, "saha tarafı" (aşağı yön) varsayılan
# 10 eş dilim => 9 radyal çizgi

import sys, math, time, threading
from PyQt5 import QtCore, QtGui, QtWidgets

def v_add(a,b): return (a[0]+b[0], a[1]+b[1])
def v_sub(a,b): return (a[0]-b[0], a[1]-b[1])
def v_mul(a,s): return (a[0]*s, a[1]*s)
def v_len(a): return math.hypot(a[0], a[1])
def v_norm(a):
    l = v_len(a)
    return (1.0, 0.0) if l < 1e-6 else (a[0]/l, a[1]/l)

class Overlay(QtWidgets.QWidget):
    def __init__(self, P3, P4, thickness=3, seconds=0, passthrough=False):
        super().__init__()
        self.P3 = P3
        self.P4 = P4
        self.th = max(1, int(thickness))
        self.sec = max(0, int(seconds))
        self.passthrough = bool(passthrough)

        screen = QtGui.QGuiApplication.primaryScreen()
        geo = screen.geometry() if screen else QtCore.QRect(0,0,1920,1080)
        self.setGeometry(geo)

        flags = QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        if self.passthrough:
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            self.setFocusPolicy(QtCore.Qt.NoFocus)
            self.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)

        if self.sec > 0:
            QtCore.QTimer.singleShot(self.sec * 1000, self.close)

        self.showFullScreen()
        self.raise_()

    def keyPressEvent(self, ev):
        if ev.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Q):
            self.close()

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Merkez
        C = v_mul(v_add(self.P3, self.P4), 0.5)

        # Kale çizgisi doğrultusu (P3->P4)
        u = v_norm(v_sub(self.P4, self.P3))

        # Kale çizgisine dik normal (2 aday var). Biz varsayılan olarak "aşağı" bakanı seçeceğiz.
        n1 = (-u[1], u[0])
        n2 = (u[1], -u[0])
        n = n1 if n1[1] > n2[1] else n2   # ekranda y aşağı büyür -> y'si büyük olan "aşağı"

        base_ang = math.atan2(n[1], n[0])  # rad

        # Yarıçap: kale çizgisinin uzunluğuna göre otomatik
        goal_w = v_len(v_sub(self.P4, self.P3))
        R = max(60.0, goal_w * 3.0)  # isterse 3.0'ı değiştir

        # Penler
        arc_pen = QtGui.QPen(QtGui.QColor(0, 255, 255, 220))
        arc_pen.setWidth(max(2, self.th))
        arc_pen.setCosmetic(True)

        line_pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 230))
        line_pen.setWidth(max(2, self.th))
        line_pen.setCosmetic(True)

        # P3 ve P4'ten merkeze (C) çizgiler
        p3p4_pen = QtGui.QPen(QtGui.QColor(255, 0, 0, 220))
        p3p4_pen.setWidth(max(2, self.th))
        p3p4_pen.setCosmetic(True)

        p.setPen(p3p4_pen)
        p.drawLine(QtCore.QPointF(self.P3[0], self.P3[1]), QtCore.QPointF(C[0], C[1]))
        p.drawLine(QtCore.QPointF(self.P4[0], self.P4[1]), QtCore.QPointF(C[0], C[1]))

        # Yarım daire yayı: base_ang - 90° ... +90°
        rect = QtCore.QRectF(C[0]-R, C[1]-R, 2*R, 2*R)
        start_deg = (base_ang * 180.0 / math.pi) - 90.0
        span_deg = 180.0

        p.setPen(arc_pen)
        p.drawArc(rect, int(start_deg*16), int(span_deg*16))

        # 10 eş parça => 9 çizgi (18° aralık)
        p.setPen(line_pen)
        step = 180.0 / 10.0  # 18
        for k in range(1, 10):
            deg = -90.0 + k * step
            ang = base_ang + deg * math.pi / 180.0
            ex = C[0] + R * math.cos(ang)
            ey = C[1] + R * math.sin(ang)
            p.drawLine(QtCore.QPointF(C[0], C[1]), QtCore.QPointF(ex, ey))

        # Merkez nokta
        p.setBrush(QtGui.QColor(255, 0, 0, 180))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(C[0], C[1]), self.th*1.6, self.th*1.6)

def main():
    args = sys.argv[1:]
    passthrough = "--pass" in args
    nums = []
    for a in args:
        if a.startswith("--"): 
            continue
        try: nums.append(int(a))
        except: pass

    if len(nums) < 4:
        print("Kullanım: python overlay_half10.py x3 y3 x4 y4 [thickness] [seconds] [--pass]")
        sys.exit(1)

    x3,y3,x4,y4 = nums[0],nums[1],nums[2],nums[3]
    thickness = nums[4] if len(nums) >= 5 else 3
    seconds   = nums[5] if len(nums) >= 6 else 0

    if seconds > 0:
        def killer(t):
            time.sleep(t+2)
            sys.exit(0)
        threading.Thread(target=killer, args=(seconds,), daemon=True).start()

    app = QtWidgets.QApplication(sys.argv)
    ov = Overlay((x3,y3),(x4,y4), thickness=thickness, seconds=seconds, passthrough=passthrough)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
