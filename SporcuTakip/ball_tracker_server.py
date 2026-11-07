# ball_tracker_server.py
import argparse
import json
import os
import socket
import threading
import time

import cv2
import numpy as np
from ultralytics import YOLO

# ----------------------------
# Defaults (senin ayarlara yakın)
# ----------------------------
MODEL_PATH = "yolov8m.pt"
CONF = 0.12
YOLO_IMGSZ = 960

MAX_MISSES = 8

# Template verify (CSRT içinde)
TM_METHOD = cv2.TM_CCOEFF_NORMED
TM_VERIFY_EVERY = 10
TM_VERIFY_THRESH = 0.50
ROI_PAD = 10
TEMPLATE_MIN_SIZE = 12

# YOLO false positive azaltma (kutucuk/afiş vb)
MIN_BOX = 6
MAX_BOX_AREA_RATIO = 0.08
ASPECT_MIN, ASPECT_MAX = 0.6, 1.7

# Daire doğrulama
CIRCLE_VERIFY = True
CIRCLE_MIN_SCORE = 0.22
CIRCLE_DP = 1.2
CIRCLE_PARAM1 = 120
CIRCLE_PARAM2 = 18

# Sabit nesne (poster) kontrolü
STATIC_CHECK_FRAMES = 100
STATIC_MOVE_THRESH = 6

# YOLO verify (tracker yanlışsa)
YOLO_VERIFY_EVERY = 10
YOLO_VERIFY_IMGSZ = 512
YOLO_NOTBALL_LIMIT = 3

# Reacquire (template search)
TM_SEARCH_DOWNSCALE = 0.6
TM_SEARCH_THRESH = 0.62


def create_csrt():
    if hasattr(cv2, "legacy") and hasattr(cv2.legacy, "TrackerCSRT_create"):
        return cv2.legacy.TrackerCSRT_create()
    if hasattr(cv2, "TrackerCSRT_create"):
        return cv2.TrackerCSRT_create()
    raise RuntimeError("CSRT tracker yok. opencv-contrib-python kurmanız gerekebilir.")


def clamp_box(frame, box_xyxy):
    H, W = frame.shape[:2]
    x1, y1, x2, y2 = box_xyxy
    x1 = max(0, min(W - 1, int(x1)))
    y1 = max(0, min(H - 1, int(y1)))
    x2 = max(0, min(W - 1, int(x2)))
    y2 = max(0, min(H - 1, int(y2)))
    if x2 <= x1 + 1 or y2 <= y1 + 1:
        return None
    return (x1, y1, x2, y2)


def has_circle_like(gray_roi):
    rh, rw = gray_roi.shape[:2]
    if rh < 14 or rw < 14:
        return False

    g = cv2.GaussianBlur(gray_roi, (5, 5), 0)

    rmin = max(3, int(min(rh, rw) * 0.18))
    rmax = max(rmin + 1, int(min(rh, rw) * 0.55))

    circles = cv2.HoughCircles(
        g,
        cv2.HOUGH_GRADIENT,
        dp=CIRCLE_DP,
        minDist=max(8, min(rh, rw) // 3),
        param1=CIRCLE_PARAM1,
        param2=CIRCLE_PARAM2,
        minRadius=rmin,
        maxRadius=rmax
    )
    return circles is not None and len(circles) > 0


def ball_gate(frame, box_xyxy, conf_score):
    box_xyxy = clamp_box(frame, box_xyxy)
    if box_xyxy is None:
        return False

    x1, y1, x2, y2 = box_xyxy
    bw = x2 - x1
    bh = y2 - y1

    if bw < MIN_BOX or bh < MIN_BOX:
        return False

    aspect = bw / float(bh + 1e-6)
    if aspect < ASPECT_MIN or aspect > ASPECT_MAX:
        return False

    H, W = frame.shape[:2]
    area_ratio = (bw * bh) / float(H * W + 1e-6)
    if area_ratio > MAX_BOX_AREA_RATIO:
        return False

    if CIRCLE_VERIFY:
        gray_roi = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        circle_ok = has_circle_like(gray_roi)
        if conf_score < CIRCLE_MIN_SCORE and not circle_ok:
            return False

    return True


class StaticRejector:
    def __init__(self):
        self.positions = []
        self.reject_counter = 0

    def reset(self):
        self.positions.clear()

    def is_static(self, box_xyxy):
        x1, y1, x2, y2 = box_xyxy
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        self.positions.append((cx, cy))
        if len(self.positions) > STATIC_CHECK_FRAMES:
            self.positions.pop(0)

        if len(self.positions) < STATIC_CHECK_FRAMES:
            return False

        xs = [p[0] for p in self.positions]
        ys = [p[1] for p in self.positions]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)

        if dx < STATIC_MOVE_THRESH and dy < STATIC_MOVE_THRESH:
            self.reject_counter += 1
            return True
        return False


class BallTracker:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

        self.ball_class_id = None
        for k, v in self.model.names.items():
            if v == "sports ball":
                self.ball_class_id = k
                break
        if self.ball_class_id is None:
            raise RuntimeError("'sports ball' sınıfı bulunamadı (YOLO names içinde yok)")

        self.tracker = None
        self.tracking = False
        self.misses = 0

        self.last_box_xyxy = None
        self.last_conf = 0.0

        self.ball_template = None
        self.force_reacquire = False

        self.yolo_notball_count = 0
        self.static_rej = StaticRejector()

        self.frame_idx = -1

    def update_template_from_box(self, frame, box_xyxy):
        box_xyxy = clamp_box(frame, box_xyxy)
        if box_xyxy is None:
            return

        x1, y1, x2, y2 = box_xyxy
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return
        h, w = crop.shape[:2]
        if h < TEMPLATE_MIN_SIZE or w < TEMPLATE_MIN_SIZE:
            return

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        self.ball_template = gray

    def tm_verify_inside_roi(self, frame, box_xyxy):
        if self.ball_template is None:
            return True, 1.0

        box_xyxy = clamp_box(frame, box_xyxy)
        if box_xyxy is None:
            return False, 0.0

        x1, y1, x2, y2 = box_xyxy
        H, W = frame.shape[:2]

        x1p = max(0, x1 - ROI_PAD)
        y1p = max(0, y1 - ROI_PAD)
        x2p = min(W - 1, x2 + ROI_PAD)
        y2p = min(H - 1, y2 + ROI_PAD)

        roi = frame[y1p:y2p, x1p:x2p]
        if roi.size == 0:
            return False, 0.0

        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        roi_gray = cv2.GaussianBlur(roi_gray, (3, 3), 0)

        th, tw = self.ball_template.shape[:2]
        rh, rw = roi_gray.shape[:2]
        if th >= rh or tw >= rw:
            return False, 0.0

        res = cv2.matchTemplate(roi_gray, self.ball_template, TM_METHOD)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return (max_val >= TM_VERIFY_THRESH), float(max_val)

    def yolo_verify_on_roi(self, frame, box_xyxy):
        box_xyxy = clamp_box(frame, box_xyxy)
        if box_xyxy is None:
            return False, 0.0

        x1, y1, x2, y2 = box_xyxy
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False, 0.0

        results = self.model.predict(
            roi,
            conf=CONF,
            classes=[self.ball_class_id],
            imgsz=YOLO_VERIFY_IMGSZ,
            verbose=False
        )
        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return False, 0.0

        bestc = 0.0
        for b in r.boxes:
            c = float(b.conf[0])
            if c > bestc:
                bestc = c
        return True, bestc

    def tm_search_fullframe(self, frame):
        if self.ball_template is None:
            return None, 0.0

        f = frame
        s = TM_SEARCH_DOWNSCALE
        if s != 1.0:
            f = cv2.resize(frame, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        templ = self.ball_template
        th, tw = templ.shape[:2]
        gh, gw = gray.shape[:2]
        if th >= gh or tw >= gw:
            return None, 0.0

        res = cv2.matchTemplate(gray, templ, TM_METHOD)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val < TM_SEARCH_THRESH:
            return None, float(max_val)

        x, y = max_loc
        x1 = int(x / s)
        y1 = int(y / s)
        x2 = int((x + tw) / s)
        y2 = int((y + th) / s)

        box = clamp_box(frame, (x1, y1, x2, y2))
        return box, float(max_val)

    def yolo_find_ball(self, frame):
        results = self.model.predict(
            frame,
            conf=CONF,
            classes=[self.ball_class_id],
            imgsz=YOLO_IMGSZ,
            verbose=False
        )
        r = results[0]
        if r.boxes is None:
            return None, 0.0

        best = None
        best_conf = -1.0

        for b in r.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0])
            c = float(b.conf[0])

            if (x2 - x1) < 6 or (y2 - y1) < 6:
                continue

            cand = (x1, y1, x2, y2)

            if not ball_gate(frame, cand, c):
                continue

            if self.static_rej.is_static(cand):
                continue

            if c > best_conf:
                best_conf = c
                best = cand

        return best, best_conf

    def _init_tracker(self, frame, box_xyxy):
        x1, y1, x2, y2 = box_xyxy
        roi = (x1, y1, x2 - x1, y2 - y1)

        self.tracker = create_csrt()
        ok = self.tracker.init(frame, roi)

        self.tracking = bool(ok)
        self.misses = 0
        self.force_reacquire = False
        self.yolo_notball_count = 0

        return self.tracking

    def step(self, frame, frame_idx: int):
        """
        Bir wrap png frame geldiğinde çalışır.
        Return: (found, x,y,w,h, score)
        """
        self.frame_idx = frame_idx

        if frame is None or frame.size == 0:
            self.tracking = False
            self.tracker = None
            return (False, None, None, None, None, 0.0)

        if self.tracking and self.tracker is not None:
            ok_tr, box = self.tracker.update(frame)
            if ok_tr:
                self.misses = 0
                x, y, w, h = map(int, box)
                self.last_box_xyxy = clamp_box(frame, (x, y, x + w, y + h))
                if self.last_box_xyxy is None:
                    self.misses += 1
            else:
                self.misses += 1

            if self.misses >= MAX_MISSES:
                self.tracking = False
                self.tracker = None
                self.force_reacquire = False
                self.yolo_notball_count = 0

        # doğrulama
        if self.tracking and self.last_box_xyxy is not None:
            if (frame_idx % TM_VERIFY_EVERY == 0):
                ok_tm, tm_score = self.tm_verify_inside_roi(frame, self.last_box_xyxy)
                self.last_conf = tm_score

                ok_yv, yv_conf = self.yolo_verify_on_roi(frame, self.last_box_xyxy)

                if not ok_yv:
                    self.yolo_notball_count += 1
                else:
                    self.yolo_notball_count = 0

                if self.yolo_notball_count >= YOLO_NOTBALL_LIMIT:
                    self.tracking = False
                    self.tracker = None
                    self.force_reacquire = True
                    self.yolo_notball_count = 0

        # reacquire modu
        if not self.tracking:
            if self.force_reacquire:
                tm_box, tm_sc = self.tm_search_fullframe(frame)
                if tm_box is not None:
                    ok_yv, _ = self.yolo_verify_on_roi(frame, tm_box)
                    if ok_yv:
                        self.static_rej.reset()
                        self.last_box_xyxy = tm_box
                        self.last_conf = tm_sc
                        self.update_template_from_box(frame, tm_box)
                        self._init_tracker(frame, tm_box)
                        # başarı
                        self.force_reacquire = False
                    else:
                        self.force_reacquire = False
                else:
                    self.force_reacquire = False

        # normal arama
        if not self.tracking:
            best, best_conf = self.yolo_find_ball(frame)
            if best is not None:
                best = clamp_box(frame, best)
                if best is not None:
                    self.static_rej.reset()
                    self.last_box_xyxy = best
                    self.last_conf = best_conf
                    self.update_template_from_box(frame, best)
                    self._init_tracker(frame, best)

        if self.last_box_xyxy is None:
            return (False, None, None, None, None, 0.0)

        x1, y1, x2, y2 = self.last_box_xyxy
        cx = int((x1 + x2) * 0.5)
        cy = int((y1 + y2) * 0.5)
        w = int(x2 - x1)
        h = int(y2 - y1)
        return (True, cx, cy, w, h, float(self.last_conf))


# ----------------------------
# TCP server
# ----------------------------
def parse_hostport(s: str):
    if ":" not in s:
        return s, 5056
    host, port = s.rsplit(":", 1)
    return host, int(port)


def send_line(sock: socket.socket, obj: dict):
    data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
    sock.sendall(data)


def recv_lines(sock: socket.socket):
    buf = b""
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            yield line.decode("utf-8", errors="ignore")


def imread_any(path: str):
    if not os.path.exists(path):
        return None
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    return img


def handle_client(conn: socket.socket, addr, tracker: BallTracker):
    try:
        for line in recv_lines(conn):
            try:
                msg = json.loads(line)
            except:
                continue

            t = msg.get("type", "")
            if t == "quit":
                send_line(conn, {"type": "bye"})
                break

            if t != "frame":
                continue

            frame_idx = int(msg.get("frame", -1))
            path = msg.get("path", "")

            frame = imread_any(path)

            found, x, y, w, h, score = tracker.step(frame, frame_idx)

            if found:
                send_line(conn, {
                    "type": "ball",
                    "found": True,
                    "frame": frame_idx,
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h),
                    "score": float(score)
                })
            else:
                send_line(conn, {
                    "type": "ball",
                    "found": False,
                    "frame": frame_idx
                })
    finally:
        try:
            conn.close()
        except:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", default="127.0.0.1:5056", help="host:port")
    ap.add_argument("--model", default=MODEL_PATH, help="YOLO model path, e.g. yolov8s.pt")
    args = ap.parse_args()

    host, port = parse_hostport(args.listen)

    tracker = BallTracker(args.model)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)

    print(f"[ball_tracker_server] listening on {host}:{port}")
    while True:
        conn, addr = srv.accept()
        print(f"[ball_tracker_server] client connected: {addr}")
        # Her bağlantı için yeni tracker istersen: BallTracker(args.model)
        # Şimdilik tek tracker (devamlı takip) kullanıyoruz.
        try:
            handle_client(conn, addr, tracker)
        except Exception as e:
            try:
                send_line(conn, {"type": "error", "message": str(e)})
            except:
                pass
        print(f"[ball_tracker_server] client closed: {addr}")


if __name__ == "__main__":
    main()
