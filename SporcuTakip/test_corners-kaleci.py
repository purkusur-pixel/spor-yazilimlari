# test_corners-kaleci.py
import sys, argparse, socket, re, os
from PyQt5 import QtCore, QtGui, QtWidgets

DOT_SIZE_DEFAULT = 10

# ==========================================
# 1. BÖLÜM: LOG DOSYASI OKUYUCU (Ball.txt)
# ==========================================
class BallLogParser:
    def __init__(self, filepath):
        self.data = {}  # { frame_no: (center_x, center_y) }
        self.load_data(filepath)

    def load_data(self, filepath):
        if not os.path.exists(filepath):
            print(f"[UYARI] '{filepath}' bulunamadi. Otomatik takip calismayacak.")
            return

        print(f"[BILGI] '{filepath}' analiz ediliyor...")
        count = 0
        # Regex: [0005360] ... box=(8, 623, 31, 648)
        # 1. Grup: Frame, 2-5. Gruplar: x1, y1, x2, y2
        regex = re.compile(r'\[(\d+)\] .*box=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = regex.search(line)
                    if match:
                        frame = int(match.group(1))
                        x1 = int(match.group(2))
                        y1 = int(match.group(3))
                        x2 = int(match.group(4))
                        y2 = int(match.group(5))

                        # Dikdörtgenin orta noktasını hesapla
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2

                        self.data[frame] = (center_x, center_y)
                        count += 1
            print(f"[BILGI] {len(self.data)} farkli frame icin top verisi yuklendi.")
        except Exception as e:
            print(f"[HATA] Dosya okunurken hata: {e}")

    def get_position(self, frame_no):
        return self.data.get(frame_no)


# ==========================================
# 2. BÖLÜM: SOCKET DINLEYICI THREAD
# ==========================================
class SocketListener(QtCore.QThread):
    frame_received = QtCore.pyqtSignal(int)  # Frame nosunu GUI'ye sinyal olarak atar

    def __init__(self, socket_obj):
        super().__init__()
        self.sock = socket_obj
        self.running = True

    def run(self):
        if not self.sock:
            return
        
        buffer = ""
        while self.running:
            try:
                # C#'tan veri bekle (Bloke edici işlem)
                data = self.sock.recv(1024)
                if not data:
                    break
                
                text = data.decode("utf-8")
                buffer += text
                
                # Satır satır işle "FRAME:123\n"
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line.startswith("FRAME:"):
                        try:
                            frame_str = line.split(":")[1]
                            frame_no = int(frame_str)
                            self.frame_received.emit(frame_no)
                        except ValueError:
                            pass
            except Exception as e:
                # Socket kapandıysa veya hata varsa döngüden çık
                break
    
    def stop(self):
        self.running = False


# ==========================================
# 3. BÖLÜM: ANA SINIFLAR
# ==========================================
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
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
        )

        self.resize(140, max(40, dot_size + 8))
        self.move(int(x), int(y))
        self._drag_off = None

        self.label = QtWidgets.QLabel(self)
        self.label.move(self.dot_size + 6, 0)
        self.label.setStyleSheet(
            "color: yellow; font-weight: bold; background: transparent;"
        )
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.update_label()

    def dot_center_global(self) -> QtCore.QPoint:
        local_center = QtCore.QPoint(self.dot_size // 2, self.height() // 2)
        return self.mapToGlobal(local_center)
    
    # Otomatik hareket için eklendi
    def move_center_to(self, cx, cy):
        local_center_x = self.dot_size // 2
        local_center_y = self.height() // 2
        
        # Global merkezden pencere sol-üst köşesini hesapla
        new_x = cx - local_center_x
        new_y = cy - local_center_y
        
        self.move(int(new_x), int(new_y))
        self.update_label()
        # Koordinatı C#'a geri bildir (senkronizasyon için)
        self.moved.emit(self.idx, int(cx), int(cy))

    def update_label(self):
        c = self.dot_center_global()
        prefix = "TOP" if self.idx == 5 else str(self.idx)
        self.label.setText(f"({int(c.x())}, {int(c.y())}) •{prefix}")
        self.label.adjustSize()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 200), 2))
        
        # 5. Nokta (Top) Yeşil olsun, diğerleri Kırmızı
        if self.idx == 5:
            p.setBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0))) # Yeşil
        else:
            p.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0))) # Kırmızı
            
        p.drawEllipse(
            1,
            (self.height() - self.dot_size) // 2,
            self.dot_size,
            self.dot_size,
        )

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
    def __init__(self, sock_client, dot_size, screen_geo, margin, ball_file):
        super().__init__()
        self.sock = sock_client
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setGeometry(-2000, -2000, 1, 1)
        self.points = []

        # Ball log dosyasını yükle
        self.ball_parser = BallLogParser(ball_file)
        self.listener = None

        W, H = 140, max(40, dot_size + 8)
        cx = screen_geo.center().x()
        cy = screen_geo.center().y()

        offsets = [
            (-150, -100),  # 1
            (150, -100),   # 2
            (-150, 100),   # 3
            (150, 100),    # 4
            (0, 0),        # 5 (Top)
        ]

        def clamp(val, vmin, vmax):
            return max(vmin, min(val, vmax))

        x_min = screen_geo.left() + margin
        y_min = screen_geo.top() + margin
        x_max = screen_geo.right() - W - margin
        y_max = screen_geo.bottom() - H - margin

        starts = []
        for dx, dy in offsets:
            sx = clamp(cx + dx - W // 2, x_min, x_max)
            sy = clamp(cy + dy - H // 2, y_min, y_max)
            starts.append((sx, sy))

        for i, (x, y) in enumerate(starts, 1):
            pw = PointWindow(x, y, i, dot_size)
            pw.moved.connect(self.on_point_moved)
            pw.show()
            pw.raise_()
            pw.activateWindow()
            self.points.append(pw)

        # Socket bağlantısı ve Listener başlatma
        if self.sock and not self.sock.sock:
            if self.sock.connect():
                print("[BILGI] Socket baglantisi basarili. Dinleyici baslatiliyor...")
                self.listener = SocketListener(self.sock.sock)
                self.listener.frame_received.connect(self.on_frame_sync)
                self.listener.start()
            else:
                print("[HATA] Socket baglantisi kurulamadi!")

        self.flush_all()

    def on_frame_sync(self, frame_no):
        """C#'tan frame numarası geldiğinde çalışır."""
        pos = self.ball_parser.get_position(frame_no)
        if pos:
            cx, cy = pos
            # 5. Nokta (listede index 4) top noktasıdır
            top_noktasi = self.points[4]
            top_noktasi.move_center_to(cx, cy)

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
            if self.listener:
                self.listener.stop()
            QtWidgets.QApplication.quit()


def parse_args():
    ap = argparse.ArgumentParser(
        description="5 sürüklenebilir nokta (TCP ile koordinat yayınlar ve Ball.txt okur)."
    )
    ap.add_argument(
        "--socket",
        type=str,
        required=True,
        help="host:port (örn. 127.0.0.1:5055)",
    )
    ap.add_argument(
        "--dot",
        type=int,
        default=DOT_SIZE_DEFAULT,
        help="Nokta çapı (px).",
    )
    ap.add_argument(
        "--screen",
        choices=["primary", "cursor"],
        default="primary",
        help="Hangi ekran: primary|cursor",
    )
    ap.add_argument(
        "--margin",
        type=int,
        default=20,
        help="Ekran kenar payı.",
    )
    # Ball.txt varsayılan olarak aynı klasörde
    ap.add_argument(
        "--ball",
        type=str,
        default="ball.txt",
        help="Top takip log dosyasi yolu.",
    )
    return ap.parse_args()


def pick_screen_geometry(mode: str) -> QtCore.QRect:
    app = QtWidgets.QApplication.instance()
    if mode == "cursor":
        s = app.screenAt(QtGui.QCursor.pos())
        if s:
            return s.availableGeometry()
    return app.primaryScreen().availableGeometry()


def main():
    # Yüksek DPI
    QtWidgets.QApplication.setAttribute(
        QtCore.Qt.AA_EnableHighDpiScaling, True
    )
    QtWidgets.QApplication.setAttribute(
        QtCore.Qt.AA_UseHighDpiPixmaps, True
    )

    args = parse_args()
    try:
        host, port = args.socket.split(":")
        port = int(port)
    except ValueError:
        print("Hata: Socket argümanı 'host:port' formatında olmalı.")
        sys.exit(1)

    app = QtWidgets.QApplication(sys.argv)

    sock_client = SocketClient(host, port)
    
    # Connect artık controller içinde yapılıyor ki thread başlatılabilsin

    geo = pick_screen_geometry(args.screen)
    ctrl = Controller(sock_client, args.dot, geo, args.margin, args.ball)
    ctrl.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()