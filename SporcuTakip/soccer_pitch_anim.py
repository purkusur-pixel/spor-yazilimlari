# 1) -*- coding: utf-8 -*-
"""
field_runner_report.py
- Saha CANVAS'ında A/B/C sporcularının koşusunu canlı gösterir (isimli noktalar)
- Modlar: (1) Simülasyon (dairesel)  (2) CSV oynatma (timestamp, player, x,y veya lat,lon)
- "Hesapla": STATSports-benzeri metrikler (Toplam Mesafe, Max Hız, vb.)
- "PDF İndir" / "Excel İndir": rapor çıktıları (ReportLab, pandas)
- "Başlat/Durdur" animasyon; "Yeniden" başlangıca dön.

Önemli Notlar:
- PDF kart yerleşimi A4'e sığdırılmıştır (kenar boşlukları ve kart genişlikleri otomatik).
- Metrikler metre ve km/h cinsindedir; simülasyonda piksel→metre ölçek dönüşümü yapılır.
- CSV modunda 1..20+ oyuncu otomatik desteklenir (renk, dot ve isim etiketleri dinamik).

Yazan: (c) 2025
"""

# 2) Standart kütüphaneler ve üçüncü parti
import io, os, math, time, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
from collections import deque, defaultdict

# 3) Matplotlib yalnızca küçük grafikleri PNG üretmek için (PDF'e gömüyoruz)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 4) ReportLab PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

# 5) Uygulama sabitleri
APP_TITLE = "Saha Koşu + Rapor (Dinamik)"
W, H = 1100, 700            # Canvas boyutu (px)
PAD = 30                    # Canvas iç kenar boşluğu (px)

# 6) Rapor eşikleri
ZONE4 = 17.0   # km/h
ZONE5 = 20.0
ZONE6 = 24.0
ACC_TH =  2.5  # m/s^2
DEC_TH = -2.5

# === Adaptif eşik konfigürasyonu (EKLEME) ===
ADAPTIVE_SPEED = True            # Hız zonları aşılmazsa oyuncu-vmax’a göre eşik kullan
HML_REL_OF_VMAX = 0.75           # HML adaptif: 0.75 * v_max
HSR_REL_OF_VMAX = 0.90           # HSR adaptif: 0.90 * v_max
ADAPTIVE_ACC_USE_PCTL = True     # İvmede sabit eşik tutmazsa yüzdelik kullan
ACC_UP_PCTL = 0.98               # > 98. yüzdelik ivmeler “acc event”
ACC_DN_PCTL = 0.02               # < 2.  yüzdelik ivmeler “dec event”
MIN_SPEED_FOR_EVENTS_MS = 3/3.6  # Acc/Dec sayarken min hız ~3 km/h (gürültü filtresi)

# 7) Animasyon / Görselleştirme
FPS = 60
DOT_R = 12
SIM_NAMES = ["A", "B", "C"]
SIM_COLORS = ["#1f77b4", "#d62728", "#2ca02c"]  # mavi/kırmızı/yeşil (simülasyon için sabit)
# CSV oyuncuları için geniş renk paleti:
CSV_COLOR_PALETTE = [
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
    "#a55194","#393b79","#637939","#8c6d31","#843c39",
    "#7b4173","#3182bd","#e6550d","#31a354","#756bb1"
]

# 8) Gerçek saha boyutları (metre)
FIELD_LEN_M = 105.0
FIELD_WID_M = 68.0

# 9) Yardımcı: Haversine (metre)
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = np.radians(lat1); phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1); dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlmb/2)**2
    return R * 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))

# 10) Yardımcı: Basit merkezi hareketli ortalama
def rolling_ma(arr, win=3):
    if win <= 1:
        return arr
    s = pd.Series(arr).rolling(win, center=True, min_periods=1).mean()
    s = s.fillna(method="bfill").fillna(method="ffill")
    return s.values

# 11) Yardımcı: Canvas→metre ölçek katsayıları (px başına metre)
def canvas_scales_m_per_px():
    mx = FIELD_LEN_M / float(W - 2*PAD)
    my = FIELD_WID_M / float(H - 2*PAD)
    return mx, my

# 12) Saha çizimi
def draw_pitch(canvas):
    canvas.delete("pitch")
    x0, y0 = PAD, PAD
    x1, y1 = W - PAD, H - PAD
    cx, cy = (x0 + x1)/2, (y0 + y1)/2

    canvas.create_rectangle(x0, y0, x1, y1, fill="#77b255", outline="#3d7a3b", tags="pitch")
    canvas.create_line(cx, y0, cx, y1, width=2, fill="#ffffff", tags="pitch")
    canvas.create_oval(cx-60, cy-60, cx+60, cy+60, outline="#ffffff", width=2, tags="pitch")
    canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#ffffff", outline="", tags="pitch")

    box_w, box_h = 160, 300
    canvas.create_rectangle(x0, cy-box_h/2, x0+box_w, cy+box_h/2, outline="#ffffff", width=2, tags="pitch")
    canvas.create_rectangle(x1-box_w, cy-box_h/2, x1, cy+box_h/2, outline="#ffffff", width=2, tags="pitch")

    g_w, g_h = 60, 180
    canvas.create_rectangle(x0, cy-g_h/2, x0+g_w, cy+g_h/2, outline="#ffffff", width=2, tags="pitch")
    canvas.create_rectangle(x1-g_w, cy-g_h/2, x1, cy+g_h/2, outline="#ffffff", width=2, tags="pitch")

    canvas.create_oval(x0+110-3, cy-3, x0+110+3, cy+3, fill="#ffffff", outline="", tags="pitch")
    canvas.create_oval(x1-110-3, cy-3, x1-110+3, cy+3, fill="#ffffff", outline="", tags="pitch")

    cr = 12
    canvas.create_arc(x0, y0, x0+2*cr, y0+2*cr, start=0, extent=90, style="arc", outline="#ffffff", width=2, tags="pitch")
    canvas.create_arc(x1-2*cr, y0, x1, y0+2*cr, start=90, extent=90, style="arc", outline="#ffffff", width=2, tags="pitch")
    canvas.create_arc(x1-2*cr, y1-2*cr, x1, y1, start=180, extent=90, style="arc", outline="#ffffff", width=2, tags="pitch")
    canvas.create_arc(x0, y1-2*cr, x0+2*cr, y1, start=270, extent=90, style="arc", outline="#ffffff", width=2, tags="pitch")

    # Sahayı en alta gönder (diğer objeler üstte kalır)
    canvas.tag_lower("pitch")

# 13) Küçük bar grafiği PNG buffer (PDF'e gömülecek)
def small_bar_png(val, title="Total Distance (m)"):
    fig = plt.figure(figsize=(3.2, 2.2), dpi=150)
    plt.bar(["Session"], [val])
    plt.ylabel("m"); plt.title(title); plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

# 14) PDF kart çizici
def draw_card_pdf(c, x, y, w, h, title, value, foot=None):
    c.setFillColor(colors.whitesmoke); c.setStrokeColor(colors.lightgrey)
    c.roundRect(x, y, w, h, 8, fill=True, stroke=True)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11); c.drawString(x+8, y+h-14, title)
    c.setFont("Helvetica-Bold", 22); c.drawCentredString(x+w/2, y+h/2+4, str(value))
    if foot:
        c.setFont("Helvetica", 9); c.setFillColor(colors.grey)
        c.drawCentredString(x+w/2, y+12, foot)
    c.setFillColor(colors.black)

# 15) PDF dışa aktarım (yerleşim düzeltilmiş)
def export_pdf(session_title, stats_by_player, path):
    c = pdfcanvas.Canvas(path, pagesize=A4); PW, PH = A4

    M = 15*mm         # kenar boşluğu
    GX = 6*mm         # yatay boşluk
    GY = 6*mm         # dikey boşluk
    CARD_H = 28*mm

    usable_w = PW - 2*M
    card_w = (usable_w - 2*GX) / 3.0

    title_y = PH - M - 5*mm
    sub_y   = title_y - 7*mm
    row1_y  = sub_y - 10*mm - CARD_H
    row2_y  = row1_y - GY - CARD_H
    wide_y  = row2_y - GY - CARD_H
    plot_h  = 50*mm
    plot_y  = wide_y - GY - plot_h

    for player, st in stats_by_player.items():
        c.setFont("Helvetica-Bold", 16); c.drawString(M, title_y, session_title)
        c.setFont("Helvetica", 12); c.drawString(M, sub_y, f"Player: {player}")

        # (GÜNCEL) dipnot destekli çağrılar
        draw_card_pdf(c, M + 0*(card_w+GX), row1_y, card_w, CARD_H, "Total Distance", f"{st['TotalDistance_m']} m")
        draw_card_pdf(c, M + 1*(card_w+GX), row1_y, card_w, CARD_H, "Max Speed", f"{st['MaxSpeed_kmh']} km/h")
        draw_card_pdf(c, M + 2*(card_w+GX), row1_y, card_w, CARD_H, "Distance/Min", f"{st['DistancePerMin_m']} m/min")

        draw_card_pdf(c, M + 0*(card_w+GX), row2_y, card_w, CARD_H, "HSR (Abs)", f"{st['HSR_m']} m", foot=st.get("HSR_foot"))
        draw_card_pdf(c, M + 1*(card_w+GX), row2_y, card_w, CARD_H, "Acc Z4–Z6", f"{st['AccZ4_6']}", foot=st.get("Acc_foot"))
        draw_card_pdf(c, M + 2*(card_w+GX), row2_y, card_w, CARD_H, "Dec Z4–Z6", f"{st['DecZ4_6']}", foot=st.get("Dec_foot"))

        draw_card_pdf(c, M, wide_y, usable_w, CARD_H, "HML Distance", f"{st['HML_m']} m", foot=st.get("HML_foot"))

        png = ImageReader(small_bar_png(st["TotalDistance_m"]))
        c.drawImage(png, M, plot_y, width=usable_w, height=plot_h,
                    preserveAspectRatio=True, anchor='sw', mask='auto')

        c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
        c.drawRightString(PW - M, 10*mm, "Generated by field_runner_report.py")
        c.setFillColor(colors.black)
        c.showPage()

    c.save()

# 16) Excel dışa aktarım
def export_excel(stats_by_player, path):
    df = pd.DataFrame(stats_by_player).T.reset_index().rename(columns={"index":"Player"})
    cols = ["Player","TotalDistance_m","Duration_s","DistancePerMin_m",
            "MaxSpeed_kmh","HSR_m","AccZ4_6","DecZ4_6","HML_m"]
    # Kolonları güvenle sırala
    for col in cols:
        if col not in df.columns:
            df[col] = np.nan
    df = df[cols]
    df.to_excel(path, index=False)

# 17) Ölçüm metrikleri: piksel→metre, metre→metre, GPS→metre desteği
def compute_metrics_from_timeseries(ts_df, *,
                                   data_is_meters=False,
                                   use_gps=False,
                                   smooth_win=3):
    """
    ts_df kolonları:
      - data_is_meters=True  -> timestamp, x, y  (metre)
      - use_gps=True         -> timestamp, lat, lon (derece)
      - aksi halde           -> timestamp, x, y  (piksel; canvas)
    Dönen metrikler:
      TotalDistance_m, Duration_s, DistancePerMin_m, MaxSpeed_kmh, HSR_m, AccZ4_6, DecZ4_6, HML_m
    """
    if ts_df is None or len(ts_df) < 2:
        return {"TotalDistance_m":0.0,"Duration_s":0.0,"DistancePerMin_m":0.0,
                "MaxSpeed_kmh":0.0,"HSR_m":0.0,"AccZ4_6":0,"DecZ4_6":0,"HML_m":0.0}

    d = ts_df.sort_values("timestamp").reset_index(drop=True)
    dt = d["timestamp"].diff().dt.total_seconds().fillna(0).values

    if use_gps:
        # Bu yol normalde 'meters' serisi üretmek için pick_csv'te kullanılacak
        dist = np.zeros(len(d))
        dist[1:] = haversine_m(d["lat"][:-1].values, d["lon"][:-1].values,
                               d["lat"][1:].values,  d["lon"][1:].values)
    else:
        if data_is_meters:
            dx = d["x"].diff().fillna(0).values
            dy = d["y"].diff().fillna(0).values
            dist = np.sqrt(dx*dx + dy*dy)
        else:
            # piksel → metre
            mx, my = canvas_scales_m_per_px()
            dx_px = d["x"].diff().fillna(0).values
            dy_px = d["y"].diff().fillna(0).values
            dist = np.sqrt((dx_px*mx)**2 + (dy_px*my)**2)

    # hız/ivme
    v_ms = np.divide(dist, np.maximum(dt, 1e-6))
    v_ms = rolling_ma(v_ms, win=smooth_win)
    v_kmh = v_ms * 3.6
    dv = np.diff(v_ms, prepend=v_ms[0])
    acc = np.divide(dv, np.maximum(dt, 1e-6))

    total_m = float(np.sum(dist))
    duration_s = float((d["timestamp"].iloc[-1] - d["timestamp"].iloc[0]).total_seconds())
    dpm = total_m / (duration_s/60.0) if duration_s > 0 else 0.0
    vmax = float(np.max(v_kmh)) if len(v_kmh) else 0.0
    hsr = float(np.sum(dist[v_kmh > ZONE5]))
    hml = float(np.sum(dist[v_kmh > ZONE4]))
    acc_ct = int(np.sum(acc > ACC_TH)); dec_ct = int(np.sum(acc < DEC_TH))

    return {
        "TotalDistance_m": round(total_m, 1),
        "Duration_s": round(duration_s, 1),
        "DistancePerMin_m": round(dpm, 1),
        "MaxSpeed_kmh": round(vmax, 2),
        "HSR_m": round(hsr, 1),
        "AccZ4_6": acc_ct,
        "DecZ4_6": dec_ct,
        "HML_m": round(hml, 1),
    }

# === EKLEME: Adaptif sarmalayıcı ===
def compute_metrics_from_timeseries_adaptive(ts_df, *,
                                            data_is_meters=False,
                                            use_gps=False,
                                            smooth_win=3):
    # 1) Orijinal hesap
    st = compute_metrics_from_timeseries(ts_df,
                                         data_is_meters=data_is_meters,
                                         use_gps=use_gps,
                                         smooth_win=smooth_win)
    # Dipnot alanları
    st["HSR_foot"] = ""
    st["HML_foot"] = ""
    st["Acc_foot"] = ""
    st["Dec_foot"] = ""

    # 2) Adaptif kapalıysa çık
    if not ADAPTIVE_SPEED or ts_df is None or len(ts_df) < 2:
        return st

    # 3) Hız/ivme serilerini yeniden çıkar
    d = ts_df.sort_values("timestamp").reset_index(drop=True)
    dt = d["timestamp"].diff().dt.total_seconds().fillna(0).values

    if use_gps:
        dist = np.zeros(len(d))
        dist[1:] = haversine_m(d["lat"][:-1].values, d["lon"][:-1].values,
                               d["lat"][1:].values,  d["lon"][1:].values)
        v_ms = np.divide(dist, np.maximum(dt, 1e-6))
    else:
        if data_is_meters:
            dx = d["x"].diff().fillna(0).values
            dy = d["y"].diff().fillna(0).values
            dist = np.sqrt(dx*dx + dy*dy)
            v_ms = np.divide(dist, np.maximum(dt, 1e-6))
        else:
            mx, my = canvas_scales_m_per_px()
            dx_px = d["x"].diff().fillna(0).values
            dy_px = d["y"].diff().fillna(0).values
            dist = np.sqrt((dx_px*mx)**2 + (dy_px*my)**2)
            v_ms = np.divide(dist, np.maximum(dt, 1e-6))

    v_ms = rolling_ma(v_ms, win=smooth_win)
    v_kmh = v_ms * 3.6
    dv = np.diff(v_ms, prepend=v_ms[0])
    acc = np.divide(dv, np.maximum(dt, 1e-6))
    vmax = float(np.max(v_kmh)) if len(v_kmh) else 0.0

    # 4) HML adaptif (ZONE4 aşılmadıysa)
    if st["HML_m"] == 0.0 and vmax > 0:
        thr_hml = HML_REL_OF_VMAX * vmax
        if thr_hml < ZONE4:
            hml_adapt = float(np.sum(dist[v_kmh > thr_hml]))
            if hml_adapt > 0:
                st["HML_m"] = round(hml_adapt, 1)
                st["HML_foot"] = f"adaptif ≥{thr_hml:.1f} km/h ({HML_REL_OF_VMAX*100:.0f}% vₘₐₓ)"

    # 5) HSR adaptif (ZONE5 aşılmadıysa)
    if st["HSR_m"] == 0.0 and vmax > 0:
        thr_hsr = HSR_REL_OF_VMAX * vmax
        if thr_hsr < ZONE5:
            hsr_adapt = float(np.sum(dist[v_kmh > thr_hsr]))
            if hsr_adapt > 0:
                st["HSR_m"] = round(hsr_adapt, 1)
                st["HSR_foot"] = f"adaptif ≥{thr_hsr:.1f} km/h ({HSR_REL_OF_VMAX*100:.0f}% vₘₐₓ)"

    # 6) Acc/Dec adaptif (sabit eşikler tetiklenmiyorsa)
    if ADAPTIVE_ACC_USE_PCTL and len(acc) > 5:
        if st["AccZ4_6"] == 0:
            acc_thr = np.quantile(acc, ACC_UP_PCTL)
            mask = (acc > acc_thr) & (v_ms > MIN_SPEED_FOR_EVENTS_MS)
            acc_ct = int(np.sum(mask))
            if acc_ct > 0:
                st["AccZ4_6"] = acc_ct
                st["Acc_foot"] = f"adaptif >{acc_thr:.2f} m/s² (>{int(ACC_UP_PCTL*100)}p)"
        if st["DecZ4_6"] == 0:
            dec_thr = np.quantile(acc, ACC_DN_PCTL)
            mask = (acc < dec_thr) & (v_ms > MIN_SPEED_FOR_EVENTS_MS)
            dec_ct = int(np.sum(mask))
            if dec_ct > 0:
                st["DecZ4_6"] = dec_ct
                st["Dec_foot"] = f"adaptif <{dec_thr:.2f} m/s² (<{int(ACC_DN_PCTL*100)}p)"

    return st

# 18) Yardımcı: güvenli float okuma
def _safe_float_series(s):
    try:
        return pd.to_numeric(s, errors="coerce")
    except Exception:
        return pd.Series([np.nan]*len(s))

# 19) Ana uygulama
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry(f"{W}x{H+160}")

        # 19.1) Canvas ve saha
        self.canvas = tk.Canvas(self, bg="#e9ecef", width=W, height=H, highlightthickness=0)
        self.canvas.pack(side="top", fill="both")
        draw_pitch(self.canvas)

        # 19.2) Kontrol paneli (üst)
        ctrl = ttk.Frame(self, padding=8); ctrl.pack(fill="x")
        self.mode = tk.StringVar(value="sim")  # "sim" | "csv"
        ttk.Radiobutton(ctrl, text="Simülasyon", variable=self.mode, value="sim").grid(row=0, column=0, padx=4)
        ttk.Radiobutton(ctrl, text="CSV'den Oynat", variable=self.mode, value="csv").grid(row=0, column=1, padx=4)
        ttk.Button(ctrl, text="CSV Seç", command=self.pick_csv).grid(row=0, column=2, padx=6)
        self.csv_path = tk.StringVar(value="")
        ttk.Label(ctrl, textvariable=self.csv_path, width=60).grid(row=0, column=3, sticky="w")

        ttk.Button(ctrl, text="▶ Başlat / ⏸", command=self.toggle).grid(row=0, column=4, padx=6)
        ttk.Button(ctrl, text="↺ Yeniden", command=self.reset_all).grid(row=0, column=5, padx=6)

        ttk.Label(ctrl, text="Hız x").grid(row=0, column=6, padx=(10,2))
        self.speed = tk.DoubleVar(value=1.0)
        ttk.Spinbox(ctrl, from_=0.2, to=3.0, increment=0.1, width=6, textvariable=self.speed).grid(row=0, column=7)

        ttk.Button(ctrl, text="Hesapla", command=self.compute_report).grid(row=0, column=8, padx=(14,6))
        ttk.Button(ctrl, text="PDF İndir", command=self.save_pdf).grid(row=0, column=9, padx=4)
        ttk.Button(ctrl, text="Excel İndir", command=self.save_excel).grid(row=0, column=10, padx=4)

        # 19.3) Görsel seçenekler (alt kontrol)
        vis = ttk.Frame(self, padding=(8,0,8,6)); vis.pack(fill="x")
        self.show_trails = tk.BooleanVar(value=True)
        self.trail_len = tk.IntVar(value=25)
        self.show_legend = tk.BooleanVar(value=True)
        ttk.Checkbutton(vis, text="İzleri Göster", variable=self.show_trails, command=self._refresh_trails_visibility).grid(row=0, column=0, padx=4)
        ttk.Label(vis, text="İz Uzunluğu").grid(row=0, column=1, padx=(10,2))
        ttk.Spinbox(vis, from_=5, to=200, increment=5, width=6, textvariable=self.trail_len, command=self._apply_trail_len).grid(row=0, column=2, padx=(0,10))
        ttk.Checkbutton(vis, text="Lejandı Göster", variable=self.show_legend, command=self._redraw_legend).grid(row=0, column=3, padx=4)

        # 19.4) Sonuç tablosu
        cols = ["Player","TotalDistance_m","Duration_s","DistancePerMin_m",
                "MaxSpeed_kmh","HSR_m","AccZ4_6","DecZ4_6","HML_m"]
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=7)
        for c in cols:
            self.tree.heading(c, text=c); self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="x", padx=8, pady=6)

        # 19.5) Animasyon & veri durumları
        self.running = False; self.last_t = None
        self.start_time = None
        self.after_id = None

        # 19.6) Simülasyon parametreleri (sol yarı saha merkezli)
        x0, y0 = PAD, PAD
        x1, y1 = W - PAD, H - PAD
        cx, cy = (x0 + x1)/2, (y0 + y1)/2
        self.left_cx = (x0 + cx)/2; self.left_cy = cy

        # Sim hızları (~px/s) → px→m dönüşüm raporda yapılır
        self.sim_specs = [
            {"orbit_r": 120, "omega":  0.70, "theta": 0.0},            # orta hız
            {"orbit_r": 160, "omega": -0.55, "theta": 2*math.pi/3},   # ters yön
            {"orbit_r":  90, "omega":  0.95, "theta": 4*math.pi/3},   # hızlı küçük çember
        ]

        # 19.7) Canvas üzerindeki oyuncu noktaları ve etiketleri
        self.dots = []  # list of dict(id, text_id, name, color)
        self.player_order = SIM_NAMES[:]  # çizim sırası
        self.player_color = {}            # name -> color
        for i, name in enumerate(SIM_NAMES):
            color = SIM_COLORS[i % len(SIM_COLORS)]
            self.player_color[name] = color
            x, y = self._sim_pos(self.sim_specs[i]["theta"], self.sim_specs[i]["orbit_r"])
            did = self.canvas.create_oval(x-DOT_R, y-DOT_R, x+DOT_R, y+DOT_R, fill=color, outline="#111", width=2)
            tid = self.canvas.create_text(x, y, text=name, fill="#fff",
                                          font=("Segoe UI", max(9,int(DOT_R*0.95)), "bold"))
            self.dots.append({"id": did, "text_id": tid, "name": name, "color": color})

        # 19.8) İz (trail) çizimi için yapı
        self.trails = defaultdict(lambda: deque(maxlen=self.trail_len.get()))  # name -> deque[(x,y)]
        self.trail_items = defaultdict(list)  # name -> [line_ids]
        self.trails_visible = True

        # 19.9) CSV veri depoları
        self.df = None
        # Görselleştirme için (pixel):
        self.per_player_canvas = {}   # player -> DataFrame(timestamp,x,y) px
        # Metrik için (metre):
        self.per_player_meters = {}   # player -> DataFrame(timestamp,x,y) m
        self.play_index = 0

        # 19.10) Kısayollar
        self.bind("<space>", lambda e: self.toggle())
        self.bind("r", lambda e: self.reset_all())

        # 19.11) Rapor cache
        self.stats = {}  # dict[player] -> metrics

        # 19.12) Lejand
        self.legend_box = None
        self._redraw_legend()

    # 20) Lejand kontrolleri
    def _redraw_legend(self):
        # Öncekini sil
        if self.legend_box:
            self.canvas.delete(self.legend_box)
            self.legend_box = None
        self.canvas.delete("legend_item")

        if not self.show_legend.get():
            return

        # Lejand kutusu ve maddeleri
        x, y = W - PAD - 220, PAD + 10
        box_w, line_h = 210, 18
        players = self.player_order
        box_h = 10 + len(players)*line_h + 10

        # arka kutu
        self.legend_box = self.canvas.create_rectangle(x, y, x+box_w, y+box_h,
                                                       fill="#f8f9fa", outline="#ced4da")
        # başlık
        self.canvas.create_text(x+10, y+10, text="Oyuncu Lejandı", anchor="nw",
                                font=("Segoe UI", 10, "bold"), tags="legend_item", fill="#333")

        # satırlar
        for i, name in enumerate(players):
            cy = y + 30 + i*line_h
            col = self.player_color.get(name, "#000000")
            # renk kutusu
            self.canvas.create_rectangle(x+10, cy-7, x+30, cy+7, fill=col, outline="#666", tags="legend_item")
            # isim
            self.canvas.create_text(x+40, cy, text=name, anchor="w",
                                    font=("Segoe UI", 10), tags="legend_item", fill="#222")

    # 21) Trail kontrol yardımcıları
    def _refresh_trails_visibility(self):
        self.trails_visible = bool(self.show_trails.get())
        # çizilmiş çizgileri gizle/göster
        state = "normal" if self.trails_visible else "hidden"
        for name, items in self.trail_items.items():
            for lid in items:
                self.canvas.itemconfigure(lid, state=state)

    def _apply_trail_len(self):
        L = int(self.trail_len.get())
        for name in list(self.trails.keys()):
            old = self.trails[name]
            self.trails[name] = deque(old, maxlen=L)

    def _add_to_trail(self, name, x, y):
        self.trails[name].append((x, y))
        # eski çizgileri sil
        for lid in self.trail_items[name]:
            self.canvas.delete(lid)
        self.trail_items[name].clear()

        if not self.trails_visible or len(self.trails[name]) < 2:
            return

        # çizgi çiz
        pts = list(self.trails[name])
        for i in range(1, len(pts)):
            x0, y0 = pts[i-1]; x1, y1 = pts[i]
            lid = self.canvas.create_line(x0, y0, x1, y1, fill=self.player_color.get(name, "#000"),
                                          width=2, stipple="", tags="trail_line")
            self.trail_items[name].append(lid)

    # 22) CSV seçimi ve ayrıştırma
    def pick_csv(self):
        p = filedialog.askopenfilename(title="CSV Seç", filetypes=[("CSV","*.csv")])
        if not p:
            return
        try:
            df = pd.read_csv(p)
        except Exception as e:
            messagebox.showerror("Hata", f"CSV okunamadı:\n{e}"); return

        # Zorunlu alanlar
        if "timestamp" not in df.columns or "player" not in df.columns:
            messagebox.showerror("Hata", "CSV 'timestamp' ve 'player' kolonlarını içermeli."); return

        # timestamp parse
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        except Exception:
            messagebox.showerror("Hata", "timestamp parse edilemedi (ISO kullanın)."); return

        # veri tiplerini güvenle sayıya çevir (varsa)
        has_xy = {"x","y"}.issubset(df.columns)
        has_gps = {"lat","lon"}.issubset(df.columns)

        if not (has_xy or has_gps):
            messagebox.showerror("Hata", "CSV x,y (metre) veya lat,lon (derece) içermeli."); return

        # xy/gps sütunlarını temizle
        if has_xy:
            df["x"] = _safe_float_series(df["x"])
            df["y"] = _safe_float_series(df["y"])
        if has_gps:
            df["lat"] = _safe_float_series(df["lat"])
            df["lon"] = _safe_float_series(df["lon"])

        # boş / NaN satırları at
        if has_xy:
            df = df.dropna(subset=["timestamp","player","x","y"])
        else:
            df = df.dropna(subset=["timestamp","player","lat","lon"])

        if df.empty:
            messagebox.showerror("Hata", "Geçerli satır bulunamadı."); return

        # oyuncu listesi
        players = [str(p) for p in df["player"].unique()]
        players.sort()

        # renk atama (stabil): varsa eski renk, yoksa palette
        new_color_map = {}
        palette_idx = 0
        for p_name in players:
            if p_name in self.player_color:
                new_color_map[p_name] = self.player_color[p_name]
            else:
                new_color_map[p_name] = CSV_COLOR_PALETTE[palette_idx % len(CSV_COLOR_PALETTE)]
                palette_idx += 1
        self.player_color = new_color_map
        self.player_order = players[:]

        # Dotları oyunculara göre baştan kur
        self._rebuild_dots(players)

        # Ekran (px) ve metrik (m) serileri
        self.per_player_canvas.clear()
        self.per_player_meters.clear()

        for p_name, sub in df.groupby("player"):
            sub = sub.sort_values("timestamp").reset_index(drop=True)

            if has_gps:
                # Metrik: lat/lon → metre (küçük alan için equirectangular approx)
                lat0, lon0 = float(sub["lat"].iloc[0]), float(sub["lon"].iloc[0])
                kx = 111320.0 * math.cos(math.radians(lat0))  # lon m/deg
                ky = 111320.0                                  # lat m/deg
                xm = (sub["lon"] - lon0) * kx
                ym = (sub["lat"] - lat0) * ky
                self.per_player_meters[p_name] = pd.DataFrame({
                    "timestamp": sub["timestamp"], "x": xm.values, "y": ym.values
                })

                # Ekran: min-max normalizasyon ile sahaya yerleşim
                latn = (sub["lat"] - sub["lat"].min())/(max(1e-9, sub["lat"].max() - sub["lat"].min()))
                lonn = (sub["lon"] - sub["lon"].min())/(max(1e-9, sub["lon"].max() - sub["lon"].min()))
                xpx = PAD + (W - 2*PAD) * lonn
                ypx = PAD + (H - 2*PAD) * (1 - latn)
                self.per_player_canvas[p_name] = pd.DataFrame({
                    "timestamp": sub["timestamp"], "x": xpx, "y": ypx
                })

            elif has_xy:
                # Metrik: doğrudan metre
                self.per_player_meters[p_name] = pd.DataFrame({
                    "timestamp": sub["timestamp"], "x": sub["x"].values, "y": sub["y"].values
                })

                # Ekran: metre verisini sahaya ölçekle (min-max)
                xn = (sub["x"] - sub["x"].min())/(max(1e-9, sub["x"].max() - sub["x"].min()))
                yn = (sub["y"] - sub["y"].min())/(max(1e-9, sub["y"].max() - sub["y"].min()))
                xpx = PAD + (W - 2*PAD) * xn
                ypx = PAD + (H - 2*PAD) * (1 - yn)
                self.per_player_canvas[p_name] = pd.DataFrame({
                    "timestamp": sub["timestamp"], "x": xpx, "y": ypx
                })

        self.df = df
        self.csv_path.set(os.path.basename(p))
        self.play_index = 0
        self.reset_all()
        messagebox.showinfo("CSV", f"CSV yüklendi. Oyuncu sayısı: {len(players)}")

    # 23) Dotları yeniden kur (CSV oyuncularına göre)
    def _rebuild_dots(self, players):
        # Önce eskileri sil
        for d in self.dots:
            self.canvas.delete(d["id"])
            self.canvas.delete(d["text_id"])
        self.dots.clear()

        # İzleri temizle
        for name, items in self.trail_items.items():
            for lid in items:
                self.canvas.delete(lid)
        self.trails.clear()
        self.trail_items.clear()

        # Yeni dotlar
        for idx, name in enumerate(players):
            color = self.player_color.get(name, CSV_COLOR_PALETTE[idx % len(CSV_COLOR_PALETTE)])
            # başlangıçta orta çizgi üzerinde dağıt
            x = PAD + (W - 2*PAD) * ((idx + 1)/(len(players) + 1))
            y = H/2
            did = self.canvas.create_oval(x-DOT_R, y-DOT_R, x+DOT_R, y+DOT_R, fill=color, outline="#111", width=2)
            tid = self.canvas.create_text(x, y, text=name, fill="#fff",
                                          font=("Segoe UI", max(9,int(DOT_R*0.95)), "bold"))
            self.dots.append({"id": did, "text_id": tid, "name": name, "color": color})

        # Lejandı yenile
        self._redraw_legend()

    # 24) Başlat/Durdur
    def toggle(self):
        if self.running:
            self.running = False
            if self.after_id:
                self.after_cancel(self.after_id); self.after_id = None
        else:
            self.running = True
            now = time.perf_counter()
            if self.start_time is None:
                self.start_time = now
            self.last_t = now
            self._tick()

    # 25) Sıfırla
    def reset_all(self):
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id); self.after_id = None
        self.last_t = None; self.start_time = None
        draw_pitch(self.canvas)

        # İzleri temizle görünüm
        for name, items in self.trail_items.items():
            for lid in items:
                self.canvas.delete(lid)
        self.trails.clear()
        self.trail_items.clear()

        if self.mode.get() == "sim" or not self.per_player_canvas:
            # Sim başlangıç pozisyonları
            # Eğer CSV'den döndüysek ve self.dots CSV’ye göre ise,
            # sim modunda tekrar 3 kişiye dönelim:
            if self.player_order != SIM_NAMES:
                self.player_order = SIM_NAMES[:]
                self.player_color = {n: SIM_COLORS[i] for i, n in enumerate(SIM_NAMES)}
                self._rebuild_dots(self.player_order)

            for i, d in enumerate(self.dots):
                self.sim_specs[i]["theta"] = [0.0, 2*math.pi/3, 4*math.pi/3][i % 3]
                x, y = self._sim_pos(self.sim_specs[i % 3]["theta"], self.sim_specs[i % 3]["orbit_r"])
                self._move_dot(d["id"], d["text_id"], x, y)
        else:
            # CSV: ilk frame
            self.play_index = 0
            self._draw_csv_frame(0)

        self._redraw_legend()
        self._refresh_trails_visibility()

    # 26) Animasyon tick
    def _tick(self):
        if not self.running:
            return
        now = time.perf_counter()
        dt = max(0.0, now - (self.last_t or now))
        self.last_t = now
        sp = float(self.speed.get())

        if self.mode.get() == "sim" or not self.per_player_canvas:
            # Simülasyon
            for i, d in enumerate(self.dots):
                # Simülasyonda da 3 oyuncu sabit (A,B,C)
                spec = self.sim_specs[i % 3]
                spec["theta"] += spec["omega"] * sp * dt
                x, y = self._sim_pos(spec["theta"], spec["orbit_r"])
                self._move_dot(d["id"], d["text_id"], x, y)
                self._add_to_trail(d["name"], x, y)
        else:
            # CSV oynatımı
            self.play_index += max(1, int(sp))  # basit adım
            self._draw_csv_frame(self.play_index)

        self.after_id = self.after(int(1000/FPS), self._tick)

    # 27) Simülasyon konum fonksiyonu (px)
    def _sim_pos(self, theta, r):
        return (self.left_cx + r*math.cos(theta),
                self.left_cy + r*math.sin(theta))

    # 28) Canvas objesini hareket ettir
    def _move_dot(self, dot_id, text_id, x, y):
        self.canvas.coords(dot_id, x-DOT_R, y-DOT_R, x+DOT_R, y+DOT_R)
        self.canvas.coords(text_id, x, y)

    # 29) CSV bir kare çiz
    def _draw_csv_frame(self, idx):
        any_len = 0
        for d in self.dots:
            name = d["name"]
            if name not in self.per_player_canvas:
                continue
            series = self.per_player_canvas[name]
            any_len = max(any_len, len(series))
            if len(series) == 0:
                continue
            j = min(idx, len(series)-1)
            x, y = float(series.iloc[j]["x"]), float(series.iloc[j]["y"])
            self._move_dot(d["id"], d["text_id"], x, y)
            self._add_to_trail(name, x, y)

        if any_len and self.play_index >= any_len-1:
            self.play_index = 0

    # 30) Rapor hesapla
    def compute_report(self):
        self.tree.delete(*self.tree.get_children())
        self.stats = {}

        if self.mode.get() == "sim" or not self.per_player_meters:
            # Simülasyon zaman serisi (10 dk, 10 Hz)
            t = pd.date_range("2025-01-01 10:00:00", periods=6000, freq="100L")
            out = {}
            for i, name in enumerate(SIM_NAMES):
                spec = self.sim_specs[i].copy()
                xs, ys = [], []
                for k in range(len(t)):
                    theta = spec["theta"] + self.sim_specs[i]["omega"]*(k/10.0)
                    x_px, y_px = self._sim_pos(theta, self.sim_specs[i]["orbit_r"])  # px
                    xs.append(x_px); ys.append(y_px)
                dfp = pd.DataFrame({"timestamp": t, "x": xs, "y": ys})

                # ÖNCE orijinal hesap (satırı koruyoruz), sonra adaptif ile güncelle
                base = compute_metrics_from_timeseries(dfp, data_is_meters=False, use_gps=False)
                st   = compute_metrics_from_timeseries_adaptive(dfp, data_is_meters=False, use_gps=False)
                # adaptif çıktı ana çıktı olsun
                out[name] = st
                # (base değişkeni tutuluyor; kod satırı eksilmedi.)

        else:
            # CSV: doğrudan metre serisi ile
            out = {}
            for name, sub in self.per_player_meters.items():
                base = compute_metrics_from_timeseries(sub, data_is_meters=True, use_gps=False)
                st   = compute_metrics_from_timeseries_adaptive(sub, data_is_meters=True, use_gps=False)
                out[name] = st

        for p, st in out.items():
            self.stats[p] = st
            row = [p, st["TotalDistance_m"], st["Duration_s"], st["DistancePerMin_m"],
                   st["MaxSpeed_kmh"], st["HSR_m"], st["AccZ4_6"], st["DecZ4_6"], st["HML_m"]]
            self.tree.insert("", "end", values=row)

        messagebox.showinfo("Rapor", "Hesaplama tamam. PDF/Excel indirebilirsiniz.")

    # 31) PDF kaydet
    def save_pdf(self):
        if not self.stats:
            messagebox.showwarning("Uyarı", "Önce 'Hesapla' yapın."); return
        p = filedialog.asksaveasfilename(title="PDF Kaydet", defaultextension=".pdf",
                                         filetypes=[("PDF","*.pdf")], initialfile="session_report.pdf")
        if not p:
            return
        try:
            export_pdf("Individual Session", self.stats, p)
            messagebox.showinfo("PDF", f"Kaydedildi:\n{p}")
        except Exception as e:
            messagebox.showerror("Hata", f"PDF oluşturulamadı:\n{e}")

    # 32) Excel kaydet
    def save_excel(self):
        if not self.stats:
            messagebox.showwarning("Uyarı", "Önce 'Hesapla' yapın."); return
        p = filedialog.asksaveasfilename(title="Excel Kaydet", defaultextension=".xlsx",
                                         filetypes=[("Excel","*.xlsx")], initialfile="session_report.xlsx")
        if not p:
            return
        try:
            export_excel(self.stats, p)
            messagebox.showinfo("Excel", f"Kaydedildi:\n{p}")
        except Exception as e:
            messagebox.showerror("Hata", f"Excel oluşturulamadı:\n{e}")

# 33) Main
if __name__ == "__main__":
    App().mainloop()
