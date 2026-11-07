import cv2
import numpy as np
import os
import glob
import itertools
import json
from datetime import datetime
import sys

# Ekran görüntüsü için
try:
    from mss import mss   # pip install mss
except ImportError:
    mss = None

# ==========================
# AYARLAR
# ==========================
CORNERS_DIR = "corners"
TEMP_DIR    = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

SCALE = 0.75

CANNY_LOW  = 50
CANNY_HIGH = 150

# ADAY AYARLARI
TOP_K = 20
MATCH_THRESHOLD = 0.08

# === GEOMETRİK KISITLAMALAR ===
MIN_DIST_PX = 250       # Noktalar arası min mesafe
Y_TOL_RATIO = 0.08      # Yatay hizalama toleransı
SLOPE_SYM_TOL = 0.20    # Eğimlerin birbirine benzeme toleransı
CLUSTER_DIST_RATIO = 0.02


# ==========================
# 1) TEMPLATE YÜKLEME
# ==========================
def load_corner_templates():
    templates = []
    paths = sorted(glob.glob(os.path.join(CORNERS_DIR, "*.*")))
    if not paths:
        raise RuntimeError(f"{CORNERS_DIR} klasöründe patch yok.")

    # JSON çıktısını bozmamak için stdout yerine stderr
    print(f"{len(paths)} köşe patch'i yükleniyor...", file=sys.stderr, flush=True)

    for path in paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        blur = cv2.GaussianBlur(img, (3, 3), 0)
        edge = cv2.Canny(blur, CANNY_LOW, CANNY_HIGH)
        h, w = edge.shape[:2]
        
        if SCALE != 1.0:
            new_w, new_h = max(1, int(w * SCALE)), max(1, int(h * SCALE))
            edge_small = cv2.resize(edge, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            edge_small = edge
            new_w, new_h = w, h

        templates.append({
            "name": os.path.basename(path),
            "edge": edge_small,
            "h": new_h,
            "w": new_w
        })
    return templates


# ==========================
# SIRALAMA (TL, TR, BR, BL)
# ==========================
def order_points(pts):
    pts = np.array(pts, dtype="float32")
    s = pts.sum(axis=1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    
    diff = np.diff(pts, axis=1)
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    
    return np.array([tl, tr, br, bl], dtype="float32")


# ==========================
# EĞİM VE GEOMETRİ KONTROLÜ
# ==========================
def check_geometric_rules(tl, tr, br, bl, img_h):
    # 1. Mesafe Kontrolü
    pts = [tl, tr, br, bl]
    for i in range(4):
        for j in range(i + 1, 4):
            dist = np.linalg.norm(pts[i] - pts[j])
            if dist < MIN_DIST_PX:
                return False, f"Mesafe Yetersiz ({dist:.0f})"

    # 2. Perspektif (Üst kenar < Alt kenar)
    top_width = np.linalg.norm(tr - tl)
    bottom_width = np.linalg.norm(br - bl)
    if top_width > bottom_width * 1.1:  # %10 tolerans
        return False, "Ters Perspektif"

    # 3. Y Hizalaması
    y_tol_px = img_h * Y_TOL_RATIO
    if abs(tl[1] - tr[1]) > y_tol_px:
        return False, "Ust Y Hizasi Bozuk"
    if abs(bl[1] - br[1]) > y_tol_px:
        return False, "Alt Y Hizasi Bozuk"

    # === 4. EĞİM SİMETRİSİ ===
    dy_left = bl[1] - tl[1]
    dx_left = bl[0] - tl[0]
    
    dy_right = br[1] - tr[1]
    dx_right = br[0] - tr[0]

    if abs(dx_left) < 1e-4:
        dx_left = -1e-4
    if abs(dx_right) < 1e-4:
        dx_right = 1e-4

    m_left = dy_left / dx_left
    m_right = dy_right / dx_right

    if m_left > 0:
        return False, "Sol Kenar Egimi Yanlis Yon"
    if m_right < 0:
        return False, "Sag Kenar Egimi Yanlis Yon"

    abs_mL = abs(m_left)
    abs_mR = abs(m_right)
    
    avg_m = (abs_mL + abs_mR) / 2.0
    diff = abs(abs_mL - abs_mR)
    
    ratio = diff / avg_m
    
    if ratio > SLOPE_SYM_TOL:
        return False, f"Egim Simetrik Degil (Fark: %{ratio*100:.1f})"

    return True, "OK"


# ==========================
# EĞİM BAZLI EKSİK NOKTA TAHMİNİ
# ==========================
def estimate_missing_point_by_slope(pts_3):
    pts_np = np.array(pts_3, dtype="float32")
    sorted_y = pts_np[np.argsort(pts_np[:, 1])]
    
    top_p = sorted_y[0]
    bot_p = sorted_y[2]
    mid_p = sorted_y[1]
    
    for i in range(3):
        for j in range(i+1, 3):
            if np.linalg.norm(pts_np[i] - pts_np[j]) < MIN_DIST_PX:
                raise ValueError("Noktalar cok yakin")

    if abs(mid_p[1] - top_p[1]) < abs(mid_p[1] - bot_p[1]):
        tops = sorted([top_p, mid_p], key=lambda p: p[0])
        tl, tr = np.array(tops[0]), np.array(tops[1])
        
        center_x = (tl[0] + tr[0]) / 2
        
        if bot_p[0] < center_x:
            bl = np.array(bot_p)
            dx = bl[0] - tl[0]
            if abs(dx) < 1e-4:
                dx = -1e-4
            m_left = (bl[1] - tl[1]) / dx
            
            m_target = -m_left
            y_target = bl[1]
            dy = y_target - tr[1]
            x_target = tr[0] + (dy / m_target)
            
            br = np.array([x_target, y_target], dtype="float32")
            return [tl, tr, br, bl], br
        
        else:
            br = np.array(bot_p)
            dx = br[0] - tr[0]
            if abs(dx) < 1e-4:
                dx = 1e-4
            m_right = (br[1] - tr[1]) / dx
            
            m_target = -m_right
            y_target = br[1]
            dy = y_target - tl[1]
            x_target = tl[0] + (dy / m_target)
            
            bl = np.array([x_target, y_target], dtype="float32")
            return [tl, tr, br, bl], bl

    else:
        bots = sorted([bot_p, mid_p], key=lambda p: p[0])
        bl, br = np.array(bots[0]), np.array(bots[1])
        center_x = (bl[0] + br[0]) / 2
        
        if top_p[0] < center_x:
            tl = np.array(top_p)
            dx = bl[0] - tl[0]
            if abs(dx) < 1e-4:
                dx = -1e-4
            m_left = (bl[1] - tl[1]) / dx
            
            m_target = -m_left
            y_target = tl[1]
            dy = br[1] - y_target
            x_target = br[0] - (dy / m_target)
            
            tr = np.array([x_target, y_target], dtype="float32")
            return [tl, tr, br, bl], tr
        else:
            tr = np.array(top_p)
            dx = br[0] - tr[0]
            if abs(dx) < 1e-4:
                dx = 1e-4
            m_right = (br[1] - tr[1]) / dx
            
            m_target = -m_right
            y_target = tr[1]
            dy = bl[1] - y_target
            x_target = bl[0] - (dy / m_target)
            
            tl = np.array([x_target, y_target], dtype="float32")
            return [tl, tr, br, bl], tl


# ==========================
# KÜMELEME
# ==========================
def cluster_candidates(candidates, img_w, img_h):
    if not candidates:
        return []
    candidates_sorted = sorted(candidates, key=lambda c: c["score"], reverse=True)
    R = CLUSTER_DIST_RATIO * max(img_w, img_h)
    R2 = R * R
    clusters = []

    for c in candidates_sorted:
        cx, cy, s = c["cx"], c["cy"], c["score"]
        best_idx, best_d2 = None, R2
        for idx, cl in enumerate(clusters):
            d2 = (cx - cl["cx"])**2 + (cy - cl["cy"])**2
            if d2 <= best_d2:
                best_d2 = d2
                best_idx = idx
        
        if best_idx is None:
            clusters.append({"cx": cx, "cy": cy, "score_sum": s, "count": 1})
        else:
            cl = clusters[best_idx]
            tot = cl["score_sum"] + s
            cl["cx"] = (cl["cx"] * cl["score_sum"] + cx * s) / tot
            cl["cy"] = (cl["cy"] * cl["score_sum"] + cy * s) / tot
            cl["score_sum"] = tot
            cl["count"] += 1
    
    return [
        {"cx": cl["cx"], "cy": cl["cy"], "score": cl["score_sum"]}
        for cl in clusters
    ]


# ==========================
# KÖŞE + ORTA ÇİZGİ TESPİTİ
# ==========================
def detect_court_and_midline(img_color, templates):
    h_img, w_img = img_color.shape[:2]
    gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    scale_inv = 1.0 / SCALE
    
    if SCALE != 1.0:
        gray_proc = cv2.resize(gray, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
    else:
        gray_proc = gray

    blur = cv2.GaussianBlur(gray_proc, (3, 3), 0)
    edge_big = cv2.Canny(blur, CANNY_LOW, CANNY_HIGH)
    
    raw_candidates = []
    for tmpl in templates:
        res = cv2.matchTemplate(edge_big, tmpl["edge"], cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val > MATCH_THRESHOLD:
            cx = (max_loc[0] + tmpl["w"]/2) * scale_inv
            cy = (max_loc[1] + tmpl["h"]/2) * scale_inv
            raw_candidates.append({"score": max_val, "cx": cx, "cy": cy})

    candidates = cluster_candidates(raw_candidates, w_img, h_img)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = candidates[:min(TOP_K, len(candidates))]

    # --------------------------------------------------
    # STRATEJİ 1: MÜKEMMEL 4'LÜ
    # --------------------------------------------------
    best_4_pts = None
    best_4_score = -1
    
    if len(top_candidates) >= 4:
        for combo in itertools.combinations(range(len(top_candidates)), 4):
            pts = [(top_candidates[i]["cx"], top_candidates[i]["cy"]) for i in combo]
            
            valid_dist = True
            for i in range(4):
                for j in range(i+1, 4):
                    if np.linalg.norm(
                        np.array(pts[i]) - np.array(pts[j])
                    ) < MIN_DIST_PX:
                        valid_dist = False
                        break
                if not valid_dist:
                    break
            if not valid_dist:
                continue

            ordered = order_points(pts)
            is_valid, _ = check_geometric_rules(
                ordered[0], ordered[1], ordered[2], ordered[3], h_img
            )
            
            if is_valid:
                s_sum = sum(top_candidates[i]["score"] for i in combo)
                if s_sum > best_4_score:
                    best_4_score = s_sum
                    best_4_pts = ordered

    if best_4_pts is not None:
        tl, tr, br, bl = best_4_pts

        # Homografi için hedef dikdörtgen boyutu
        width_top    = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        width  = max(width_top, width_bottom)

        height_left  = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)
        height = max(height_left, height_right)

        dst_pts = np.array([
            [0,        0       ],
            [width-1,  0       ],
            [width-1,  height-1],
            [0,        height-1]
        ], dtype="float32")

        # Homografi: orijinal -> dikdörtgen
        H, status = cv2.findHomography(best_4_pts, dst_pts)

        # Dikdörtgende tam orta yatay çizgi
        mid_y = (height - 1) / 2.0

        midline_dst = np.array([
            [[0.0,       mid_y]],
            [[width-1.0, mid_y]]
        ], dtype=np.float32)

        # Ters homografi ile orijinal uzaya geri
        H_inv = np.linalg.inv(H).astype(np.float32)
        midline_src = cv2.perspectiveTransform(midline_dst, H_inv)
        p1 = midline_src[0, 0]  # (x1, y1)
        p2 = midline_src[1, 0]  # (x2, y2)

        # Soldan sağa sıralama (ml = sol, mr = sağ)
        if p2[0] < p1[0]:
            p1, p2 = p2, p1

        return {
            "tl": tl, "tr": tr, "br": br, "bl": bl,
            "ml": p1, "mr": p2
        }

    # --------------------------------------------------
    # STRATEJİ 2: 3 NOKTA + 1 TAHMİN
    # --------------------------------------------------
    best_3_pts_poly = None
    best_3_score = -1
    
    if len(top_candidates) >= 3:
        for combo in itertools.combinations(range(len(top_candidates)), 3):
            pts_3 = [(top_candidates[i]["cx"], top_candidates[i]["cy"]) for i in combo]
            try:
                full_pts, pred_pt = estimate_missing_point_by_slope(pts_3)
            except ValueError:
                continue
            except Exception:
                continue

            ordered = order_points(full_pts)
            is_valid, _ = check_geometric_rules(
                ordered[0], ordered[1], ordered[2], ordered[3], h_img
            )
            
            if is_valid:
                s_sum = sum(top_candidates[i]["score"] for i in combo)
                if s_sum > best_3_score:
                    best_3_score = s_sum
                    best_3_pts_poly = ordered

    if best_3_pts_poly is not None:
        tl, tr, br, bl = best_3_pts_poly

        width_top    = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        width  = max(width_top, width_bottom)

        height_left  = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)
        height = max(height_left, height_right)

        dst_pts = np.array([
            [0,        0       ],
            [width-1,  0       ],
            [width-1,  height-1],
            [0,        height-1]
        ], dtype="float32")

        H, status = cv2.findHomography(best_3_pts_poly, dst_pts)

        mid_y = (height - 1) / 2.0
        midline_dst = np.array([
            [[0.0,       mid_y]],
            [[width-1.0, mid_y]]
        ], dtype=np.float32)

        H_inv = np.linalg.inv(H).astype(np.float32)
        midline_src = cv2.perspectiveTransform(midline_dst, H_inv)
        p1 = midline_src[0, 0]
        p2 = midline_src[1, 0]

        if p2[0] < p1[0]:
            p1, p2 = p2, p1

        return {
            "tl": tl, "tr": tr, "br": br, "bl": bl,
            "ml": p1, "mr": p2
        }

    # Hiçbir strateji çalışmadı
    return None


# ==========================
# EKRAN GÖRÜNTÜSÜ AL
# ==========================
def take_screenshot():
    if mss is None:
        raise RuntimeError("mss kütüphanesi yok. pip install mss ile yükle.")

    with mss() as sct:
        monitor = sct.monitors[1]  # 1 = ana ekran
        img = sct.grab(monitor)
        frame = np.array(img)      # BGRA
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(TEMP_DIR, f"{ts}.jpg")
        cv2.imwrite(path, frame)
        return frame, path


# ==========================
# DEBUG ÇİZİM (sadece dosyaya)
# ==========================
def draw_debug_image(img, result):
    out = img.copy()
    tl, tr, br, bl = result["tl"], result["tr"], result["br"], result["bl"]
    ml, mr = result["ml"], result["mr"]

    # Kort poligonu (mavi)
    poly = np.array([tl, tr, br, bl], dtype=np.int32)
    cv2.polylines(out, [poly], True, (255, 0, 0), 3)

    for p in [tl, tr, br, bl]:
        cv2.circle(out, (int(p[0]), int(p[1])), 6, (255, 0, 0), -1)

    # Orta çizgi + kırmızı daireler
    cv2.line(
        out,
        (int(ml[0]), int(ml[1])),
        (int(mr[0]), int(mr[1])),
        (0, 0, 255),
        3
    )

    # 4 nokta: 1=TL, 2=TR, 3=ML, 4=MR
    key_points = [
        ("1", tl),
        ("2", tr),
        ("3", ml),
        ("4", mr)
    ]

    for label, p in key_points:
        x, y = int(p[0]), int(p[1])
        cv2.circle(out, (x, y), 10, (0, 0, 255), -1)
        cv2.putText(out, label, (x + 12, y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return out


# ==========================
# MAIN
# ==========================
def main():
    try:
        templates = load_corner_templates()
    except Exception as e:
        print(json.dumps({"error": f"template_error: {e}"}))
        return

    try:
        img, img_path = take_screenshot()
    except Exception as e:
        print(json.dumps({"error": f"screenshot_error: {e}"}))
        return

    result = detect_court_and_midline(img, templates)

    if result is None:
        print(json.dumps({
            "error": "court_not_found",
            "temp_image": img_path
        }))
        return

    # Debug resmi dosyaya kaydediyoruz (ama pencere açmıyoruz)
    debug_img = draw_debug_image(img, result)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_debug")
    debug_path = os.path.join(TEMP_DIR, f"{ts}.jpg")
    cv2.imwrite(debug_path, debug_img)

    tl = result["tl"]
    tr = result["tr"]
    ml = result["ml"]
    mr = result["mr"]

    out_json = {
        "tl": [float(tl[0]), float(tl[1])],
        "tr": [float(tr[0]), float(tr[1])],
        "ml": [float(ml[0]), float(ml[1])],
        "mr": [float(mr[0]), float(mr[1])],
        "temp_image": img_path,
        "debug_image": debug_path
    }

    # C# tarafı bunu okuyup textBox1-4'e yazacak
    print(json.dumps(out_json))


if __name__ == "__main__":
    main()
