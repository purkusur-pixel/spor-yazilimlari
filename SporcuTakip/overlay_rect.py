# overlay_rect.py — 8×3 ana ızgara + üst tek satır + altta 1x..32x + yanlarda 4×1 bloklar (dilimli)
# Kullanım:
#    python overlay_rect.py x1 y1 x2 y2 x3 y3 x4 y4 [thickness=6] [seconds=0] [--pass] [--test]

# =========================【1】KONFİG & SABİTLER=========================
import sys, os, time, math, threading, ctypes
from PyQt5 import QtWidgets, QtGui, QtCore

# GÜNCELLEME: Global klavye dinleyicisi için eklendi
import atexit
try:
    import keyboard
except ImportError:
    print("HATA: 'keyboard' kütüphanesi bulunamadı.", file=sys.stderr, flush=True)
    print("Yüklemek için: pip install keyboard", file=sys.stderr, flush=True)
    sys.exit(1)


# — Yan şerit numaraları —
SHOW_SIDE_NUMBERS = True
SIDE_NUMBER_STYLE = "pref"    # "plain" -> 1..4,  "pref" -> LT1..LT4 / RT1..RT4 / LB1..LB4 / RB1..RB4
SIDE_NUM_FG = (255, 255, 255)
SIDE_NUM_SCALE = 0.70

# Ana ızgara
COLS, ROWS = 8, 3

# Alt X etiketleri (1 tam + 1/3 bant => toplam 4 satır = 32 hücre)
DOWN_FULL_BANDS    = 1
DOWN_PARTIAL_FRAC = 1.0/ROWS
MAX_X_LABELS       = 32

# Üst tek satır
UP_PARTIAL_FRAC    = 1.0/ROWS

# Görünürlük
SHOW_NUMBERS_MIDDLE = True
SHOW_NUMBERS_TOP    = True
SHOW_X_LABELS_DOWN  = True

# Renkler
GRID_COLOR         = (255, 255, 0)
COLOR_NUM          = (255, 255, 255)
COLOR_X            = (255, 150, 0)

BORDER_MIDDLE      = (220, 60, 60)
FILL_MIDDLE        = (155, 0, 211, 80)
BORDER_TOP         = (255, 0, 0)
BORDER_DOWN_FULL   = (255, 0, 0)
BORDER_DOWN_PART   = (255, 0, 0)

# Yazı ölçekleri
FONT_SCALE_NUM = 0.80
FONT_SCALE_X   = 0.75

# Köşe 4×1 (bölmesiz) blok görselliği
SIMPLE_ZONE_BORDER = (255, 255, 0)
SIMPLE_ZONE_FILL   = (0, 255, 0, 50)
SIMPLE_ZONE_TEXT   = (255, 255, 255)

# YAN ŞERİT DİLİMLEME
SIDE_STRIPE_DIVIDER_COLOR = (0, 0, 0)
SIDE_STRIPE_DIVIDER_WIDTH_FACTOR = 0.9
SIDE_STRIPE_MARGIN_RATIO  = 0.05

# Windows hotkey (Ctrl+Alt+F8 ile kapat)
MOD_ALT, MOD_CONTROL, VK_F8 = 0x0001, 0x0002, 0x77
WM_HOTKEY, WM_CLOSE = 0x0312, 0x0010
user32 = ctypes.windll.user32
import ctypes.wintypes

# =========================【2】GEOMETRİ & HOMOGRAFİ=========================
def parse_int(s, d):
    try: return int(s)
    except: return d

def sort_cw(pts):
    cx = sum(x for x,_ in pts)/len(pts); cy = sum(y for _,y in pts)/len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1]-cy, p[0]-cx))

def normalize_quad(pts):
    pts = sorted(pts, key=lambda p: p[1])
    top = sorted(pts[:2], key=lambda p: p[0])
    bot = sorted(pts[2:], key=lambda p: p[0])
    TL, TR = top[0], top[1]; BL, BR = bot[0], bot[1]
    return TL, TR, BR, BL

def _build_A(src, dst):
    s, t = src; x, y = dst
    return [
        [-s, -t, -1,    0,  0,  0,  s*x, t*x, x],
        [ 0,  0,  0,   -s, -t, -1,  s*y, t*y, y],
    ]

def compute_homography(quad):
    TL, TR, BR, BL = quad
    srcs = [(0,0), (1,0), (1,1), (0,1)]
    dsts = [TL, TR, BR, BL]
    A = []
    for src, dst in zip(srcs, dsts):
        A.extend(_build_A(src, dst))
    M = [[*row[:8]] for row in A]
    b = [-row[8] for row in A]
    n=8
    for i in range(n):
        piv=i; mx=abs(M[i][i])
        for r in range(i+1,n):
            if abs(M[r][i])>mx: mx=abs(M[r][i]); piv=r
        if mx<1e-12: continue
        if piv!=i:
            M[i],M[piv]=M[piv],M[i]; b[i],b[piv]=b[piv],b[i]
        div=M[i][i]
        for c in range(i,n): M[i][c]/=div
        b[i]/=div
        for r in range(n):
            if r==i: continue
            f=M[r][i]
            if f==0: continue
            for c in range(i,n): M[r][c]-=f*M[i][c]
            b[r]-=f*b[i]
    h=b+[1.0]
    return [[h[0],h[1],h[2]],
            [h[3],h[4],h[5]],
            [h[6],h[7],1.0]]

def mat3_inv(M):
    a,b,c = M[0]; d,e,f = M[1]; g,h,i = M[2]
    A = e*i - f*h
    B = -(d*i - f*g)
    C = d*h - e*g
    D = -(b*i - c*h)
    E = a*i - c*g
    F = -(a*h - b*g)
    G = b*f - c*e
    H = -(a*f - c*d)
    I = a*e - b*d
    det = a*A + b*B + c*C
    if abs(det) < 1e-12: det = 1e-12
    inv = [[A/det, D/det, G/det],
           [B/det, E/det, H/det],
           [C/det, F/det, I/det]]
    return inv

def warp(H, s, t):
    x = H[0][0]*s + H[0][1]*t + H[0][2]
    y = H[1][0]*s + H[1][1]*t + H[1][2]
    w = H[2][0]*s + H[2][1]*t + H[2][2]
    if abs(w) < 1e-9: w = 1e-9
    return (x/w, y/w)

def unwarp(Hinv, x, y):
    s = Hinv[0][0]*x + Hinv[0][1]*y + Hinv[0][2]
    t = Hinv[1][0]*x + Hinv[1][1]*y + Hinv[1][2]
    w = Hinv[2][0]*x + Hinv[2][1]*y + Hinv[2][2]
    if abs(w) < 1e-9: w = 1e-9
    return (s/w, t/w)

def grid_to_st(col, row):
    return (col / COLS, row / ROWS)

def make_zone_from_grid(col0, col1, row0, row1):
    TL = grid_to_st(col0, row0)
    TR = grid_to_st(col1, row0)
    BR = grid_to_st(col1, row1)
    BL = grid_to_st(col0, row1)
    return [TL, TR, BR, BL]

# =========================【3】WIDGET & HOTKEY=========================
class Overlay(QtWidgets.QWidget):
    
    # GÜNCELLEME: Thread'ler arası güvenli iletişim için sinyal
    global_x_pressed = QtCore.pyqtSignal(int, int)

    def __init__(self, points, thickness=6, seconds=0, passthrough=False, test_mode=False):
        super().__init__()
        self.th = max(1, int(thickness))
        self.sec = max(0, int(seconds))
        self.pass_ = passthrough
        self.test = test_mode

        scr = QtGui.QGuiApplication.primaryScreen()
        vg = scr.virtualGeometry() if scr else QtCore.QRect(0,0,1920,1080)
        self.setGeometry(vg)

        if self.test:
            cx, cy = vg.x()+vg.width()//2, vg.y()+vg.height()//2
            w,h = 800,600
            pts = sort_cw([(cx-w//2,cy-h//2),(cx+w//2,cy-h//2),
                           (cx+w//2,cy+h//2),(cx-w//2,cy+h//2)])
        else:
            pts = sort_cw(points)

        self.TL,self.TR,self.BR,self.BL = normalize_quad(pts)
        self.H = compute_homography((self.TL,self.TR,self.BR,self.BL))
        self.Hinv = mat3_inv(self.H)  # ekran → (s,t)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        if self.pass_:
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            self.setFocusPolicy(QtCore.Qt.NoFocus)
            self.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)
            try:
                hwnd=int(self.winId()); GWL_EXSTYLE=-20; WS_EX_LAYERED=0x80000; WS_EX_TRANSPARENT=0x20
                getex=user32.GetWindowLongW; setex=user32.SetWindowLongW
                setex(hwnd, GWL_EXSTYLE, getex(hwnd, GWL_EXSTYLE)|WS_EX_LAYERED|WS_EX_TRANSPARENT)
            except Exception: pass

        self.showFullScreen(); self.raise_()
        if self.sec>0: QtCore.QTimer.singleShot(self.sec*1000, self.close)
        if self.pass_:
            threading.Thread(target=self._hotkey_loop, daemon=True).start()

        # GÜNCELLEME: Global 'X' tuşu kancasını (hook) başlat
        self.global_x_pressed.connect(self.handle_global_x_press)

        # Sadece pass-through modunda global hook kullan
        self.enable_global_hook = self.pass_
        if self.enable_global_hook:
            try:
                # 'x' tuşuna basıldığında trigger_global_x_hook metodunu çağır
                keyboard.on_press_key('x', self.trigger_global_x_hook)
                # Uygulama kapanırken kancaları temizle
                atexit.register(keyboard.unhook_all)
            except Exception as e:
                print(f"Global klavye kancası (hook) başlatılamadı: {e}", file=sys.stderr, flush=True)



    def _hotkey_loop(self):
        if os.name!='nt': return
        if not user32.RegisterHotKey(None,1,MOD_CONTROL|MOD_ALT,VK_F8): return
        try:
            msg=ctypes.wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg),None,0,0)!=0:
                if msg.message==WM_HOTKEY and msg.wParam==1:
                    try: user32.PostMessageW(int(self.winId()), WM_CLOSE,0,0)
                    except: pass
                    break
        finally:
            user32.UnregisterHotKey(None,1)

    # --- Bölge çözümleyici: ekran (x,y) -> bölge adı ---
    def region_name_at(self, x_screen: float, y_screen: float) -> str:
        s, t = unwarp(self.Hinv, x_screen, y_screen)
        eps = 1e-6

        

        # Üst tek satır
        if (-UP_PARTIAL_FRAC - eps) <= t < 0.0 - eps and (0.0 - eps) <= s < 1.0 + eps:
            col = int(math.floor(s * COLS))
            col = max(0, min(COLS-1, col))
            return str(24 + 1 + col)  # 25..32

        # Orta 8×3 ana ızgara
        if (0.0 - eps) <= t < 1.0 - eps and (0.0 - eps) <= s < 1.0 - eps:
            row = int(math.floor(t * ROWS))           # 0=üst, 1=orta, 2=alt
            col = int(math.floor(s * COLS))           # 0..7
            row_from_bottom = (ROWS - 1 - row)        # alttan üste
            base = 1 + row_from_bottom * COLS
            return str(base + col)                    # 1..24

        # Alt etiketli bölge: 1x..32x (1 tam bant + 1/3 bant)
        if (1.0 - eps) <= t < (2.0 + UP_PARTIAL_FRAC + eps) and (0.0 - eps) <= s < 1.0 + eps:
            if t < 2.0 - eps:
                row = int(math.floor((t - 1.0) * ROWS))  # 0..2
            else:
                row = 3                                  # kısmi bant tek satır
            col = int(math.floor(s * COLS))
            col = max(0, min(COLS-1, col))
            idx = row * COLS + col + 1                   # 1..32
            idx = max(1, min(MAX_X_LABELS, idx))
            return f"{idx}x"

        return "OUTSIDE"

    # GÜNCELLEME: Bu, 'keyboard' kütüphanesinin kendi thread'inde çalışır
    def trigger_global_x_hook(self, event):
        try:
            # Sadece 'x' tuşuna basıldığında ve event türü 'down' ise işle
            if event.event_type == keyboard.KEY_DOWN and event.name == 'x':
                # Pencere var mı ve görünür mü kontrol et
                if not self or not self.isVisible():
                    return
                # Eğer başka bir tuş basılıysa (Ctrl, Shift vs) yoksay
                if keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt') or keyboard.is_pressed('shift'):
                    return
                
                pos = ctypes.wintypes.POINT()
                user32.GetCursorPos(ctypes.byref(pos))
                # Sinyali ana GUI thread'ine gönder
                self.global_x_pressed.emit(pos.x, pos.y)
        except Exception:
            pass

    # GÜNCELLEME: Bu ana PyQt GUI thread'inde çalışır
    @QtCore.pyqtSlot(int, int)
    def handle_global_x_press(self, x_global, y_global):
        try:
            # Pencere hala geçerli mi kontrol et
            if not self or not self.isVisible():
                return
            pos_local = self.mapFromGlobal(QtCore.QPoint(x_global, y_global))
            name = self.region_name_at(pos_local.x(), pos_local.y())
            print(name, flush=True)
        except Exception:
            pass # Hata durumunda sessizce geç

    def keyPressEvent(self, e):
        # Sadece pass-through DEĞİLKEN (pencere odak alabiliyorken) X'i burada işle
        if not self.pass_ and e.key() == QtCore.Qt.Key_X:
            pos_global = QtGui.QCursor.pos()
            pos = self.mapFromGlobal(pos_global)
            name = self.region_name_at(pos.x(), pos.y())
            print(name, flush=True)
            return

        # ESC ile kapatma sadece pass-through değilken
        if not self.pass_ and e.key() == QtCore.Qt.Key_Escape:
            self.close()


    def closeEvent(self,e):
        QtWidgets.QApplication.quit(); return super().closeEvent(e)

# =========================【4】METİN ÇİZİMİ=========================
    def _draw_text_shadowed(self, p, x, y, text, fg, size_mul=1.0, bold=True, shadow=True):
        font = p.font()
        font.setPointSize(max(10, int(self.th * 2.2 * size_mul)))
        font.setBold(bold)
        p.setFont(font)
        fm = QtGui.QFontMetricsF(font)
        w = fm.horizontalAdvance(text)
        h = fm.height()
        rect = QtCore.QRectF(x - w/2, y - h/2, w, h)
        if shadow:
            sp = QtGui.QPen(QtGui.QColor(0,0,0)); sp.setWidth(4); p.setPen(sp)
            p.drawText(rect.translated(2,2), QtCore.Qt.AlignCenter, text)
        p.setPen(QtGui.QColor(*fg))
        p.drawText(rect, QtCore.Qt.AlignCenter, text)

# =========================【5】ANA BAND ÇİZİMİ=========================
    def _draw_band(self, p: QtGui.QPainter, t0: float, height_frac: float, start_idx: int,
                   draw_numbers: bool=True, number_color=COLOR_NUM, number_from_bottom: bool=False,
                   x_start: int=None, x_label_cap: int=None,
                   border_color=(255,0,0), fill_color=None):
        gpen = QtGui.QPen(QtGui.QColor(*GRID_COLOR))
        gpen.setStyle(QtCore.Qt.DashLine); gpen.setCosmetic(True)
        gpen.setWidth(max(1, self.th-2)); p.setPen(gpen)
        for i in range(1, COLS):
            s=i/COLS
            p.drawLine(QtCore.QPointF(*warp(self.H,s,t0)),
                       QtCore.QPointF(*warp(self.H,s,t0+height_frac)))
        for j in range(1, ROWS):
            y=j/ROWS
            if y < height_frac - 1e-9:
                p.drawLine(QtCore.QPointF(*warp(self.H,0.0,t0+y)),
                           QtCore.QPointF(*warp(self.H,1.0,t0+y)))

        pen_border = QtGui.QPen(QtGui.QColor(*border_color)); pen_border.setCosmetic(True); pen_border.setWidth(self.th)
        p.setPen(pen_border)
        corners=[warp(self.H,0.0,t0), warp(self.H,1.0,t0),
                 warp(self.H,1.0,t0+height_frac), warp(self.H,0.0,t0+height_frac)]
        poly=QtGui.QPolygonF([QtCore.QPointF(*c) for c in corners])
        if fill_color is not None:
            r,g,b,a = fill_color; p.setBrush(QtGui.QColor(r,g,b,a))
        else:
            p.setBrush(QtCore.Qt.NoBrush)
        p.drawPolygon(poly)

        xi  = x_start if x_start is not None else None

        full_rows = int(height_frac*ROWS + 1e-9)
        residual = height_frac*ROWS - full_rows

        for j in range(full_rows):
            coords=[]
            for i in range(COLS):
                s=(i+0.5)/COLS; t=t0+(j+0.5)/ROWS
                coords.append((i,)+warp(self.H,s,t))

            row_base = start_idx + ((full_rows-1 - j)*COLS if number_from_bottom else j*COLS)

            for k,(i,cx,cy) in enumerate(coords):
                if draw_numbers:
                    lab = row_base + k
                    self._draw_text_shadowed(p, cx, cy, str(lab), fg=number_color, size_mul=FONT_SCALE_NUM, bold=True)
                if xi is not None and (x_label_cap is None or xi - x_start < x_label_cap):
                    self._draw_text_shadowed(p, cx, cy, f"{xi}x", fg=COLOR_X, size_mul=FONT_SCALE_X, bold=True, shadow=False)
                    xi += 1

        if residual > 1e-6:
            j = full_rows
            cells = int(round(residual * COLS)); cells = max(1, min(COLS, cells))
            coords=[]
            for i in range(cells):
                s=(i+0.5)/COLS; t=t0+(j+0.5)/ROWS
                coords.append((i,)+warp(self.H,s,t))

            row_base = start_idx + full_rows*COLS
            for k,(i,cx,cy) in enumerate(coords):
                if draw_numbers:
                    lab = row_base + k
                    self._draw_text_shadowed(p, cx, cy, str(lab), fg=number_color, size_mul=FONT_SCALE_NUM, bold=True)
                if xi is not None and (x_label_cap is None or xi - x_start < x_label_cap):
                    self._draw_text_shadowed(p, cx, cy, f"{xi}x", fg=COLOR_X, size_mul=FONT_SCALE_X, bold=True, shadow=False)
                    xi += 1

        total_cells = full_rows*COLS + (int(round(residual*COLS)) if residual>1e-6 else 0)
        nxt = start_idx + (total_cells if draw_numbers else 0)
        return nxt if draw_numbers else start_idx, (xi if x_start is not None else None)

# =========================【6】KÖŞE 4×1 DİKDÖRTGENLER + DİLİM ÇİZGİLERİ=========================
    def _draw_zone_simple(self, p, quad, label=None):
        pen = QtGui.QPen(QtGui.QColor(*SIMPLE_ZONE_BORDER))
        pen.setCosmetic(True)
        pen.setWidth(max(1, self.th - 1))
        p.setPen(pen)

        r,g,b,a = SIMPLE_ZONE_FILL
        p.setBrush(QtGui.QColor(r,g,b,a))

        poly_pts = [QtCore.QPointF(*warp(self.H, *st)) for st in quad]
        poly = QtGui.QPolygonF(poly_pts)
        p.drawPolygon(poly)
        p.setBrush(QtCore.Qt.NoBrush)

        if label:
            cx = sum(pt.x() for pt in poly_pts) / 4.0
            cy = sum(pt.y() for pt in poly_pts) / 4.0
            self._draw_text_shadowed(p, cx, cy, label, fg=SIMPLE_ZONE_TEXT, size_mul=0.75, bold=True)

    def _subzones_def(self):
        return [
            ("", make_zone_from_grid(-1, 0, -1, 3)),  # Sol-üst 4×1
            ("", make_zone_from_grid( 8, 9, -1, 3)),  # Sağ-üst 4×1
            ("", make_zone_from_grid(-1, 0,  3, 7)),  # Sol-alt 4×1
            ("", make_zone_from_grid( 8, 9,  3, 7)),  # Sağ-alt 4×1
        ]

    def _draw_side_dividers(self, p: QtGui.QPainter):
        pen = QtGui.QPen(QtGui.QColor(*SIDE_STRIPE_DIVIDER_COLOR))
        pen.setCosmetic(True)
        pen.setWidth(max(2, self.th - 2))
        p.setPen(pen)

        side_w = 1.0 / COLS
        inset = side_w * SIDE_STRIPE_MARGIN_RATIO
        short_len = side_w * SIDE_STRIPE_DIVIDER_WIDTH_FACTOR

        sL0 = -side_w + (side_w - short_len)/2.0 + inset
        sL1 = sL0 + short_len - 2*inset
        sLmid = (sL0 + sL1) / 2.0

        sR0 = 1.0 + (side_w - short_len)/2.0 + inset
        sR1 = sR0 + short_len - 2*inset
        sRmid = (sR0 + sR1) / 2.0

        top_rows_boundary = [-1, 0, 1, 2, 3]
        bot_rows_boundary = [3, 4, 5, 6, 7]

        def draw_h_short(s0, s1, t_row):
            t = t_row / ROWS
            p.drawLine(QtCore.QPointF(*warp(self.H, s0, t)),
                       QtCore.QPointF(*warp(self.H, s1, t)))

        for r in top_rows_boundary:
            draw_h_short(sL0, sL1, r)
            draw_h_short(sR0, sR1, r)
        for r in bot_rows_boundary:
            draw_h_short(sL0, sL1, r)
            draw_h_short(sR0, sR1, r)

        if SHOW_SIDE_NUMBERS:
            def label_for(which, idx):
                return f"{which}{idx}" if SIDE_NUMBER_STYLE=="pref" else str(idx)
            def draw_num(cx, cy, text):
                self._draw_text_shadowed(p, cx, cy, text, fg=SIDE_NUM_FG, size_mul=SIDE_NUM_SCALE, bold=True)

            top_centers = [(-1+0.5)/ROWS, (0+0.5)/ROWS, (1+0.5)/ROWS, (2+0.5)/ROWS]
            bot_centers = [(3+0.5)/ROWS, (4+0.5)/ROWS, (5+0.5)/ROWS, (6+0.5)/ROWS]

            for i, tmid in enumerate(top_centers, start=1):
                x,y = warp(self.H, sLmid, tmid); draw_num(x, y, label_for("LT", i))
            for i, tmid in enumerate(top_centers, start=1):
                x,y = warp(self.H, sRmid, tmid); draw_num(x, y, label_for("RT", i))
            for i, tmid in enumerate(bot_centers, start=1):
                x,y = warp(self.H, sLmid, tmid); draw_num(x, y, label_for("LB", i))
            for i, tmid in enumerate(bot_centers, start=1):
                x,y = warp(self.H, sRmid, tmid); draw_num(x, y, label_for("RB", i))

# =========================【7】PAINT=========================
    def paintEvent(self, ev: QtGui.QPaintEvent):
        # GÜNCELLEME: Izgaranın her zaman çizilmesi için bu kontrol kaldırıldı/devre dışı bırakıldı.
        # if getattr(self, "silent", False):
        #     return  # hiçbir şey çizme; pencere saydam ve odak bizde
        
        # if getattr(self, "silent", False):
        #     return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 35))

        # 1) ORTA bant (1..24) — alttan üste numaralandır
        nxt, _ = self._draw_band(
            p, t0=0.0, height_frac=1.0, start_idx=1,
            draw_numbers=SHOW_NUMBERS_MIDDLE, number_color=COLOR_NUM, number_from_bottom=True,
            x_start=None, x_label_cap=None,
            border_color=BORDER_MIDDLE, fill_color=FILL_MIDDLE
        )

        # 2) ÜST tek satır (25..32)
        nxt, _ = self._draw_band(
            p, t0=-UP_PARTIAL_FRAC, height_frac=UP_PARTIAL_FRAC, start_idx=nxt,
            draw_numbers=SHOW_NUMBERS_TOP, number_color=COLOR_NUM, number_from_bottom=False,
            x_start=None, x_label_cap=None,
            border_color=BORDER_TOP, fill_color=None
        )

        # 3) ALT — 1x..32x
        t = 1.0
        x_counter = 1 if SHOW_X_LABELS_DOWN else None
        for _ in range(DOWN_FULL_BANDS):
            if not (SHOW_X_LABELS_DOWN and x_counter is not None and x_counter <= MAX_X_LABELS):
                break
            cap = MAX_X_LABELS - x_counter + 1
            if cap <= 0: break
            _, x_counter = self._draw_band(
                p, t0=t, height_frac=1.0, start_idx=0,
                draw_numbers=False, number_color=COLOR_NUM, number_from_bottom=False,
                x_start=x_counter, x_label_cap=cap,
                border_color=BORDER_DOWN_FULL, fill_color=None
            )
            t += 1.0
        if DOWN_PARTIAL_FRAC > 1e-6 and (SHOW_X_LABELS_DOWN and x_counter is not None and x_counter <= MAX_X_LABELS):
            cap = MAX_X_LABELS - x_counter + 1
            if cap > 0:
                _, x_counter = self._draw_band(
                    p, t0=t, height_frac=DOWN_PARTIAL_FRAC, start_idx=0,
                    draw_numbers=False, number_color=COLOR_NUM, number_from_bottom=False,
                    x_start=x_counter, x_label_cap=cap,
                    border_color=BORDER_DOWN_PART, fill_color=None
                )

        # 4) Köşe 4×1 bölgeler
        for label, quad in self._subzones_def():
            self._draw_zone_simple(p, quad, label=label)

        # 5) Yan şerit dilim çizgileri
        self._draw_side_dividers(p)

# =========================【8】MAIN=========================
def main():
    args=sys.argv[1:]
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    passthrough = ("--pass" in args)
    silent      = ("--silent" in args)
    test        = ("--test" in args)
    clean=[a for a in args if not a.startswith("--")]

    nums=[parse_int(a,None) for a in clean]; nums=[n for n in nums if n is not None]

    if test:
        points=[(0,0),(0,0),(0,0),(0,0)]
        th=nums[0] if len(nums)>=1 else 6
        sec=nums[1] if len(nums)>=2 else 0
    else:
        if len(nums)<8:
            print("Kullanım: python overlay_rect.py x1 y1 x2 y2 x3 y3 x4 y4 [thickness=6] [seconds=0] [--pass] [--test]")
            sys.exit(1)
        points=[(nums[0],nums[1]),(nums[2],nums[3]),(nums[4],nums[5]),(nums[6],nums[7])]
        th=nums[8] if len(nums)>=9 else 6
        sec=nums[9] if len(nums)>=10 else 0

    if sec and sec>0:
        def w(t): time.sleep(t); os._exit(0)
        threading.Thread(target=w, args=(int(sec)+2,), daemon=True).start()

    app=QtWidgets.QApplication(sys.argv); QtWidgets.QApplication.setQuitOnLastWindowClosed(True)
    ov=Overlay(points, thickness=th, seconds=sec, passthrough=passthrough, test_mode=test)
    
    # Bu satır artık ızgarayı gizlemeyecek, ancak zararı da yok.
    ov.silent = silent

    ov.show(); sys.exit(app.exec_())

if __name__=="__main__":
    main()