# test_corners_tcp.py
import sys, argparse, socket
from PyQt5 import QtCore, QtGui, QtWidgets

DOT_SIZE_DEFAULT = 10

class SocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((self.host, self.port))
            self.sock = s
            return True
        except Exception:
            self.sock = None
            return False

    def send_point(self, idx, cx, cy):
        if not self.sock:
            return
        try:
            msg = f"{idx},{cx},{cy}\n".encode("utf-8")
            self.sock.sendall(msg)
        except Exception:
            # bağlantı koptuysa bir daha denemeyelim (basit)
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

class PointWindow(QtWidgets.QWidget):
    moved = QtCore.pyqtSignal(int, int, int)  # (idx, cx, cy)

    def __init__(self, x, y, idx, dot_size):
        super().__init__(None)
        self.idx = idx
        self.dot_size = dot_size
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.resize(120, max(40, dot_size + 8))
        self.move(int(x), int(y))
        self._drag_off = None

        self.label = QtWidgets.QLabel(self)
        self.label.move(self.dot_size + 6, 0)
        self.label.setStyleSheet("color: yellow; font-weight: bold; background: transparent;")
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.update_label()

    def dot_center_global(self) -> QtCore.QPoint:
        local_center = QtCore.QPoint(self.dot_size // 2, self.height() // 2)
        return self.mapToGlobal(local_center)

    def update_label(self):
        c = self.dot_center_global()
        self.label.setText(f"({int(c.x())}, {int(c.y())}) •{self.idx}")
        self.label.adjustSize()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor(0,0,0,200), 2))
        p.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        p.drawEllipse(1, (self.height()-self.dot_size)//2, self.dot_size, self.dot_size)

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
            self.moved.emit(self.idx, int(c.x()), int(c.y()))

    def mouseReleaseEvent(self, ev):
        self._drag_off = None
        self.setCursor(QtCore.Qt.OpenHandCursor)

class Controller(QtWidgets.QWidget):
    def __init__(self, sock_client, dot_size, screen_geo, margin):
        super().__init__()
        self.sock = sock_client
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setGeometry(-2000, -2000, 1, 1)
        self.points = []

        # 4 noktayı merkezin etrafına ser
        W, H = 120, max(40, dot_size + 8)
        cx = screen_geo.center().x()
        cy = screen_geo.center().y()
        offsets = [(-150, -100), (150, -100), (-150, 100), (150, 100)]
        def clamp(val, vmin, vmax): return max(vmin, min(val, vmax))
        x_min = screen_geo.left() + margin
        y_min = screen_geo.top() + margin
        x_max = screen_geo.right() - W - margin
        y_max = screen_geo.bottom() - H - margin

        starts = []
        for dx, dy in offsets:
            sx = clamp(cx + dx - W//2, x_min, x_max)
            sy = clamp(cy + dy - H//2, y_min, y_max)
            starts.append((sx, sy))

        for i, (x, y) in enumerate(starts, 1):
            pw = PointWindow(x, y, i, dot_size)
            pw.moved.connect(self.on_point_moved)
            pw.show(); pw.raise_(); pw.activateWindow()
            self.points.append(pw)

        # bağlantı kur ve ilk koordinatları gönder
        if self.sock and not self.sock.sock:
            self.sock.connect()
        self.flush_all()

    def on_point_moved(self, idx, cx, cy):
        if self.sock and self.sock.sock:
            self.sock.send_point(idx, cx, cy)

    def flush_all(self):
        for pw in self.points:
            c = pw.dot_center_global()
            if self.sock and self.sock.sock:
                self.sock.send_point(pw.idx, int(c.x()), int(c.y()))

    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Escape:
            QtWidgets.QApplication.quit()

def parse_args():
    ap = argparse.ArgumentParser(description="4 sürüklenebilir nokta (TCP ile koordinat yayınlar).")
    ap.add_argument("--socket", type=str, required=True, help="host:port (örn. 127.0.0.1:5055)")
    ap.add_argument("--dot", type=int, default=DOT_SIZE_DEFAULT, help="Nokta çapı (px).")
    ap.add_argument("--screen", choices=["primary", "cursor"], default="primary",
                    help="Hangi ekran: primary|cursor")
    ap.add_argument("--margin", type=int, default=20, help="Ekran kenar payı.")
    return ap.parse_args()

def pick_screen_geometry(mode: str) -> QtCore.QRect:
    app = QtWidgets.QApplication.instance()
    if mode == "cursor":
        s = app.screenAt(QtGui.QCursor.pos())
        if s: return s.availableGeometry()
    return app.primaryScreen().availableGeometry()

def main():
    # Yüksek DPI
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    args = parse_args()
    host, port = args.socket.split(":")
    port = int(port)

    app = QtWidgets.QApplication(sys.argv)

    sock_client = SocketClient(host, port)
    sock_client.connect()  # C# önce başlıyorsa burası başarılı olur

    geo = pick_screen_geometry(args.screen)
    ctrl = Controller(sock_client, args.dot, geo, args.margin)
    ctrl.show()

    # ilk değerleri console'a da basmak istersen:
    for p in ctrl.points:
        c = p.dot_center_global()
        # print(f"Nokta {p.idx} başlangıç: ({int(c.x())}, {int(c.y())})")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
