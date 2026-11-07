# -*- coding: utf-8 -*-
"""
Thermal bacak görüntüsünden anatomik noktalar:

- KASIK: İki bacağın ilk ayrıldığı satır (biraz yukarı kaydırılmış)
- UST_DIZ_L, UST_DIZ_R → çizgi
- ALT_DIZ_L, ALT_DIZ_R → çizgi
- BILEK_L, BILEK_R → çizgi
- L_PARMAK, R_PARMAK → çizgi
- Kasık hariç tüm noktalar çizgi olarak gösterilir.
- İki yeni görüntü: üst bacak ve alt bacak bölgeleri.
- Kasık merkezinde, dikine elips — sadece person_kirmizi üzerinde görünür.
- Sağ ve sol üst bacak (UST_DIZ'den yukarı person_kirmizi içine kadar):
    → alanı eşit 3 dikey parçaya bölünür, renklendirilir ve numaralanır.
"""

import cv2
import numpy as np
from skimage.morphology import medial_axis
from skimage.measure import label, regionprops
from scipy.ndimage import gaussian_filter1d
from collections import deque


IMG_PATH    = r"termal_bacak2.jpg"
OUT_VIS     = r"termal_anatomik_pose3.png"
SHOW_WINDOW = True


# ===========================================================
# [F1] THERMAL → BINARY + SİMETRİ
# ===========================================================
def segment_thermal_to_binary(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(img_path)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([90, 50, 50], dtype=np.uint8)
    upper_blue = np.array([130, 255, 255], dtype=np.uint8)

    mask_bg = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_fg = cv2.bitwise_not(mask_bg)

    k = np.ones((5, 5), np.uint8)
    mask_fg = cv2.morphologyEx(mask_fg, cv2.MORPH_OPEN, k)
    mask_fg = cv2.morphologyEx(mask_fg, cv2.MORPH_CLOSE, k)

    cnts, _ = cv2.findContours(mask_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        raise RuntimeError("Kontur bulunamadı.")

    largest = max(cnts, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    final_mask = np.zeros_like(mask_fg)
    cv2.drawContours(final_mask, [largest], -1, 255, -1)

    symmetry_x = x + w // 2
    return img, final_mask, (x, y, w, h), symmetry_x


# ===========================================================
# [F2] GÖVDEDEN ALT BACAK İSKELET PARÇALARI
# ===========================================================
def row_width_profile(mask):
    prof = (mask > 0).sum(axis=1).astype(np.float32)
    return gaussian_filter1d(prof, sigma=3)


def extract_lower_from_binary_mask(mask):
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    person = (mask > 0).astype(np.uint8) * 255

    lbl = label(person > 0)
    if lbl.max() == 0:
        raise RuntimeError("Silüet bulunamadı.")
    props = regionprops(lbl)
    person_label = max(props, key=lambda p: p.area).label
    person = (lbl == person_label).astype(np.uint8) * 255

    H, W = person.shape

    # --- UST_DIZ seviyesi: genişlik profil tepe noktası ---
    prof = row_width_profile(person)
    hips_min = int(0.45 * H)
    hips_max = int(0.80 * H)
    y_hips = int(np.argmax(prof[hips_min:hips_max]) + hips_min)

    xs = np.where(person[y_hips, :] > 0)[0]
    if xs.size < 2:
        raise RuntimeError("UST_DIZ kenarları bulunamadı.")
    ust_diz_l = (int(xs[0]),  y_hips)
    ust_diz_r = (int(xs[-1]), y_hips)

    # --- Ayak bilekleri: alt bant ---
    cnts, _ = cv2.findContours(person, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cnts, key=cv2.contourArea)
    pts = cnt[:, 0, :]
    ymax = pts[:, 1].max()
    band_lo = int(ymax - 0.08 * H)
    band_pts = pts[pts[:, 1] >= band_lo]
    if band_pts.size == 0:
        band_pts = pts[pts[:, 1] >= ymax - 1]

    ayak_bilek_l = tuple(band_pts[np.argmin(band_pts[:, 0])])
    ayak_bilek_r = tuple(band_pts[np.argmax(band_pts[:, 0])])

    # --- BILEK (diz kapağı): medial axis ile en dar nokta ---
    skel_bool, dist = medial_axis(person > 0, return_distance=True)
    sk = skel_bool.astype(np.uint8)

    lower = np.zeros_like(sk)
    lower[y_hips + 2:, :] = sk[y_hips + 2:, :]
    lbl_l = label(lower > 0)
    comps = [p for p in regionprops(lbl_l) if p.area > 10]
    comps = sorted(comps, key=lambda p: p.area, reverse=True)[:2]

    def bilek_on_component(comp_mask, ayak_bilek_xy):
        ys, xs = np.where(comp_mask)
        if xs.size == 0:
            return None
        ay = ayak_bilek_xy[1]
        Hloc = person.shape[0]
        valid = (ys > y_hips + int(0.1 * Hloc)) & (ys < ay - int(0.05 * Hloc))
        xs2, ys2 = xs[valid], ys[valid]
        if xs2.size == 0:
            return None
        rad = dist[ys2, xs2]
        i = int(np.argmin(rad))  # en dar nokta = diz kapağı
        return (int(xs2[i]), int(ys2[i]))

    bilek_l = bilek_r = None
    if len(comps) == 2:
        c1, c2 = comps
        c1xs = np.mean(np.where(lbl_l == c1.label)[1])
        c2xs = np.mean(np.where(lbl_l == c2.label)[1])
        if c1xs < c2xs:
            bilek_l = bilek_on_component(lbl_l == c1.label, ayak_bilek_l)
            bilek_r = bilek_on_component(lbl_l == c2.label, ayak_bilek_r)
        else:
            bilek_l = bilek_on_component(lbl_l == c2.label, ayak_bilek_l)
            bilek_r = bilek_on_component(lbl_l == c1.label, ayak_bilek_r)

    return ust_diz_l, ust_diz_r, bilek_l, bilek_r, ayak_bilek_l, ayak_bilek_r, y_hips, person


# ===========================================================
# [F3] KASIK: İLK AYRILMA SATIRI + YUKARI KAYDIRMA
# ===========================================================
def find_groin_from_components(person, bbox):
    H, W = person.shape
    bx, by, bw, bh = bbox

    y_min = max(int(0.15 * H), by)
    y_max = min(int(0.90 * H), by + bh)
    MIN_AREA = 30

    groin_y = None

    # İlk ayrılma satırını bul
    for y in range(y_min, y_max):
        sub = person[y:, :] > 0
        lbl = label(sub)
        comps = [p for p in regionprops(lbl) if p.area > MIN_AREA]
        if len(comps) >= 2:
            groin_y = y
            break

    # Eğer bulunamazsa fallback
    if groin_y is None:
        last_one_y = None
        for y in range(y_min, y_max):
            sub = person[y:, :] > 0
            lbl = label(sub)
            comps = [p for p in regionprops(lbl) if p.area > MIN_AREA]
            if len(comps) == 1:
                last_one_y = y
            elif len(comps) >= 2 and last_one_y is not None:
                break
        groin_y = last_one_y if last_one_y is not None else (y_min + y_max) // 2

    # Kasığı biraz yukarı kaydır (anatomik doğruluk için)
    offset = int(0.012 * H)
    groin_y = max(y_min, groin_y - offset)

    xs = np.where(person[groin_y, :] > 0)[0]
    if xs.size >= 2:
        groin_x = (int(xs[0]) + int(xs[-1])) // 2
    else:
        groin_x = bx + bw // 2

    return groin_x, groin_y


# ===========================================================
# [F4] PARMAKLAR
# ===========================================================
def find_toes_from_person_mask(person):
    H, W = person.shape
    cnts, _ = cv2.findContours(person, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return None, None
    cnt = max(cnts, key=cv2.contourArea)
    pts = cnt[:, 0, :]
    ymax = pts[:, 1].max()
    band_lo = int(ymax - 0.05 * H)
    toe_pts = pts[pts[:, 1] >= band_lo]
    if toe_pts.size == 0:
        toe_pts = pts[pts[:, 1] >= ymax - 1]

    toe_l = tuple(toe_pts[np.argmin(toe_pts[:, 0])])
    toe_r = tuple(toe_pts[np.argmax(toe_pts[:, 0])])
    return toe_l, toe_r


# ===========================================================
# [F5] MEDIAL AXIS YAKIN NOKTA + BFS YOL TAKİBİ
# ===========================================================
def nearest_skel_point(skel, pt, H, W, max_r=10):
    x0, y0 = pt
    best = None
    best_d2 = None

    for r in range(max_r + 1):
        y_min = max(0, y0 - r)
        y_max = min(H - 1, y0 + r)
        x_min = max(0, x0 - r)
        x_max = min(W - 1, x0 + r)

        found_any = False
        for yy in range(y_min, y_max + 1):
            for xx in range(x_min, x_max + 1):
                if skel[yy, xx]:
                    d2 = (xx - x0)**2 + (yy - y0)**2
                    if best_d2 is None or d2 < best_d2:
                        best_d2 = d2
                        best = (xx, yy)
                        found_any = True
        if found_any:
            break

    return best  # (x, y) ya da None


def trace_medial_path(skel, start_pt, end_pt, H, W):
    # Başlangıç ve bitişi en yakın iskelet pikseline çek
    start_near = nearest_skel_point(skel, start_pt, H, W, max_r=10)
    end_near   = nearest_skel_point(skel, end_pt,   H, W, max_r=10)

    if start_near is None or end_near is None:
        return None

    start = (start_near[1], start_near[0])  # (y, x)
    end   = (end_near[1],   end_near[0])    # (y, x)

    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),           (0,1),
                  (1,-1),  (1,0),   (1,1)]

    queue = deque([(start, [start])])
    visited = set([start])

    while queue:
        (y, x), path = queue.popleft()

        if (y, x) == end:
            return [(p[1], p[0]) for p in path]  # (x, y)

        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            if (0 <= ny < H and 0 <= nx < W and
                skel[ny, nx] and (ny, nx) not in visited):
                visited.add((ny, nx))
                queue.append(((ny, nx), path + [(ny, nx)]))

    return None  # yol bulunamadı


# ===========================================================
# [F6] ALT_DIZ: TERMAL GRADYAN + FALLBACK
# ===========================================================
def find_alt_diz_by_thermal_gradient(path, hsv_img, H, W, y_top, y_bottom):
    if len(path) < 3:
        return None

    scores = []
    ys_path = []

    for (x, y) in path:
        if not (0 <= x < W and 0 <= y < H):
            scores.append(0.0)
            ys_path.append(y)
            continue

        h, s, v = hsv_img[y, x]  # HSV

        whiteness = float(v) - float(s)

        if h < 15 or h > 165:
            redness = float(s)
        else:
            redness = 0.0

        score = redness - whiteness
        scores.append(score)
        ys_path.append(y)

    scores = np.array(scores, dtype=np.float32)
    ys_path = np.array(ys_path, dtype=np.int32)

    grads = np.abs(np.diff(scores))
    if grads.size == 0:
        return None

    y_mid = ys_path[:-1]
    mask = (y_mid > y_top) & (y_mid < y_bottom)

    if mask.any():
        grads_masked = grads.copy()
        grads_masked[~mask] = 0.0
        idx = int(np.argmax(grads_masked))
    else:
        idx = int(np.argmax(grads))

    cand_x, cand_y = path[idx]

    if not (y_top < cand_y < y_bottom):
        candidates = [p for p in path if y_top < p[1] < y_bottom]
        if not candidates:
            return None
        cand_x, cand_y = candidates[len(candidates) // 2]

    return (int(cand_x), int(cand_y))


def find_mid_leg_points(ust_diz_l, ust_diz_r, bilek_l, bilek_r, person_mask, thermal_img):
    H, W = person_mask.shape

    skel_bool = medial_axis(person_mask > 0)
    skel = skel_bool.astype(np.uint8)

    hsv = cv2.cvtColor(thermal_img, cv2.COLOR_BGR2HSV)

    alt_diz_l = alt_diz_r = None

    # SOL BACAK
    if ust_diz_l is not None and bilek_l is not None:
        path_l = trace_medial_path(skel, ust_diz_l, bilek_l, H, W)
        if path_l and len(path_l) > 5:
            y_top_l = ust_diz_l[1]
            y_bottom_l = bilek_l[1]
            if y_top_l < y_bottom_l:
                alt_diz_l = find_alt_diz_by_thermal_gradient(
                    path_l, hsv, H, W, y_top_l, y_bottom_l
                )
        if alt_diz_l is None:
            alt_diz_l = (
                int(ust_diz_l[0] * 0.7 + bilek_l[0] * 0.3),
                int(ust_diz_l[1] * 0.7 + bilek_l[1] * 0.3)
            )

    # SAĞ BACAK
    if ust_diz_r is not None and bilek_r is not None:
        path_r = trace_medial_path(skel, ust_diz_r, bilek_r, H, W)
        if path_r and len(path_r) > 5:
            y_top_r = ust_diz_r[1]
            y_bottom_r = bilek_r[1]
            if y_top_r < y_bottom_r:
                alt_diz_r = find_alt_diz_by_thermal_gradient(
                    path_r, hsv, H, W, y_top_r, y_bottom_r
                )
        if alt_diz_r is None:
            alt_diz_r = (
                int(ust_diz_r[0] * 0.7 + bilek_r[0] * 0.3),
                int(ust_diz_r[1] * 0.7 + bilek_r[1] * 0.3)
            )

    return alt_diz_l, alt_diz_r


# ===========================================================
# [F7] KASIK ELİPSİNİ ÇİZ (person_kirmizi'ye GÖRE)
# ===========================================================
def draw_groin_ellipses_clipped(vis, groin, person_mask, person_kirmizi=None):
    gx, gy = int(groin[0]), int(groin[1])
    H, W = vis.shape[:2]

    # Yüksekliğe göre oransal yarıçaplar
    base_a = int(0.03 * H)  # yatay yarıçap
    base_b = int(0.06 * H)  # dikey yarıçap

    axes_list = [
        (int(base_a * 2.5), int(base_b * 2.5)),
    ]

    colors = [
        (0,   0, 255),
        (0, 255,   0),
        (255, 0,   0),
        (0, 255, 255),
        (255, 0, 255),
    ]

    for axes, color in zip(axes_list, colors):
        ellipse_mask = np.zeros_like(person_mask, dtype=np.uint8)
        cv2.ellipse(
            ellipse_mask,
            (gx, gy),
            axes,
            0,          # major eksen dikey
            0, 360,
            255,
            -1,
            lineType=cv2.LINE_AA
        )

        # Hangi maskeyle kesileceğine karar ver:
        if person_kirmizi is not None:
            base_mask = person_kirmizi
        else:
            base_mask = person_mask

        clipped_mask = cv2.bitwise_and(ellipse_mask, base_mask)
        vis[clipped_mask > 0] = color



def horizontal_leg_line(mask, y):
    """
    mask = person_kirmizi veya person
    y    = çizginin dikey seviyesi
    Bu fonksiyon bacak hacmi içinde yatay tam bir çizgi döndürür.
    """
    if y < 0 or y >= mask.shape[0]:
        return None, None
    
    row = mask[y, :] > 0
    xs = np.where(row)[0]
    if xs.size < 2:
        return None, None
    
    return (int(xs[0]), int(y)), (int(xs[-1]), int(y))


def split_lower_leg_area(mask, y_top, y_bottom, x_left, x_right):
    """
    mask     : person_kirmizi veya person
    y_top    : alt diz satırı
    y_bottom : bilek satırı
    x_left,x_right : bacağın yatay sınırları (sol veya sağ)
    Çıkış: dikey bölme x_böl, bölge sınırları
    """
    # Yatay eksende örnek noktalar
    xs = np.arange(x_left, x_right + 1)

    heights = np.zeros_like(xs, dtype=np.int64)

    # Her sütunda mask içindeki piksel sayısı
    for i, x in enumerate(xs):
        col = mask[y_top:y_bottom+1, x] > 0
        heights[i] = col.sum()

    total = heights.sum()
    if total == 0:
        return None, None

    cumsum = np.cumsum(heights)
    half = total / 2.0
    idx = int(np.searchsorted(cumsum, half))
    idx = max(1, min(len(xs)-2, idx))

    x_split = int(xs[idx])
    return x_split, xs

# ===========================================================
# [F8] ANA
# ===========================================================
def main():
    # ---- 1) Segmentasyon + iskelet ----
    img, final_mask, bbox, symmetry_x = segment_thermal_to_binary(IMG_PATH)
    ust_diz_l, ust_diz_r, bilek_l, bilek_r, ayak_bilek_l, ayak_bilek_r, y_hips, person = \
        extract_lower_from_binary_mask(final_mask)

    kasik_x, kasik_y = find_groin_from_components(person, bbox)
    GROIN = (kasik_x, kasik_y)

    ALT_DIZ_L, ALT_DIZ_R = find_mid_leg_points(
        ust_diz_l, ust_diz_r, bilek_l, bilek_r, person, img)

    TOE_L, TOE_R = find_toes_from_person_mask(person)

    # ---- 2) person_kirmizi filtresi ----
    # ---- 2) person_kirmizi filtresi ----
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 2.1 KIRMIZI + BEYAZ SICAK BÖLGE MASKESİ
    lower_red1 = np.array([0, 70, 80], dtype=np.uint8)
    upper_red1 = np.array([10, 255, 255], dtype=np.uint8)
    lower_red2 = np.array([170, 70, 80], dtype=np.uint8)
    upper_red2 = np.array([180, 255, 255], dtype=np.uint8)

    mask_red1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # beyaz/sıcak
    lower_white = np.array([0, 0, 180], dtype=np.uint8)
    upper_white = np.array([180, 80, 255], dtype=np.uint8)
    mask_white = cv2.inRange(hsv_img, lower_white, upper_white)

    mask_kirmizi_ham = cv2.bitwise_or(mask_red, mask_white)

    # 2.2 SADECE KİŞİ ÜZERİNDEKİ SICAK BÖLGE
    person_bool = (person > 0).astype(np.uint8) * 255
    person_kirmizi = cv2.bitwise_and(mask_kirmizi_ham, person_bool)

    # 2.3 MORFOLOJİK TEMİZLİK
    k = np.ones((5, 5), np.uint8)
    person_kirmizi = cv2.morphologyEx(person_kirmizi, cv2.MORPH_OPEN, k)
    person_kirmizi = cv2.morphologyEx(person_kirmizi, cv2.MORPH_CLOSE, k)

    # ======================================================
    #  2.4 YENİ FİLTRE: SADECE "ELLERİ" KALDIRMA
    #  - kasık Y seviyesinin ÜSTÜNDE:
    #       sadece simetri ekseni etrafında orta bant kalsın
    #       (yanlara taşan kollar/eller gitsin)
    #  - kasık Y seviyesinin ALTINDA:
    #       hiçbir şeye dokunma, olduğu gibi kalsın
    # ======================================================

    H_p, W_p = person_kirmizi.shape

    # güvenli symmetry_x
    x0 = int(symmetry_x)
    x0 = max(0, min(W_p - 1, x0))

    # kasık Y seviyesini kullanacağız (GROIN main içinde sonra tanımlanıyor,
    # ama kasik_y değişkeni yukarıda mevcut, onu kullanıyoruz)
    kasik_y_local = int(kasik_y)  # main'deki kasik_y değişkeni

    # Merkez bant genişliği:
    # - geniş tutulursa bacakların yan tarafları korunur
    # - çok dar olursa bacağın dış kısmı da kesilir
    # Deneme için: person dikdörtgeninin genişliğinin ~%35'i
    bx, by, bw, bh = bbox
    half_band = int(bw * 0.35)

    x1_band = max(0, x0 - half_band)
    x2_band = min(W_p - 1, x0 + half_band)

    # Bant maskesi: 
    # - 0..kasik_y satırlarında sadece orta bant
    # - kasik_y..H satırlarında her yer (alt bacaklar özgür)
    band_mask = np.zeros_like(person_kirmizi, dtype=np.uint8)
    # üst kısım: sadece merkez bant
    band_mask[0:kasik_y_local, x1_band:x2_band] = 255
    # alt kısım: tamamen açık
    band_mask[kasik_y_local:H_p, :] = 255

    # person_kirmizi'yi bu bant ile kes (eller/kollar üstte yanlarda ise gider)
    person_kirmizi = cv2.bitwise_and(person_kirmizi, band_mask)

    cv2.imwrite("person_kirmizi.png", person_kirmizi)
    print("Kaydedildi: person_kirmizi.png (eller filtrelenmiş)")


    # ---- 3) Görsel kopyası ----
    vis = img.copy()
    bx, by, bw, bh = bbox

    # Kasık dikey çizgisi
   # cv2.line(vis, (kasik_x, by), (kasik_x, by + bh), (0, 0, 255), 2)

    # ---- 4) Nokta ve çizgi çizme yardımcıları ----
    def draw_point(p, color, text=None):
        if p is None:
            return
        cv2.circle(vis, (int(p[0]), int(p[1])), 6, color, -1)
        if text:
            cv2.putText(vis, text, (int(p[0]) + 5, int(p[1]) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
                        

    def draw_line_between_points(p1, p2, color, text=None):
        if p1 is None and p2 is None:
            return

        if p1 is None:
            p1 = (GROIN[0] - (p2[0] - GROIN[0]), p2[1])
        if p2 is None:
            p2 = (GROIN[0] + (GROIN[0] - p1[0]), p1[1])

        cv2.line(vis, (int(p1[0]), int(p1[1])),
                      (int(p2[0]), int(p2[1])), color, 2)

        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2
        cv2.circle(vis, (int(mid_x), int(mid_y)), 6, color, -1)

        if text:
            cv2.putText(vis, text, (int(mid_x) + 5, int(mid_y) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    # ---- 5) Anatomik noktaları çiz ----
    draw_point(GROIN, (255, 0, 255), "KASIK")
    draw_line_between_points(ust_diz_l, ust_diz_r, (0, 255, 0), "UST_DIZ")
   # draw_line_between_points(ALT_DIZ_L, ALT_DIZ_R, (255, 165, 0), "ALT_DIZ")
    # --- ALT DIZ: düz yatay çizgi ---
# ============================
#  ALT BACAĞI 2 PARÇAYA BÖL
# ============================
# ============================
#   ALT BACAK SOL & SAĞ – 2 BÖLGE
# ============================
    if ALT_DIZ_L is not None and ALT_DIZ_R is not None and bilek_l is not None and bilek_r is not None:

        base_mask = person_kirmizi if np.any(person_kirmizi > 0) else person

        # Dikey sınırlar
        y_top_lower = int((ALT_DIZ_L[1] + ALT_DIZ_R[1]) / 2)
        y_bottom_lower = int((bilek_l[1] + bilek_r[1]) / 2)

        # Evvelce yazılan split_lower_leg_area fonksiyonunu kullanıyoruz

        # ======================================
        # 1) SOL BACAK
        # ======================================
        row_sol = base_mask[y_top_lower, :] > 0
        xs_sol = np.where(row_sol)[0]
        xs_sol = xs_sol[xs_sol <= GROIN[0]]   # sol taraf

        if xs_sol.size > 5:
            x_left_sol = int(xs_sol[0])
            x_right_sol = int(xs_sol[-1])

            x_split_sol, xs_arr_sol = split_lower_leg_area(
                base_mask,
                y_top_lower,
                y_bottom_lower,
                x_left_sol,
                x_right_sol
            )

            if x_split_sol:

                # --- Dikey bölme çizgisi ---
                cv2.line(
                    vis,
                    (x_split_sol, y_top_lower),
                    (x_split_sol, y_bottom_lower),
                    (255,255,0), 2
                )

                # --- 2 bölge renklendirme (person ile AND yapılarak) ---
                boundaries_sol = [x_left_sol, x_split_sol, x_right_sol]
                colors = [(0,0,255), (0,255,0)]
                alpha = 0.28

                for idx in range(2):
                    x1 = boundaries_sol[idx]
                    x2 = boundaries_sol[idx+1]

                    # Dikdörtgen maskesi
                    rect_mask = np.zeros_like(base_mask, dtype=np.uint8)
                    cv2.rectangle(rect_mask,
                                  (x1, y_top_lower),
                                  (x2, y_bottom_lower),
                                  255, -1)

                    # person AND bölge
                    clipped = cv2.bitwise_and(rect_mask, base_mask)

                    overlay = vis.copy()
                    overlay[clipped > 0] = colors[idx]
                    vis[:] = cv2.addWeighted(overlay, alpha, vis, 1-alpha, 0)

                    # Küçük numara
                    cx = (x1 + x2) // 2
                    cy = (y_top_lower + y_bottom_lower) // 2
                    cv2.putText(
                        vis, f"{idx+1}",
                        (cx-8, cy+5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,               # ÜST BACAKLA AYNI BOY
                        (255,255,255),
                        2,                 # ÜST BACAKLA AYNI KALINLIK
                        cv2.LINE_AA
                    )


    # ======================================
    # 2) SAĞ BACAK
    # ======================================
    row_sag = base_mask[y_top_lower, :] > 0
    xs_sag = np.where(row_sag)[0]
    xs_sag = xs_sag[xs_sag >= GROIN[0]]   # sağ taraf

    if xs_sag.size > 5:
        x_left_sag = int(xs_sag[0])
        x_right_sag = int(xs_sag[-1])

        x_split_sag, xs_arr_sag = split_lower_leg_area(
            base_mask,
            y_top_lower,
            y_bottom_lower,
            x_left_sag,
            x_right_sag
        )

        if x_split_sag:

            cv2.line(
                vis,
                (x_split_sag, y_top_lower),
                (x_split_sag, y_bottom_lower),
                (0,255,255), 2
            )

            boundaries_sag = [x_left_sag, x_split_sag, x_right_sag]
            colors = [(255,0,0), (0,255,255)]
            alpha = 0.28

            for idx in range(2):
                x1 = boundaries_sag[idx]
                x2 = boundaries_sag[idx+1]

                rect_mask = np.zeros_like(base_mask, dtype=np.uint8)
                cv2.rectangle(rect_mask,
                              (x1, y_top_lower),
                              (x2, y_bottom_lower),
                              255, -1)

                clipped = cv2.bitwise_and(rect_mask, base_mask)

                overlay = vis.copy()
                overlay[clipped > 0] = colors[idx]
                vis[:] = cv2.addWeighted(overlay, alpha, vis, 1-alpha, 0)

                cx = (x1 + x2) // 2
                cy = (y_top_lower + y_bottom_lower) // 2
                # cv2.putText(
                    # vis, f"D{idx+1}",
                    # (cx-8, cy+5),
                    # cv2.FONT_HERSHEY_SIMPLEX,
                    # 0.7,               # ÜST BACAKLA AYNI BOY
                    # (255,255,255),
                    # 2,                 # ÜST BACAKLA AYNI KALINLIK
                    # cv2.LINE_AA
                # )



    # ======================================
    # 2) SAĞ BACAK ALT HACMİNİ BUL
    # ======================================
    row_sag = base_mask[y_top_lower, :] > 0
    xs_sag = np.where(row_sag)[0]
    xs_sag = xs_sag[xs_sag >= GROIN[0]]   # sadece sağ taraf

    if xs_sag.size > 5:
        x_left_sag = int(xs_sag[0])
        x_right_sag = int(xs_sag[-1])

        x_split_sag, xs_sag_arr = split_lower_leg_area(
            base_mask, y_top_lower, y_bottom_lower,
            x_left_sag, x_right_sag
        )
        if x_split_sag:

            cv2.line(
                vis,
                (x_split_sag, y_top_lower),
                (x_split_sag, y_bottom_lower),
                (0,255,255), 2
            )

            boundaries_sag = [x_left_sag, x_split_sag, x_right_sag]
            colors = [(255,0,0), (0,255,255)]
            alpha = 0.28

            for idx in range(2):
                x1 = boundaries_sag[idx]
                x2 = boundaries_sag[idx + 1]

                overlay = vis.copy()
                cv2.rectangle(
                    overlay,
                    (x1, y_top_lower),
                    (x2, y_bottom_lower),
                    colors[idx],
                    -1
                )
                vis[:] = cv2.addWeighted(overlay, alpha, vis, 1-alpha, 0)

                cx = (x1+x2)//2
                cy = (y_top_lower+y_bottom_lower)//2
                cv2.putText(
                    vis, f"{idx+1}",
                    (cx-10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255,255,255), 2, cv2.LINE_AA
                )
    
    
    if ALT_DIZ_L is not None and ALT_DIZ_R is not None:
        # Ortalama Y seviyesi
        y_alt = int((ALT_DIZ_L[1] + ALT_DIZ_R[1]) / 2)

        # Hangi maskeye göre çizilecek?
        base_mask = person_kirmizi if np.any(person_kirmizi > 0) else person

        alt_L, alt_R = horizontal_leg_line(base_mask, y_alt)

        if alt_L and alt_R:
            cv2.line(vis, alt_L, alt_R, (255,165,0), 2)
            draw_point(alt_L, (255,165,0))
            draw_point(alt_R, (255,165,0))
     
   # draw_line_between_points(bilek_l, bilek_r, (0, 255, 255), "BILEK")
   # --- BILEK: düz yatay çizgi ---
    if bilek_l is not None and bilek_r is not None:
        y_bilek = int((bilek_l[1] + bilek_r[1]) / 2)

        base_mask = person_kirmizi if np.any(person_kirmizi > 0) else person

        bL, bR = horizontal_leg_line(base_mask, y_bilek)

        if bL and bR:
            cv2.line(vis, bL, bR, (0,255,255), 2)
            draw_point(bL, (0,255,255))
            draw_point(bR, (0,255,255))

    #draw_line_between_points(TOE_L, TOE_R, (255, 128, 0), "PARMAK")
# --- PARMAK: düz yatay çizgi ---
    if TOE_L is not None and TOE_R is not None:
        # Ortalama Y seviyesi
        y_toe = int((TOE_L[1] + TOE_R[1]) / 2)

        # Hangi maskede çalışacağız? Kırmızı bölgeler daha doğru segment sunuyorsa onu kullanıyoruz.
        base_mask = person_kirmizi if np.any(person_kirmizi > 0) else person

        toe_L, toe_R = horizontal_leg_line(base_mask, y_toe)

        if toe_L and toe_R:
            cv2.line(vis, toe_L, toe_R, (255,128,0), 2)
            draw_point(toe_L, (255,128,0))
            draw_point(toe_R, (255,128,0))

    # Kasıktaki elips (person_kirmizi içinde)
    draw_groin_ellipses_clipped(vis, GROIN, person, person_kirmizi)

    print("symmetry_x:", symmetry_x)
    print("KASIK     :", GROIN)
    print("UST_DIZ_L :", ust_diz_l)
    print("UST_DIZ_R :", ust_diz_r)
    print("ALT_DIZ_L :", ALT_DIZ_L)
    print("ALT_DIZ_R :", ALT_DIZ_R)
    print("BILEK_L   :", bilek_l)
    print("BILEK_R   :", bilek_r)

    # ---- 6) Üst ve alt bacak görüntülerini kaydet ----
    H, W = vis.shape[:2]
    if ust_diz_l is not None and ust_diz_r is not None:
        y_top = min(kasik_y, ust_diz_l[1], ust_diz_r[1])
        y_bottom = max(kasik_y, ust_diz_l[1], ust_diz_r[1])
    else:
        y_top = kasik_y
        y_bottom = kasik_y + 50

    upper_region = vis[y_top:y_bottom, :]
    cv2.imwrite("termal_anatomik_upper_leg.png", upper_region)
    print("Kaydedildi: termal_anatomik_upper_leg.png")

    if ALT_DIZ_L is not None and ALT_DIZ_R is not None and bilek_l is not None and bilek_r is not None:
        y_top2 = min(ALT_DIZ_L[1], ALT_DIZ_R[1])
        y_bottom2 = max(bilek_l[1], bilek_r[1])
    else:
        y_top2 = 0
        y_bottom2 = H

    lower_region = vis[y_top2:y_bottom2, :]
    cv2.imwrite("termal_anatomik_lower_leg.png", lower_region)
    print("Kaydedildi: termal_anatomik_lower_leg.png")

    # ------------------------------------------------
    # 7) SAĞ ÜST BACAK HACMİNİ (UST_DIZ_R → person_kirmizi üst sınırı)
    #    3 EŞ ALANLI DİKİNE PARÇAYA BÖL
    # ------------------------------------------------
    if ust_diz_r is not None and GROIN is not None and person_kirmizi is not None:
        y_ust = int(ust_diz_r[1])
        gx = int(GROIN[0])

        H_p, W_p = person_kirmizi.shape

        # person_kirmizi maskesi yukarı doğru nerede bitiyor? (sağ taraf)
        top_limit_r = None
        for yy in range(y_ust - 1, -1, -1):
            row = person_kirmizi[yy, :] > 0
            xs_all = np.where(row)[0]
            xs_right = xs_all[xs_all >= gx]
            if xs_right.size > 3:
                top_limit_r = yy
            else:
                break

        if top_limit_r is None:
            top_limit_r = max(0, y_ust - 80)

        y_top_r = int(top_limit_r)

        # UST_DIZ satırında sağ bacak sınırları (person_kirmizi)
        row = person_kirmizi[y_ust, :] > 0
        xs_all = np.where(row)[0]
        xs_right = xs_all[xs_all >= gx]

        if xs_right.size > 3:
            x_start_r = int(xs_right[0])
            x_end_r   = int(xs_right[-1])

            xs = np.arange(x_start_r, x_end_r + 1)
            heights = np.zeros_like(xs, dtype=np.int64)

            for i, x in enumerate(xs):
                col = person_kirmizi[y_top_r:y_ust + 1, x] > 0
                heights[i] = col.sum()

            total = int(heights.sum())
            if total > 0:
                cumsum = np.cumsum(heights)
                t1 = total / 3.0
                t2 = 2 * total / 3.0

                i1 = int(np.searchsorted(cumsum, t1))
                i2 = int(np.searchsorted(cumsum, t2))

                i1 = max(0, min(len(xs) - 1, i1))
                i2 = max(i1 + 1, min(len(xs) - 1, i2))

                x_b1_r = int(xs[i1])
                x_b2_r = int(xs[i2])

                # Dikey çizgiler
                for xb in [x_b1_r, x_b2_r]:
                    cv2.line(
                        vis,
                        (xb, y_top_r),
                        (xb, y_ust),
                        (255, 255, 255),
                        2,
                        lineType=cv2.LINE_AA
                    )

                # 3 bölgeyi renklendir
                boundaries_r = [x_start_r, x_b1_r, x_b2_r, x_end_r]
                colors = [(0,0,255), (0,255,0), (255,0,0)]
                alpha = 0.30

                for idx in range(3):
                    x1 = boundaries_r[idx]
                    x2 = boundaries_r[idx + 1]

                    overlay = vis.copy()
                    cv2.rectangle(
                        overlay,
                        (x1, y_top_r),
                        (x2, y_ust),
                        colors[idx],
                        -1
                    )
                    vis[:] = cv2.addWeighted(
                        overlay, alpha, vis, 1 - alpha, 0
                    )

                    cx = (x1 + x2) // 2
                    cy = (y_top_r + y_ust) // 2
                    cv2.putText(
                        vis,
                        str(idx + 1),
                        (cx - 5, cy),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )

    # ------------------------------------------------
    # 8) SOL ÜST BACAK HACMİNİ (UST_DIZ_L → person_kirmizi üst sınırı)
    #    3 EŞ ALANLI DİKİNE PARÇAYA BÖL
    # ------------------------------------------------
    if ust_diz_l is not None and GROIN is not None and person_kirmizi is not None:
        y_ust = int(ust_diz_l[1])
        gx = int(GROIN[0])

        H_p, W_p = person_kirmizi.shape

        # person_kirmizi maskesi yukarı doğru nerede bitiyor? (sol taraf)
        top_limit_l = None
        for yy in range(y_ust - 1, -1, -1):
            row = person_kirmizi[yy, :] > 0
            xs_all = np.where(row)[0]
            xs_left = xs_all[xs_all <= gx]
            if xs_left.size > 3:
                top_limit_l = yy
            else:
                break

        if top_limit_l is None:
            top_limit_l = max(0, y_ust - 80)

        y_top_l = int(top_limit_l)

        # UST_DIZ satırında sol bacak sınırları (person_kirmizi)
        row = person_kirmizi[y_ust, :] > 0
        xs_all = np.where(row)[0]
        xs_left = xs_all[xs_all <= gx]

        if xs_left.size > 3:
            x_start_l = int(xs_left[0])      # en sola yakın
            x_end_l   = int(xs_left[-1])     # kasığa en yakın

            xs = np.arange(x_start_l, x_end_l + 1)
            heights = np.zeros_like(xs, dtype=np.int64)

            for i, x in enumerate(xs):
                col = person_kirmizi[y_top_l:y_ust + 1, x] > 0
                heights[i] = col.sum()

            total = int(heights.sum())
            if total > 0:
                cumsum = np.cumsum(heights)
                t1 = total / 3.0
                t2 = 2 * total / 3.0

                i1 = int(np.searchsorted(cumsum, t1))
                i2 = int(np.searchsorted(cumsum, t2))

                i1 = max(0, min(len(xs) - 1, i1))
                i2 = max(i1 + 1, min(len(xs) - 1, i2))

                x_b1_l = int(xs[i1])
                x_b2_l = int(xs[i2])

                for xb in [x_b1_l, x_b2_l]:
                    cv2.line(
                        vis,
                        (xb, y_top_l),
                        (xb, y_ust),
                        (255, 255, 255),
                        2,
                        lineType=cv2.LINE_AA
                    )

                boundaries_l = [x_start_l, x_b1_l, x_b2_l, x_end_l]
                colors = [(0,0,255),(0,255,0),(255,0,0)]
                alpha = 0.30

                for idx in range(3):
                    x1 = boundaries_l[idx]
                    x2 = boundaries_l[idx + 1]

                    overlay = vis.copy()
                    cv2.rectangle(
                        overlay,
                        (x1, y_top_l),
                        (x2, y_ust),
                        colors[idx],
                        -1
                    )
                    vis[:] = cv2.addWeighted(
                        overlay, alpha, vis, 1 - alpha, 0
                    )

                    cx = (x1 + x2) // 2
                    cy = (y_top_l + y_ust) // 2
                    cv2.putText(
                        vis,
                        str(idx + 1),
                        (cx - 5, cy),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )

    # ------------------------------------------------
    # 9) PERSON MASKESİNİ AYRI BİR RESİM OLARAK KAYDET
    # ------------------------------------------------
    person_vis = np.zeros_like(vis)
    person_vis[person > 0] = (255, 255, 255)
    contours, _ = cv2.findContours(person, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(person_vis, contours, -1, (0, 0, 255), 2)
    cv2.imwrite("person_mask_only.png", person_vis)
    print("Kaydedildi: person_mask_only.png")

    # ------------------------------------------------
    # 10) TÜM ÇİZİMLERLE BİRLİKTE ANA GÖRÜNTÜYÜ KAYDET
    # ------------------------------------------------
    cv2.imwrite(OUT_VIS, vis)
    print("Kaydedildi:", OUT_VIS)

    if SHOW_WINDOW:
        cv2.imshow("Thermal Anatomik Noktalar", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
