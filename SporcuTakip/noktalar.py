import sys
from PyQt5 import QtCore, QtGui, QtWidgets

DOT_SIZE = 5

class PointWindow(QtWidgets.QWidget):
    moved = QtCore.pyqtSignal(int, int)  # global coord

    def __init__(self, x, y, idx):
        super().__init__(None)
        self.idx = idx
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
        )
        # Nokta + yazı alanı
        self.resize(120, 40)
        self.move(x, y)
        self._drag_off = None

        # Koordinat etiketi
        self.label = QtWidgets.QLabel(self)
        self.label.move(DOT_SIZE + 5, 0)
        self.label.setStyleSheet("color: yellow; font-weight: bold; background: transparent;")

        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.update_label()

    # --- ÖNEMLİ: Noktanın GERÇEK MERKEZİ (global ekran koordinatı) ---
    def dot_center_global(self) -> QtCore.QPoint:
        local_center = QtCore.QPoint(DOT_SIZE // 2, self.height() // 2)
        return self.mapToGlobal(local_center)

    def update_label(self):
        c = self.dot_center_global()
        cx, cy = int(c.x()), int(c.y())
        self.label.setText(f"({cx}, {cy})  •{self.idx}")
        self.label.adjustSize()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        p.setPen(QtCore.Qt.NoPen)
        # Daireyi solda, dikeyde ortalanmış çiziyoruz
        p.drawEllipse(0, (self.height()-DOT_SIZE)//2, DOT_SIZE, DOT_SIZE)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self._drag_off = ev.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        if self._drag_off is not None:
            new_top_left = ev.globalPos() - self._drag_off
            self.move(new_top_left)
            self.update_label()
            c = self.dot_center_global()
            print(f"Nokta {self.idx} (MERKEZ): ({int(c.x())}, {int(c.y())})")

    def mouseReleaseEvent(self, ev):
        self._drag_off = None
        self.setCursor(QtCore.Qt.OpenHandCursor)


class Controller(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setGeometry(-2000, -2000, 1, 1)
        self.points = []

        scr = QtWidgets.QApplication.primaryScreen().availableGeometry()
        w, h = scr.width(), scr.height()

        starts = [
            (int(w*0.20), int(h*0.30)),
            (int(w*0.40), int(h*0.50)),
            (int(w*0.60), int(h*0.60)),
            (int(w*0.80), int(h*0.40)),
        ]

        for i, (x, y) in enumerate(starts, 1):
            pw = PointWindow(x, y, i)
            pw.moved.connect(lambda X, Y, k=i: None)
            pw.show()
            self.points.append(pw)

    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Escape:
            QtWidgets.QApplication.quit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    ctrl = Controller()
    ctrl.show()

    # Başlangıçta merkez koordinatlarını yaz
    for p in ctrl.points:
        c = p.dot_center_global()
        print(f"Nokta {p.idx} başlangıç (MERKEZ): ({int(c.x())}, {int(c.y())})")

    sys.exit(app.exec_())
