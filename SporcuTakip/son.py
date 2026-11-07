# -*- coding: utf-8 -*-
import os, argparse, base64, json
import numpy as np
import cv2
from roboflow import Roboflow

# -------------------- Yardımcılar --------------------
def ensure_dir(d):
    os.makedirs(d, exist_ok=True)
    return d

def points_to_poly(pred):
    """
    Roboflow prediction -> polygon noktaları (N,2) float32
    'points' (list of dict), {'exterior': [...]}, 'polygon', 'segments' varyantlarını destekler.
    """
    pts = None
    if "points" in pred:
        pts = pred["points"]
        if isinstance(pts, dict) and "exterior" in pts:
            pts = pts["exterior"]
    elif "polygon" in pred:
        pts = pred["polygon"]
    elif "segments" in pred:
        pts = pred["segments"]
    if isinstance(pts, list) and len(pts) > 0:
        if isinstance(pts[0], dict) and "x" in pts[0] and "y" in pts[0]:
            arr = np.array([[float(p["x"]), float(p["y"])] for p in pts], dtype=np.float32)
            return arr
        if isinstance(pts[0], (list, tuple)) and len(pts[0]) == 2:
            return np.array(pts, dtype=np.float32)
    return None

def decode_bitmap_mask(pred):
    """
    'bitmap' alanını (PNG base64 veya ham) 0/255 maske olarak döndürür,
    ayrıca sol-üst yerleşim (left, top).
    """
    bm = pred.get("bitmap")
    if not bm or "data" not in bm:
        return None
    raw = base64.b64decode(bm["data"])
    arr = np.frombuffer(raw, dtype=np.uint8)
    small = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if small is None:
        try:
            small = np.frombuffer(raw, dtype=np.uint8).reshape(int(bm["height"]), int(bm["width"])) * 255
        except Exception:
            return None
    _, small = cv2.threshold(small, 127, 255, cv2.THRESH_BINARY)
    left, top = int(bm.get("left", 0)), int(bm.get("top", 0))
    return small, left, top

def order_quad(quad):
    """
    4 noktalı çokgeni TL,TR,BR,BL sırasına sok.
    """
    pts = quad.astype(np.float32)
    # en üst iki, en alt iki
    idx = np.argsort(pts[:, 1], kind='mergesort')
    top2, bot2 = pts[idx[:2]], pts[idx[2:]]
    TL, TR = (top2[0], top2[1]) if top2[0, 0] <= top2[1, 0] else (top2[1], top2[0])
    BL, BR = (bot2[0], bot2[1]) if bot2[0, 0] <= bot2[1, 0] else (bot2[1], bot2[0])
    return np.array([TL, TR, BR, BL], dtype=np.float32)

def quad_from_mask_or_polys(mask, poly_list, img_shape):
    """
    Birleşik maske veya poligonlardan dış sınırın 4 köşesini bul.
    Önce poligonları birleştirip dışbükey kılıf (convex hull), sonra approxPolyDP (4'e indirgeme),
    olmadı minAreaRect kutusu.
    """
    H, W = img_shape[:2]

    # 1) Poligonlardan birleşik nokta kümesi
    all_pts = []
    for poly in poly_list:
        if poly is not None and len(poly) >= 3:
            all_pts.append(poly.reshape(-1, 2))
    if len(all_pts) > 0:
        pts = np.vstack(all_pts).astype(np.float32)
        hull = cv2.convexHull(pts)
        peri = cv2.arcLength(hull, True)
        # Epsilon'ı görüntü boyutuna göre ayarla
        eps = max(4.0, 0.02 * peri)
        approx = cv2.approxPolyDP(hull, eps, True).reshape(-1, 2)
        if approx.shape[0] == 4:
            return order_quad(approx)

    # 2) Maske üzerinden en büyük kontur
    if mask is not None and np.count_nonzero(mask) > 0:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts):
            cnt = max(cnts, key=cv2.contourArea)
            peri = cv2.arcLength(cnt, True)
            for frac in [0.02, 0.03, 0.04, 0.05, 0.07, 0.1]:
                eps = max(4.0, frac * peri)
                approx = cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2)
                if approx.shape[0] == 4:
                    return order_quad(approx)

            # 3) Yine 4 elde edemezsek minAreaRect kutusunu al
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)  # 4x2 float
            return order_quad(box)

    return None  # bulunamadı

# -------------------- Ana akış --------------------
def main(img_path, out_dir, api_key=os.environ.get("ROBOFLOW_API_KEY", ""),
         project="tenniscourtsegmentation", version=5, confidence=40):

    ensure_dir(out_dir)

    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(img_path)
    H, W = img.shape[:2]

    rf = Roboflow(api_key=api_key)
    model = rf.workspace().project(project).version(version).model

    print("[INFO] Roboflow’a istek gönderiliyor...")
    result = model.predict(img_path, confidence=confidence).json()

    # Ham JSON
    with open(os.path.join(out_dir, "roboflow_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    overlay = img.copy()
    union_mask = np.zeros((H, W), dtype=np.uint8)
    polys = []

    # 1) predictions parse: polygon -> mask; bitmap -> mask; bbox fallback
    preds = result.get("predictions", [])
    for pred in preds:
        poly = points_to_poly(pred)
        if poly is not None and len(poly) >= 3:
            polys.append(poly)
            cv2.fillPoly(union_mask, [poly.astype(np.int32)], 255)
            continue

        bm = decode_bitmap_mask(pred)
        if bm is not None:
            small, left, top = bm
            h, w = small.shape[:2]
            x1, y1 = max(0, left), max(0, top)
            x2, y2 = min(W, left + w), min(H, top + h)
            roiW, roiH = x2 - x1, y2 - y1
            if roiW > 0 and roiH > 0:
                union_mask[y1:y2, x1:x2] = np.maximum(union_mask[y1:y2, x1:x2], small[0:roiH, 0:roiW])
            continue

        if all(k in pred for k in ("x", "y", "width", "height")):
            cx, cy = float(pred["x"]), float(pred["y"])
            bw, bh = float(pred["width"]), float(pred["height"])
            x1 = int(round(cx - bw/2)); y1 = int(round(cy - bh/2))
            x2 = int(round(cx + bw/2)); y2 = int(round(cy + bh/2))
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(W-1, x2), min(H-1, y2)
            cv2.rectangle(union_mask, (x1, y1), (x2, y2), 255, -1)

    # 2) 4 köşeyi çıkar
    quad = quad_from_mask_or_polys(union_mask, polys, img.shape)  # TL, TR, BR, BL veya None

    # 3) Annotated görüntü (maske + poligon + 4 nokta)
    # Maske bindirme
    color_mask = cv2.cvtColor(union_mask, cv2.COLOR_GRAY2BGR)
    color_mask[:, :, 1] = np.maximum(color_mask[:, :, 1], union_mask)  # yeşil kanal
    annotated = cv2.addWeighted(overlay, 0.7, color_mask, 0.3, 0)

    # Poligonları çiz (varsa)
    for poly in polys:
        cv2.polylines(annotated, [poly.astype(np.int32)], True, (0, 255, 0), 2)

    # 4) 4 köşeyi işaretle ve yaz
    corners_json = {}
    if quad is not None:
        q = quad.astype(int)
        names = ["TL", "TR", "BR", "BL"]
        # dış dörtgeni çizgilerle göster
        cv2.polylines(annotated, [q], True, (0, 0, 255), 2)
        for name, (x, y) in zip(names, q):
            cv2.circle(annotated, (int(x), int(y)), 8, (0, 255, 255), -1)
            cv2.putText(annotated, name, (int(x)+6, int(y)-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            corners_json[name] = [float(quad[names.index(name), 0]), float(quad[names.index(name), 1])]
    else:
        print("[WARN] 4 köşe güvenli şekilde çıkarılamadı; corners.json boş yazılacak.")

    # 5) Kaydet
    cv2.imwrite(os.path.join(out_dir, "mask.png"), union_mask)
    cv2.imwrite(os.path.join(out_dir, "annotated.png"), annotated)
    with open(os.path.join(out_dir, "corners.json"), "w", encoding="utf-8") as f:
        json.dump(corners_json, f, indent=2)
    print("[OK] Kaydedildi:\n -", os.path.join(out_dir, "annotated.png"),
          "\n -", os.path.join(out_dir, "mask.png"),
          "\n -", os.path.join(out_dir, "corners.json"))

# -------------------- CLI --------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True, help="girdi görseli")
    ap.add_argument("--out", default="results", help="çıktı klasörü")
    ap.add_argument("--api_key", default=os.environ.get("ROBOFLOW_API_KEY", ""))
    ap.add_argument("--project", default="tenniscourtsegmentation")
    ap.add_argument("--version", type=int, default=5)
    ap.add_argument("--confidence", type=int, default=40)
    args = ap.parse_args()
    main(args.img, args.out, args.api_key, args.project, args.version, args.confidence)
