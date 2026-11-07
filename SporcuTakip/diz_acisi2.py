# # -*- coding: utf-8 -*-
# """
# diz_acisi2.py
# Kinematik açı ölçümü (MediaPipe Pose) + SQLite kayıt + canlı overlay.
# 
# Bölümler:
#   1) İçe Aktarımlar & Sabitler
#   2) Yardımcı Fonksiyonlar (açı, çizim, önizleme, nazik durdurma)
#   3) Argümanlar (CLI) ve Kaynak Tipi Çözümleme
#   4) Açı Şemaları ve MediaPipe Landmark İndeksleri
#   5) SQLite Başlatma (Tablo oluşturma + otomatik migrate)
#   6) Çerçeve İşleme (tek kare -> overlay + açı satırı)
#   7) FOTOĞRAF Modu
#   8) VİDEO/KAMERA Modu (FPS, klavye kontrolü, preview, stopfile)
#   9) Kapanış (kalan buffer yazımı, release/close)
# 
# Notlar:
# 1)video yüksek fps li olsa bile 20 fps video gösterimi yapıldı.  yorum olarak kapalı kısım tam fps çalışan 20 fps
# """
# 
# # ===================== 1) İÇE AKTARIMLAR & SABİTLER ==========================
# import os
# import time
# import argparse
# import sqlite3
# from collections import OrderedDict
# 
# import cv2
# import numpy as np
# import mediapipe as mp
# 
# MODEL_COMPLEXITY = 1
# MIN_DET, MIN_TRACK = 0.5, 0.5
# CACHE_SIZE = 50          # DB'ye batch yazma boyutu
# STEP_SEC = 1             # ←/→ ile sarma süresi (saniye)
# DRAW_KNEE_ARC = True     # Diz arkasına (dış açı) kırmızı yay çiz
# 
# 
# # ===================== 2) YARDIMCI FONKSİYONLAR ==============================
# def angle_3pt(a, b, c):
#     """(2.1) 3 noktadan B tepe noktasındaki İÇ açıyı (0..180) derece cinsinden döndür."""
#     a, b, c = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
#     ang = np.degrees(np.arctan2(c[1]-b[1], c[0]-b[0]) -
#                      np.arctan2(a[1]-b[1], a[0]-b[0]))
#     ang = abs(ang)
#     if ang > 180:
#         ang = 360 - ang
#     return float(ang)
# 
# 
# def lm_xy(landmarks, idx, w, h):
#     """(2.2) MediaPipe landmark -> (piksel koordinatı, visibility)"""
#     lm = landmarks[idx]
#     return (lm.x * w, lm.y * h), lm.visibility
# 
# 
# def draw_angle_circle(img, center, value, color=(0, 255, 255)):
#     """(2.3) Eklem noktasına küçük daire ve SADECE SAYI (°/?) yaz."""
#     cx, cy = map(int, center)
#     cv2.circle(img, (cx, cy), 22, color, 2)
#     cv2.putText(img, f"{int(round(value))}", (cx - 16, cy - 24),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)
# 
# 
# def big_arc_angles(a_pt, pivot, c_pt):
#     """
#     (2.4) Pivot (diz) merkezli BÜYÜK (dış) yay için start/end açıları (OpenCV ellipse formatı).
#     A=hip, C=ankle ışınları; büyük yay = bacağın arkası.
#     """
#     v1 = np.array(a_pt) - np.array(pivot)
#     v2 = np.array(c_pt) - np.array(pivot)
#     a1 = np.degrees(np.arctan2(v1[1], v1[0])) % 360
#     a2 = np.degrees(np.arctan2(v2[1], v2[0])) % 360
#     diff_small = (a2 - a1 + 360) % 360
#     if diff_small > 180:
#         diff_small = 360 - diff_small
#     sweep_big = 360 - diff_small  # > 180
#     start = a2
#     end = (a2 + sweep_big) % 360
#     return start, end
# 
# 
# def draw_knee_outer_arc(img, knee, hip, ankle, color=(0, 0, 255)):
#     """(2.5) Diz ARKASINA (dış açı) kırmızı yay."""
#     start, end = big_arc_angles(hip, knee, ankle)
#     center = (int(knee[0]), int(knee[1]))
#     axes = (28, 28)
#     cv2.ellipse(img, center, axes, 0, start, end, color, 2)
# 
# 
# def write_preview_atomic(frame, preview_path):
#     """
#     (2.6) Önizlemeyi JPEG olarak atomik şekilde yaz.
#          (temp -> replace) C# tarafı aynı anda okuyabilir.
#     """
#     if not preview_path:
#         return
#     ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
#     if not ok:
#         return
#     tmp = preview_path + ".tmp"
#     try:
#         with open(tmp, "wb") as f:
#             f.write(buf.tobytes())
#         os.replace(tmp, preview_path)
#     except OSError:
#         pass
# 
# 
# def stop_requested(stop_file):
#     """(2.7) Nazik durdurma için stop file kontrolü."""
#     return bool(stop_file) and os.path.exists(stop_file)
# 
# 
# # ===================== 3) ARGS & KAYNAK ÇÖZÜMLEME ============================
# ap = argparse.ArgumentParser()
# ap.add_argument("--source", default="C0007.mp4",
#                 help="Kamera index (0..), video yolu veya fotoğraf yolu")
# ap.add_argument("--db", default="angles.db", help="SQLite veritabanı yolu")
# ap.add_argument("--fps", type=int, default=20, help="Hedef FPS")
# ap.add_argument("--show", action="store_true", help="İşleneni ekranda göster")
# ap.add_argument("--noshow", action="store_true", help="Gösterimi kapat")
# ap.add_argument("--save", action="store_true", help="İşlenmiş çıktıyı kaydet")
# ap.add_argument("--out", default="processed.mp4", help="Çıkış dosyası (mp4/jpg)")
# # C# entegrasyonu için:
# ap.add_argument("--stopfile", default="", help="Nazik durdurma için flag dosyası")
# ap.add_argument("--preview", default="", help="Canlı önizleme JPEG yolu")
# args = ap.parse_args()
# 
# SHOW = args.show and not args.noshow
# TARGET_FPS = int(args.fps)
# DB_PATH = args.db
# STOPFILE = args.stopfile
# PREVIEW_PATH = args.preview
# SAVE = args.save
# OUT_PATH = args.out
# 
# SRC_STR = str(args.source)
# IS_DIGIT = SRC_STR.isdigit()
# VIDEO_SOURCE = int(SRC_STR) if IS_DIGIT else SRC_STR
# 
# IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
# IS_IMAGE = (not IS_DIGIT) and SRC_STR.lower().endswith(IMG_EXT)
# 
# # MediaPipe kısa adlar
# mp_drawing, mp_pose = mp.solutions.drawing_utils, mp.solutions.pose
# 
# 
# # ========== 4) AÇI ŞEMALARI ve LANDMARK İNDEKSLERİ ===========================
# L = mp_pose.PoseLandmark
# IDX = {
#     "R_SHOULDER": L.RIGHT_SHOULDER.value,  "L_SHOULDER": L.LEFT_SHOULDER.value,
#     "R_ELBOW":    L.RIGHT_ELBOW.value,     "L_ELBOW":    L.LEFT_ELBOW.value,
#     "R_WRIST":    L.RIGHT_WRIST.value,     "L_WRIST":    L.LEFT_WRIST.value,
#     "R_INDEX":    L.RIGHT_INDEX.value,     "L_INDEX":    L.LEFT_INDEX.value,
#     "R_HIP":      L.RIGHT_HIP.value,       "L_HIP":      L.LEFT_HIP.value,
#     "R_KNEE":     L.RIGHT_KNEE.value,      "L_KNEE":     L.LEFT_KNEE.value,
#     "R_ANKLE":    L.RIGHT_ANKLE.value,     "L_ANKLE":    L.LEFT_ANKLE.value,
# }
# 
# # İç açı: omuz/dirsek/bilek; Diz: DIŞ (arka) açı
# ANGLE_SCHEMAS = OrderedDict({
#     "Right Shoulder": ("R_HIP",      "R_SHOULDER", "R_ELBOW"),
#     "Right Elbow":    ("R_SHOULDER", "R_ELBOW",    "R_WRIST"),
#     "Right Wrist":    ("R_ELBOW",    "R_WRIST",    "R_INDEX"),
#     "Right Knee":     ("R_HIP",      "R_KNEE",     "R_ANKLE"),  # dış açı
#     "Left Shoulder":  ("L_HIP",      "L_SHOULDER", "L_ELBOW"),
#     "Left Elbow":     ("L_SHOULDER", "L_ELBOW",    "L_WRIST"),
#     "Left Wrist":     ("L_ELBOW",    "L_WRIST",    "L_INDEX"),
#     "Left Knee":      ("L_HIP",      "L_KNEE",     "L_ANKLE"),  # dış açı
# })
# 
# 
# # ===================== 5) SQLITE BAŞLATMA (MIGRATE) ==========================
# conn = sqlite3.connect(DB_PATH)
# cur = conn.cursor()
# TABLE = "angles"
# 
# # tablo yoksa minimal oluştur
# cur.execute(f"""
# CREATE TABLE IF NOT EXISTS {TABLE} (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     timestamp REAL
# );
# """)
# conn.commit()
# 
# # mevcut kolonları al ve eksikleri ekle
# cur.execute(f"PRAGMA table_info({TABLE});")
# existing_cols = {row[1] for row in cur.fetchall()}
# for col in ANGLE_SCHEMAS.keys():
#     if col not in existing_cols:
#         cur.execute(f'ALTER TABLE {TABLE} ADD COLUMN "{col}" REAL;')
# conn.commit()
# 
# 
# # ===================== 6) ÇERÇEVE İŞLEME FONKSİYONU ==========================
# def process_frame(frame, pose):
#     """
#     (6) Bir kareyi işler:
#         - iskelet overlay
#         - eklem açıları (diz için dış açı)
#         - daire + sayı + diz arkası kırmızı yay
#         - DB satır listesi döndürür (timestamp + açılar) veya None
#     """
#     h, w = frame.shape[:2]
#     res = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#     row = None
# 
#     if res.pose_landmarks:
#         mp_drawing.draw_landmarks(
#             frame, res.pose_landmarks, mp_pose.POSE_CONNECTIONS,
#             mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
#             mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
#         )
# 
#         lm = res.pose_landmarks.landmark
#         px = {k: lm_xy(lm, i, w, h) for k, i in IDX.items()}
# 
#         row = [time.time()]
#         for name, (A, B, C) in ANGLE_SCHEMAS.items():
#             vis_ok = px[A][1] > 0.5 and px[B][1] > 0.5 and px[C][1] > 0.5
#             if not vis_ok:
#                 row.append(None)
#                 continue
# 
#             inner = angle_3pt(px[A][0], px[B][0], px[C][0])
#             val = 360 - inner if "Knee" in name else inner
#             row.append(val)
# 
#             # görsel
#             draw_angle_circle(frame, px[B][0], val)
#             if DRAW_KNEE_ARC and "Knee" in name:
#                 draw_knee_outer_arc(frame, px[B][0], px[A][0], px[C][0])
# 
#     return frame, row
# 
# 
# # ===================== 7) FOTOĞRAF MODU ======================================
# if IS_IMAGE:
#     img = cv2.imread(SRC_STR)
#     if img is None:
#         print("[ERR] Fotoğraf açılamadı:", SRC_STR)
#     else:
#         with mp_pose.Pose(model_complexity=MODEL_COMPLEXITY,
#                           min_detection_confidence=MIN_DET,
#                           min_tracking_confidence=MIN_TRACK) as pose:
#             frame, row = process_frame(img, pose)
# 
#             # DB yaz
#             if row is not None:
#                 cols = ", ".join([f'"{k}"' for k in ANGLE_SCHEMAS.keys()])
#                 placeholders = ",".join(["?"] * (1 + len(ANGLE_SCHEMAS)))
#                 cur.execute(
#                     f"INSERT INTO {TABLE} (timestamp, {cols}) VALUES ({placeholders})",
#                     tuple(row)
#                 )
#                 conn.commit()
# 
#             # kaydet
#             if SAVE:
#                 ok = cv2.imwrite(OUT_PATH, frame)
#                 print("[i] Çıktı foto kaydedildi:", OUT_PATH if ok else "[HATA] yazılamadı")
# 
#             # preview (C# için)
#             write_preview_atomic(frame, PREVIEW_PATH)
# 
#             # göster
#             if SHOW:
#                 cv2.imshow("Pose + Diz Arka Açısı", frame)
#                 cv2.waitKey(0)
#                 cv2.destroyAllWindows()
# 
#     conn.close()
#     print(f"Kayıt tamam: {DB_PATH}")
#     raise SystemExit(0)
# 
# 
# # ===================== 8) VİDEO / KAMERA MODU ================================
# cap = cv2.VideoCapture(VIDEO_SOURCE)
# if not cap.isOpened():
#     print("[ERR] Kaynak açılamadı:", VIDEO_SOURCE)
#     conn.close()
#     raise SystemExit(1)
# 
# writer = None
# frame_interval = 1.0 / max(1, TARGET_FPS)
# rows_cache = []
# paused = False
# 
# with mp_pose.Pose(model_complexity=MODEL_COMPLEXITY,
#                   min_detection_confidence=MIN_DET,
#                   min_tracking_confidence=MIN_TRACK) as pose:
# 
#     last = 0.0
#     while True:
#         # nazik durdurma
#         if stop_requested(STOPFILE):
#             print("[i] Stop flag görüldü, nazik çıkış yapılıyor...")
#             break
# 
#         if not paused:
#             ok, frame = cap.read()
#             if not ok:
#                 break
#         else:
#             # duraklatılmışken yine stop/preview çalışsın
#             time.sleep(0.05)
#             if SHOW:
#                 key = cv2.waitKey(1) & 0xFF
#                 if key == 32:  # SPACE -> devam
#                     paused = False
#             continue
# 
#         now = time.time()
#         if now - last < frame_interval:
#             # FPS sabitleme
#             if SHOW:
#                 cv2.waitKey(1)
#             continue
#         last = now
# 
#         frame, row = process_frame(frame, pose)
# 
#         # preview (C# için)
#         write_preview_atomic(frame, PREVIEW_PATH)
# 
#         # DB batch buffer
#         if row is not None:
#             rows_cache.append(tuple(row))
#             if len(rows_cache) >= CACHE_SIZE:
#                 cols = ", ".join([f'"{k}"' for k in ANGLE_SCHEMAS.keys()])
#                 placeholders = ",".join(["?"] * (1 + len(ANGLE_SCHEMAS)))
#                 cur.executemany(
#                     f"INSERT INTO {TABLE} (timestamp, {cols}) VALUES ({placeholders})",
#                     rows_cache
#                 )
#                 conn.commit()
#                 rows_cache.clear()
# 
#         # VideoWriter
#         if SAVE:
#             if writer is None:
#                 fourcc = cv2.VideoWriter_fourcc(*"mp4v")
#                 h, w = frame.shape[:2]
#                 writer = cv2.VideoWriter(OUT_PATH, fourcc, max(1, TARGET_FPS), (w, h))
#                 if not writer.isOpened():
#                     print("[ERR] VideoWriter açılamadı:", OUT_PATH)
#                     SAVE = False
#             if SAVE:
#                 writer.write(frame)
# 
#         # açık pencere kontrolü
#         if SHOW:
#             cv2.imshow("Pose + Diz Arka Açısı", frame)
#             key = cv2.waitKey(1) & 0xFF
#             if key == ord('q'):
#                 break
#             elif key == 32:  # space -> pause
#                 paused = True
#             elif key in (81, ord('a')) and not IS_DIGIT:
#                 # ← geri
#                 pos = cap.get(cv2.CAP_PROP_POS_MSEC)
#                 cap.set(cv2.CAP_PROP_POS_MSEC, max(pos - STEP_SEC * 1000, 0))
#             elif key in (83, ord('d')) and not IS_DIGIT:
#                 # → ileri
#                 pos = cap.get(cv2.CAP_PROP_POS_MSEC)
#                 cap.set(cv2.CAP_PROP_POS_MSEC, pos + STEP_SEC * 1000)
# 
# 
# # ===================== 9) KAPANIŞ ============================================
# # kalanları yaz
# if rows_cache:
#     cols = ", ".join([f'"{k}"' for k in ANGLE_SCHEMAS.keys()])
#     placeholders = ",".join(["?"] * (1 + len(ANGLE_SCHEMAS)))
#     cur.executemany(
#         f"INSERT INTO {TABLE} (timestamp, {cols}) VALUES ({placeholders})",
#         rows_cache
#     )
#     conn.commit()
# 
# # writer kapat
# if writer is not None:
#     writer.release()
# 
# # kaynakları serbest bırak
# cap.release()
# if SHOW:
#     cv2.destroyAllWindows()
# conn.close()
# 
# print(f"Kayıt tamam: {DB_PATH}")
# -*- coding: utf-8 -*-
"""
diz_acisi2.py
Kinematik açı ölçümü (MediaPipe Pose) + SQLite kayıt + canlı overlay.

Bölümler:
  1) İçe Aktarımlar & Sabitler
  2) Yardımcı Fonksiyonlar (açı, çizim, önizleme, nazik durdurma)
  3) Argümanlar (CLI) ve Kaynak Tipi Çözümleme
  4) Açı Şemaları ve MediaPipe Landmark İndeksleri
  5) SQLite Başlatma (Tablo oluşturma + otomatik migrate)
  6) Çerçeve İşleme (tek kare -> overlay + açı satırı)
  7) FOTOĞRAF Modu
  8) VİDEO/KAMERA Modu (20 FPS gerçek-zaman gösterim, klavye, preview, stopfile)
  9) Kapanış (kalan buffer yazımı, release/close)

Notlar:
1) Kaynak yüksek FPS bile olsa **gösterim 20 FPS**'e zamanlanır (okuma zamanı gelince yapılır).
"""

# ===================== 1) İÇE AKTARIMLAR & SABİTLER ==========================
import os
import time
import argparse
import sqlite3
from collections import OrderedDict

import cv2
import numpy as np
import mediapipe as mp

MODEL_COMPLEXITY = 1
MIN_DET, MIN_TRACK = 0.5, 0.5
CACHE_SIZE = 50          # DB'ye batch yazma boyutu
STEP_SEC = 1             # ←/→ ile sarma süresi (saniye)
DRAW_KNEE_ARC = True     # Diz arkasına (dış açı) kırmızı yay çiz


# ===================== 2) YARDIMCI FONKSİYONLAR ==============================
def angle_3pt(a, b, c):
    """(2.1) 3 noktadan B tepe noktasındaki İÇ açıyı (0..180) derece cinsinden döndür."""
    a, b, c = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
    ang = np.degrees(np.arctan2(c[1]-b[1], c[0]-b[0]) -
                     np.arctan2(a[1]-b[1], a[0]-b[0]))
    ang = abs(ang)
    if ang > 180:
        ang = 360 - ang
    return float(ang)


def lm_xy(landmarks, idx, w, h):
    """(2.2) MediaPipe landmark -> (piksel koordinatı, visibility)"""
    lm = landmarks[idx]
    return (lm.x * w, lm.y * h), lm.visibility


def draw_angle_circle(img, center, value, color=(0, 255, 255)):
    """(2.3) Eklem noktasına küçük daire ve SADECE SAYI (°/?) yaz."""
    cx, cy = map(int, center)
    cv2.circle(img, (cx, cy), 22, color, 2)
    cv2.putText(img, f"{int(round(value))}", (cx - 16, cy - 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)


def big_arc_angles(a_pt, pivot, c_pt):
    """
    (2.4) Pivot (diz) merkezli BÜYÜK (dış) yay için start/end açıları (OpenCV ellipse formatı).
    A=hip, C=ankle ışınları; büyük yay = bacağın arkası.
    """
    v1 = np.array(a_pt) - np.array(pivot)
    v2 = np.array(c_pt) - np.array(pivot)
    a1 = np.degrees(np.arctan2(v1[1], v1[0])) % 360
    a2 = np.degrees(np.arctan2(v2[1], v2[0])) % 360
    diff_small = (a2 - a1 + 360) % 360
    if diff_small > 180:
        diff_small = 360 - diff_small
    sweep_big = 360 - diff_small  # > 180
    start = a2
    end = (a2 + sweep_big) % 360
    return start, end


def draw_knee_outer_arc(img, knee, hip, ankle, color=(0, 0, 255)):
    """(2.5) Diz ARKASINA (dış açı) kırmızı yay."""
    start, end = big_arc_angles(hip, knee, ankle)
    center = (int(knee[0]), int(knee[1]))
    axes = (28, 28)
    cv2.ellipse(img, center, axes, 0, start, end, color, 2)


def write_preview_atomic(frame, preview_path):
    """
    (2.6) Önizlemeyi JPEG olarak atomik şekilde yaz.
         (temp -> replace) C# tarafı aynı anda okuyabilir.
    """
    if not preview_path:
        return
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        return
    tmp = preview_path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(buf.tobytes())
        os.replace(tmp, preview_path)
    except OSError:
        pass


def stop_requested(stop_file):
    """(2.7) Nazik durdurma için stop file kontrolü."""
    return bool(stop_file) and os.path.exists(stop_file)


# ===================== 3) ARGS & KAYNAK ÇÖZÜMLEME ============================
ap = argparse.ArgumentParser()
ap.add_argument("--source", default="C0007.mp4",
                help="Kamera index (0..), video yolu veya fotoğraf yolu")
ap.add_argument("--db", default="angles.db", help="SQLite veritabanı yolu")
ap.add_argument("--fps", type=int, default=20, help="Hedef FPS")
ap.add_argument("--show", action="store_true", help="İşleneni ekranda göster")
ap.add_argument("--noshow", action="store_true", help="Gösterimi kapat")
ap.add_argument("--save", action="store_true", help="İşlenmiş çıktıyı kaydet")
ap.add_argument("--out", default="processed.mp4", help="Çıkış dosyası (mp4/jpg)")
# C# entegrasyonu için:
ap.add_argument("--stopfile", default="", help="Nazik durdurma için flag dosyası")
ap.add_argument("--preview", default="", help="Canlı önizleme JPEG yolu")
args = ap.parse_args()

SHOW = args.show and not args.noshow
TARGET_FPS = int(args.fps)
DB_PATH = args.db
STOPFILE = args.stopfile
PREVIEW_PATH = args.preview
SAVE = args.save
OUT_PATH = args.out

SRC_STR = str(args.source)
IS_DIGIT = SRC_STR.isdigit()
VIDEO_SOURCE = int(SRC_STR) if IS_DIGIT else SRC_STR

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
IS_IMAGE = (not IS_DIGIT) and SRC_STR.lower().endswith(IMG_EXT)

# MediaPipe kısa adlar
mp_drawing, mp_pose = mp.solutions.drawing_utils, mp.solutions.pose


# ========== 4) AÇI ŞEMALARI ve LANDMARK İNDEKSLERİ ===========================
L = mp_pose.PoseLandmark
IDX = {
    "R_SHOULDER": L.RIGHT_SHOULDER.value,  "L_SHOULDER": L.LEFT_SHOULDER.value,
    "R_ELBOW":    L.RIGHT_ELBOW.value,     "L_ELBOW":    L.LEFT_ELBOW.value,
    "R_WRIST":    L.RIGHT_WRIST.value,     "L_WRIST":    L.LEFT_WRIST.value,
    "R_INDEX":    L.RIGHT_INDEX.value,     "L_INDEX":    L.LEFT_INDEX.value,
    "R_HIP":      L.RIGHT_HIP.value,       "L_HIP":      L.LEFT_HIP.value,
    "R_KNEE":     L.RIGHT_KNEE.value,      "L_KNEE":     L.LEFT_KNEE.value,
    "R_ANKLE":    L.RIGHT_ANKLE.value,     "L_ANKLE":    L.LEFT_ANKLE.value,
}

# İç açı: omuz/dirsek/bilek; Diz: DIŞ (arka) açı
ANGLE_SCHEMAS = OrderedDict({
    "Right Shoulder": ("R_HIP",      "R_SHOULDER", "R_ELBOW"),
    "Right Elbow":    ("R_SHOULDER", "R_ELBOW",    "R_WRIST"),
    "Right Wrist":    ("R_ELBOW",    "R_WRIST",    "R_INDEX"),
    "Right Knee":     ("R_HIP",      "R_KNEE",     "R_ANKLE"),  # dış açı
    "Left Shoulder":  ("L_HIP",      "L_SHOULDER", "L_ELBOW"),
    "Left Elbow":     ("L_SHOULDER", "L_ELBOW",    "L_WRIST"),
    "Left Wrist":     ("L_ELBOW",    "L_WRIST",    "L_INDEX"),
    "Left Knee":      ("L_HIP",      "L_KNEE",     "L_ANKLE"),  # dış açı
})


# ===================== 5) SQLITE BAŞLATMA (MIGRATE) ==========================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
TABLE = "angles"

# tablo yoksa minimal oluştur
cur.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL
);
""")
conn.commit()

# mevcut kolonları al ve eksikleri ekle
cur.execute(f"PRAGMA table_info({TABLE});")
existing_cols = {row[1] for row in cur.fetchall()}
for col in ANGLE_SCHEMAS.keys():
    if col not in existing_cols:
        cur.execute(f'ALTER TABLE {TABLE} ADD COLUMN "{col}" REAL;')
conn.commit()


# ===================== 6) ÇERÇEVE İŞLEME FONKSİYONU ==========================
def process_frame(frame, pose):
    """
    (6) Bir kareyi işler:
        - iskelet overlay
        - eklem açıları (diz için dış açı)
        - daire + sayı + diz arkası kırmızı yay
        - DB satır listesi döndürür (timestamp + açılar) veya None
    """
    h, w = frame.shape[:2]
    res = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    row = None

    if res.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, res.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
        )

        lm = res.pose_landmarks.landmark
        px = {k: lm_xy(lm, i, w, h) for k, i in IDX.items()}

        row = [time.time()]
        for name, (A, B, C) in ANGLE_SCHEMAS.items():
            vis_ok = px[A][1] > 0.5 and px[B][1] > 0.5 and px[C][1] > 0.5
            if not vis_ok:
                row.append(None)
                continue

            inner = angle_3pt(px[A][0], px[B][0], px[C][0])
            val = 360 - inner if "Knee" in name else inner
            row.append(val)

            # görsel
            draw_angle_circle(frame, px[B][0], val)
            if DRAW_KNEE_ARC and "Knee" in name:
                draw_knee_outer_arc(frame, px[B][0], px[A][0], px[C][0])

    return frame, row


# ===================== 7) FOTOĞRAF MODU ======================================
if IS_IMAGE:
    img = cv2.imread(SRC_STR)
    if img is None:
        print("[ERR] Fotoğraf açılamadı:", SRC_STR)
    else:
        with mp_pose.Pose(model_complexity=MODEL_COMPLEXITY,
                          min_detection_confidence=MIN_DET,
                          min_tracking_confidence=MIN_TRACK) as pose:
            frame, row = process_frame(img, pose)

            # DB yaz
            if row is not None:
                cols = ", ".join([f'"{k}"' for k in ANGLE_SCHEMAS.keys()])
                placeholders = ",".join(["?"] * (1 + len(ANGLE_SCHEMAS)))
                cur.execute(
                    f"INSERT INTO {TABLE} (timestamp, {cols}) VALUES ({placeholders})",
                    tuple(row)
                )
                conn.commit()

            # kaydet
            if SAVE:
                ok = cv2.imwrite(OUT_PATH, frame)
                print("[i] Çıktı foto kaydedildi:", OUT_PATH if ok else "[HATA] yazılamadı")

            # preview (C# için)
            write_preview_atomic(frame, PREVIEW_PATH)

            # göster
            if SHOW:
                cv2.imshow("Pose + Diz Arka Açısı", frame)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    conn.close()
    print(f"Kayıt tamam: {DB_PATH}")
    raise SystemExit(0)


# ===================== 8) VİDEO / KAMERA MODU ================================
cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    print("[ERR] Kaynak açılamadı:", VIDEO_SOURCE)
    conn.close()
    raise SystemExit(1)

writer = None
rows_cache = []
paused = False

# 20 FPS gerçek-zaman penceresi
slot_dt = 1.0 / max(1, TARGET_FPS)
next_due = time.time()

with mp_pose.Pose(model_complexity=MODEL_COMPLEXITY,
                  min_detection_confidence=MIN_DET,
                  min_tracking_confidence=MIN_TRACK) as pose:

    while True:
        # nazik durdurma
        if stop_requested(STOPFILE):
            print("[i] Stop flag görüldü, nazik çıkış yapılıyor...")
            break

        # PAUSE modunda bekle ama preview ve klavye çalışsın
        if paused:
            time.sleep(0.05)
            if SHOW:
                key = cv2.waitKey(1) & 0xFF
                if key == 32:  # space -> devam
                    paused = False
            continue

        # ---- 20 FPS zamanlama: zamanı gelene kadar bekle ----
        now = time.time()
        if now < next_due:
            if SHOW:
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == 32:  # pause
                    paused = True
                    continue
                elif key in (81, ord('a')) and not IS_DIGIT:
                    pos = cap.get(cv2.CAP_PROP_POS_MSEC)
                    cap.set(cv2.CAP_PROP_POS_MSEC, max(pos - STEP_SEC * 1000, 0))
                elif key in (83, ord('d')) and not IS_DIGIT:
                    pos = cap.get(cv2.CAP_PROP_POS_MSEC)
                    cap.set(cv2.CAP_PROP_POS_MSEC, pos + STEP_SEC * 1000)
            time.sleep(0.002)  # CPU tasarruf
            continue

        # artık bir kare zamanı geldi
        next_due += slot_dt
        if next_due < now:
            next_due = now  # arkada kaldıysan toparla

        ok, frame = cap.read()
        if not ok:
            break

        frame, row = process_frame(frame, pose)

        # preview (C# için)
        write_preview_atomic(frame, PREVIEW_PATH)

        # DB batch buffer
        if row is not None:
            rows_cache.append(tuple(row))
            if len(rows_cache) >= CACHE_SIZE:
                cols = ", ".join([f'"{k}"' for k in ANGLE_SCHEMAS.keys()])
                placeholders = ",".join(["?"] * (1 + len(ANGLE_SCHEMAS)))
                cur.executemany(
                    f"INSERT INTO {TABLE} (timestamp, {cols}) VALUES ({placeholders})",
                    rows_cache
                )
                conn.commit()
                rows_cache.clear()

        # VideoWriter
        if SAVE:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(OUT_PATH, fourcc, max(1, TARGET_FPS), (w, h))
                if not writer.isOpened():
                    print("[ERR] VideoWriter açılamadı:", OUT_PATH)
                    SAVE = False
            if SAVE:
                writer.write(frame)

        # açık pencere kontrolü
        if SHOW:
            cv2.imshow("Pose + Diz Arka Açısı", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == 32:  # space -> pause
                paused = True
            elif key in (81, ord('a')) and not IS_DIGIT:
                # ← geri
                pos = cap.get(cv2.CAP_PROP_POS_MSEC)
                cap.set(cv2.CAP_PROP_POS_MSEC, max(pos - STEP_SEC * 1000, 0))
            elif key in (83, ord('d')) and not IS_DIGIT:
                # → ileri
                pos = cap.get(cv2.CAP_PROP_POS_MSEC)
                cap.set(cv2.CAP_PROP_POS_MSEC, pos + STEP_SEC * 1000)


# ===================== 9) KAPANIŞ ============================================
# kalanları yaz
if rows_cache:
    cols = ", ".join([f'"{k}"' for k in ANGLE_SCHEMAS.keys()])
    placeholders = ",".join(["?"] * (1 + len(ANGLE_SCHEMAS)))
    cur.executemany(
        f"INSERT INTO {TABLE} (timestamp, {cols}) VALUES ({placeholders})",
        rows_cache
    )
    conn.commit()

# writer kapat
if writer is not None:
    writer.release()

# kaynakları serbest bırak
cap.release()
if SHOW:
    cv2.destroyAllWindows()
conn.close()

print(f"Kayıt tamam: {DB_PATH}")
