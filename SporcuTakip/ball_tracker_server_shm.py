import time
import socket
import struct
import numpy as np
import cv2
from ultralytics import YOLO
from multiprocessing.shared_memory import SharedMemory

# ===== Shared memory params =====
MMF_NAME = r"Global\SPORCU_FRAME_MMF_V1"
HEADER_SIZE = 64
MAGIC = 0x46524D45
VERSION = 1

# ===== TCP target (C# listener port ile aynı olmalı) =====
HOST = "127.0.0.1"
PORT = 5056   # <-- C# BallTrackerPort neyse aynısı

# ===== Detection / Tracking Config =====
MODEL_PATH = "yolov8n.pt"
CONF = 0.20
YOLO_IMGSZ = 640
REDETECT_INTERVAL = 10
MAX_MISSES = 10

def create_tracker():
    if hasattr(cv2, "legacy") and hasattr(cv2.legacy, "TrackerCSRT_create"):
        return cv2.legacy.TrackerCSRT_create()
    return cv2.TrackerCSRT_create()

def clamp_xyxy(x1, y1, x2, y2, W, H):
    x1 = max(0, min(W - 1, int(x1)))
    y1 = max(0, min(H - 1, int(y1)))
    x2 = max(0, min(W - 1, int(x2)))
    y2 = max(0, min(H - 1, int(y2)))
    if x2 <= x1 + 1 or y2 <= y1 + 1:
        return None
    return (x1, y1, x2, y2)

def connect_sender():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        s.connect((HOST, PORT))
        return s
    except:
        try: s.close()
        except: pass
        return None

def send_ball(sock, frame_id, found, x=None, y=None, w=0, h=0):
    if sock is None:
        return
    if not found:
        line = f'{{"type":"ball","frame":{frame_id},"found":false}}\n'
    else:
        line = f'{{"type":"ball","frame":{frame_id},"found":true,"x":{x},"y":{y},"w":{w},"h":{h}}}\n'
    try:
        sock.sendall(line.encode("utf-8"))
    except:
        pass

def read_header_from_buf(buf):
    header = buf[:HEADER_SIZE]
    magic, ver = struct.unpack_from("<II", header, 0)
    if magic != MAGIC or ver != VERSION:
        return None
    w, h, stride, ch, fmt, frame_id = struct.unpack_from("<iiiiii", header, 8)
    ticks = struct.unpack_from("<q", header, 32)[0]
    data_bytes, ready = struct.unpack_from("<ii", header, 40)
    return w, h, stride, ch, fmt, frame_id, ticks, data_bytes, ready

def main():
    print("[PY] Loading YOLO:", MODEL_PATH)
    model = YOLO(MODEL_PATH)

    # "sports ball" class id
    ball_id = None
    for k, v in model.names.items():
        if v == "sports ball":
            ball_id = k
            break
    if ball_id is None:
        print("[PY] WARNING: sports ball sınıfı bulunamadı. classes filtresi kapatılacak.")
    
    # Shared memory connect
    shm = None
    while shm is None:
        try:
            shm = SharedMemory(name=MMF_NAME)
            print("[PY] Connected to MMF:", MMF_NAME)
        except FileNotFoundError:
            print("[PY] Waiting for C# MMF...")
            time.sleep(0.5)

    sock = None
    tracker = None
    tracking = False
    misses = 0
    frames_since_detect = 0

    last_frame_id = -1

    try:
        while True:
            hdr = read_header_from_buf(shm.buf)
            if hdr is None:
                time.sleep(0.005)
                continue

            w, h, stride, ch, fmt, frame_id, ticks, data_bytes, ready = hdr

            if ready != 1 or w <= 0 or h <= 0 or data_bytes <= 0:
                time.sleep(0.001)
                continue

            if frame_id == last_frame_id:
                time.sleep(0.001)
                continue
            last_frame_id = frame_id

            # MMF pixel data
            pixel_buf = shm.buf[HEADER_SIZE:HEADER_SIZE + data_bytes]

            # stride bytes -> row_pixels = stride/4
            row_pixels = stride // 4
            if row_pixels <= 0:
                continue

            # C# Format=1 => BGRA
            # (h, row_pixels, 4) oluştur -> sonra w'e kadar crop
            img_bgra = np.ndarray((h, row_pixels, 4), dtype=np.uint8, buffer=pixel_buf)
            img_bgra = img_bgra[:, :w, :]

            # ✅ doğru dönüşüm: BGRA -> BGR
            frame = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)

            box_xyxy = None
            do_detection = (not tracking) or (frames_since_detect >= REDETECT_INTERVAL)

            if do_detection:
                # YOLO
                if ball_id is None:
                    results = model.predict(frame, conf=CONF, imgsz=YOLO_IMGSZ, verbose=False)
                else:
                    results = model.predict(frame, conf=CONF, classes=[ball_id], imgsz=YOLO_IMGSZ, verbose=False)

                best_box, best_conf = None, -1.0
                if results and results[0].boxes is not None and len(results[0].boxes) > 0:
                    for b in results[0].boxes:
                        x1, y1, x2, y2 = map(float, b.xyxy[0])
                        cf = float(b.conf[0])
                        cand = clamp_xyxy(x1, y1, x2, y2, w, h)
                        if cand and cf > best_conf:
                            best_conf = cf
                            best_box = cand

                if best_box is not None:
                    x1, y1, x2, y2 = best_box
                    roi = (x1, y1, x2 - x1, y2 - y1)

                    tracker = create_tracker()
                    tracker.init(frame, roi)
                    tracking = True
                    misses = 0
                    frames_since_detect = 0
                    box_xyxy = best_box
                else:
                    # bulunamadı
                    if tracking:
                        # takip varsa tracker ile devam etmeye çalış
                        frames_since_detect = 0
                    else:
                        box_xyxy = None
            else:
                # TRACKER
                if tracker is not None:
                    ok, bbox = tracker.update(frame)
                    if ok:
                        tx, ty, tw, th = bbox
                        cand = clamp_xyxy(tx, ty, tx + tw, ty + th, w, h)
                        if cand:
                            box_xyxy = cand
                            misses = 0
                        else:
                            misses += 1
                    else:
                        misses += 1

                    frames_since_detect += 1

                    if misses >= MAX_MISSES:
                        tracking = False
                        tracker = None
                        misses = 0

            # TCP connect retry
            if sock is None:
                sock = connect_sender()

            # SEND
            if box_xyxy is None:
                send_ball(sock, frame_id, found=False)
            else:
                x1, y1, x2, y2 = box_xyxy
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                bw, bh = int(x2 - x1), int(y2 - y1)
                send_ball(sock, frame_id, found=True, x=cx, y=cy, w=bw, h=bh)

    except KeyboardInterrupt:
        print("[PY] stopping...")
    finally:
        try:
            if sock: sock.close()
        except: pass
        try:
            if shm: shm.close()
        except: pass

if __name__ == "__main__":
    main()
