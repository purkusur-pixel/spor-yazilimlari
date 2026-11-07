# -*- coding: utf-8 -*-
"""
soccer_diagrammer.py (v1.1.1)
- Serbest kesikli çizgi (f) aracı
- Otomatik #numaralandırma
- ttk.Label pack() foreground düzeltmesi
"""

import math
import json
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, simpledialog, messagebox
from PIL import Image, ImageDraw, ImageFont

APP_TITLE = "Soccer Diagrammer"
W, H = 1100, 700
UNDO_LIMIT = 60

def clamp(v, a, b):
    return max(a, min(b, v))

def rotate_point(x, y, cx, cy, deg):
    rad = math.radians(deg)
    s, c = math.sin(rad), math.cos(rad)
    x -= cx; y -= cy
    xr = x * c - y * s
    yr = x * s + y * c
    return xr + cx, yr + cy

TEAM_COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2", "#17becf"]

class BaseObj:
    def __init__(self, kind, x, y, w=40, h=40, color="#1f77b4", rot=0, extra=None):
        self.kind = kind
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.rot = rot
        self.extra = extra or {}

    def bbox(self):
        return (self.x - self.w/2, self.y - self.h/2, self.x + self.w/2, self.y + self.h/2)

    def contains(self, px, py):
        x0,y0,x1,y1 = self.bbox()
        return x0 <= px <= x1 and y0 <= py <= y1

    def to_dict(self):
        return {"kind": self.kind, "x": self.x, "y": self.y, "w": self.w, "h": self.h,
                "color": self.color, "rot": self.rot, "extra": self.extra}

    @staticmethod
    def from_dict(d):
        return BaseObj(d["kind"], d["x"], d["y"], d.get("w",40), d.get("h",40),
                       d.get("color","#1f77b4"), d.get("rot",0), d.get("extra",{}))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{W+260}x{H+80}")
        self.minsize(900, 600)

        self.objects = []
        self.selected = None
        self.tool = tk.StringVar(value="move")
        self.cur_color = "#1f77b4"
        self.alt_color = "#d62728"
        self.overlay_is_oval = False
        self.drag_offset = (0,0)
        self.is_dragging = False
        self.start_line = None
        self.current_file = None
        self.undo_stack = []
        self.redo_stack = []
        self.pitch = tk.BooleanVar(value=True)

        # NEW
        self.seq = 1
        self.temp_path_points = None
        self.preview_item = None

        self._build_menu()
        self._build_sidebar()
        self._build_canvas()
        self._bind_keys()
        self._push_undo()
        self._draw_all()

    def _build_menu(self):
        menubar = tk.Menu(self); self.config(menu=menubar)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="New", command=self.new)
        filem.add_command(label="Open (.json)", command=self.open_json)
        filem.add_command(label="Save (.json)", command=self.save_json)
        filem.add_separator()
        filem.add_command(label="Export PNG", command=self.export_png)
        filem.add_command(label="Export PDF", command=self.export_pdf)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filem)

        editm = tk.Menu(menubar, tearoff=0)
        editm.add_command(label="Undo (z)", command=self.undo)
        editm.add_command(label="Redo (y)", command=self.redo)
        menubar.add_cascade(label="Edit", menu=editm)

        viewm = tk.Menu(menubar, tearoff=0)
        viewm.add_checkbutton(label="Show Pitch", variable=self.pitch, command=self._draw_all)
        menubar.add_cascade(label="View", menu=viewm)

        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(label="Shortcuts", command=self._show_shortcuts)
        menubar.add_cascade(label="Help", menu=helpm)

    def _build_sidebar(self):
        side = ttk.Frame(self); side.pack(side="left", fill="y")
        ttk.Label(side, text="Araçlar", font=("Segoe UI", 10, "bold")).pack(padx=8, pady=(10,4))
        tools = [
            ("Taşı (m)", "move"),
            ("Oyuncu", "player"),
            ("Top", "ball"),
            ("Koni", "cone"),
            ("Kale", "goal"),
            ("Ok/Çizgi (l)", "line"),
            ("Serbest Kesikli Çizgi (f)", "free_dashed"),
            ("Metin (t)", "text"),
            ("Vurgu/Overlay (o)", "overlay"),
        ]
        for lbl, val in tools:
            ttk.Radiobutton(side, text=lbl, value=val, variable=self.tool).pack(anchor="w", padx=10)

        ttk.Separator(side).pack(fill="x", padx=8, pady=8)
        ttk.Label(side, text="Renk").pack(padx=8, pady=(0,4))
        row = ttk.Frame(side); row.pack(fill="x", padx=8)
        ttk.Button(row, text="Seç...", command=self.choose_color).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="Değiştir (p)", command=self.cycle_color).pack(side="left", expand=True, fill="x")
        ttk.Label(side, text="Boyut + / -").pack(padx=8, pady=(8,0))
        ttk.Label(side, text="Döndür (r)").pack(padx=8, pady=(0,8))
        ttk.Separator(side).pack(fill="x", padx=8, pady=8)
        ttk.Label(side, text="İpuçları").pack(padx=8, pady=(0,4))
        tips = ("Seçmek için tıkla, taşımak için sürükle.\n"
                "Çizgi/ok için başlangıç ve bitişe tıkla.\n"
                "Serbest kesikli çizgi için basılı tutup çiz.\n"
                "Overlay için sürükleyerek alan oluştur.\n"
                "Silmek için d, büyüt/küçült için +/-.")
        lbl_tips = ttk.Label(side, text=tips)
        lbl_tips.pack(padx=8)
        try:
            lbl_tips.configure(foreground="#555")
        except tk.TclError:
            # ttk tema izin vermezse sorun olmasın
            pass
        ttk.Separator(side).pack(fill="x", padx=8, pady=8)
        ttk.Button(side, text="Geri Al (z)", command=self.undo).pack(fill="x", padx=8, pady=2)
        ttk.Button(side, text="İleri Al (y)", command=self.redo).pack(fill="x", padx=8, pady=2)
        ttk.Button(side, text="PNG Dışa Aktar", command=self.export_png).pack(fill="x", padx=8, pady=6)

    def _build_canvas(self):
        self.wrap = ttk.Frame(self); self.wrap.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.wrap, bg="#e9ecef", width=W, height=H, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def _bind_keys(self):
        self.bind("m", lambda e: self.tool.set("move"))
        self.bind("l", lambda e: self.tool.set("line"))
        self.bind("t", lambda e: self.tool.set("text"))
        self.bind("o", lambda e: self.toggle_overlay_tool())
        self.bind("p", lambda e: self.cycle_color())
        self.bind("r", lambda e: self.rotate_selected(30))
        self.bind("+", lambda e: self.scale_selected(1.1))
        self.bind("-", lambda e: self.scale_selected(0.9))
        self.bind("d", lambda e: self.delete_selected())
        self.bind("z", lambda e: self.undo())
        self.bind("y", lambda e: self.redo())
        self.bind("f", lambda e: self.tool.set("free_dashed"))

    def _draw_all(self):
        self.canvas.delete("all")
        if self.pitch.get():
            self._draw_pitch()
        for i, obj in enumerate(self.objects):
            self._draw_obj(i, obj)
        if self.selected is not None and 0 <= self.selected < len(self.objects):
            self._draw_selection(self.objects[self.selected])

    def _draw_pitch(self):
        pad = 30
        x0, y0 = pad, pad
        x1, y1 = W - pad, H - pad

        # Zemin
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="#77b255", outline="#3d7a3b")

        # Merkez koordinatları
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2

        # Orta çizgi
        self.canvas.create_line(cx, y0, cx, y1, width=2, fill="#ffffff")

        # Orta daire (HATA DÜZELTİLDİ)
        self.canvas.create_oval(cx-60, cy-60, cx+60, cy+60, outline="#ffffff", width=2)

        # UFACIK EK 1: Orta nokta
        self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#ffffff", outline="")

        # Ceza alanları
        box_w, box_h = 160, 300
        self.canvas.create_rectangle(x0, cy-box_h/2, x0+box_w, cy+box_h/2, outline="#ffffff", width=2)
        self.canvas.create_rectangle(x1-box_w, cy-box_h/2, x1, cy+box_h/2, outline="#ffffff", width=2)

        # Kale alanları
        g_w, g_h = 60, 180
        self.canvas.create_rectangle(x0, cy-g_h/2, x0+g_w, cy+g_h/2, outline="#ffffff", width=2)
        self.canvas.create_rectangle(x1-g_w, cy-g_h/2, x1, cy+g_h/2, outline="#ffffff", width=2)

        # Penaltı noktaları
        self.canvas.create_oval(x0+110-3, cy-3, x0+110+3, cy+3, fill="#ffffff", outline="")
        self.canvas.create_oval(x1-110-3, cy-3, x1-110+3, cy+3, fill="#ffffff", outline="")

        # UFACIK EK 2: Köşe yayları
        cr = 12  # köşe yayı yarıçapı
        # Sol üst
        self.canvas.create_arc(x0, y0, x0+2*cr, y0+2*cr, start=0, extent=90, style="arc", outline="#ffffff", width=2)
        # Sağ üst
        self.canvas.create_arc(x1-2*cr, y0, x1, y0+2*cr, start=90, extent=90, style="arc", outline="#ffffff", width=2)
        # Sağ alt
        self.canvas.create_arc(x1-2*cr, y1-2*cr, x1, y1, start=180, extent=90, style="arc", outline="#ffffff", width=2)
        # Sol alt
        self.canvas.create_arc(x0, y1-2*cr, x0+2*cr, y1, start=270, extent=90, style="arc", outline="#ffffff", width=2)


    def _draw_selection(self, obj):
        x0,y0,x1,y1 = obj.bbox()
        self.canvas.create_rectangle(x0, y0, x1, y1, outline="#ffeb3b", width=2, dash=(4,3))

    def _draw_obj(self, idx, obj):
        k = obj.kind
        if k == "player":
            self._draw_player(obj)
        elif k == "ball":
            self._draw_ball(obj)
        elif k == "cone":
            self._draw_cone(obj)
        elif k == "goal":
            self._draw_goal(obj)
        elif k == "line":
            self._draw_line(obj)
        elif k == "text":
            self._draw_text(obj)
        elif k == "overlay":
            self._draw_overlay(obj)
        elif k == "freepath":
            self._draw_freepath(obj)
        self._draw_id_badge(obj)

    def _draw_player(self, o):
        r = o.w/2
        self.canvas.create_oval(o.x-r, o.y-r, o.x+r, o.y+r, fill=o.color, outline="#222", width=2)
        num = o.extra.get("num")
        if num is not None:
            self.canvas.create_text(o.x, o.y, text=str(num), fill="#fff", font=("Segoe UI", int(r*0.9), "bold"))

    def _draw_ball(self, o):
        r = o.w/2
        self.canvas.create_oval(o.x-r, o.y-r, o.x+r, o.y+r, fill="#ffffff", outline="#111", width=2)
        self.canvas.create_line(o.x-r/2, o.y, o.x+r/2, o.y)
        self.canvas.create_line(o.x, o.y-r/2, o.x, o.y+r/2)

    def _draw_cone(self, o):
        w,h = o.w, o.h
        pts = [(o.x, o.y - h/2), (o.x - w/2, o.y + h/2), (o.x + w/2, o.y + h/2)]
        cx, cy = o.x, o.y
        rpts = [rotate_point(px,py,cx,cy,o.rot) for (px,py) in pts]
        self.canvas.create_polygon(*sum(([px,py] for px,py in rpts), []), fill=o.color, outline="#222", width=2)

    def _draw_goal(self, o):
        x0,y0,x1,y1 = o.bbox()
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=o.color, width=4)
        step = max(8, int(o.w/6))
        for i in range(int(o.w//step)+1):
            x = x0 + i*step
            self.canvas.create_line(x, y0, x, y1, fill="#cccccc")
        for j in range(int(o.h//step)+1):
            y = y0 + j*step
            self.canvas.create_line(x0, y, x1, y, fill="#cccccc")

    def _draw_line(self, o):
        x0, y0 = o.extra["x0"], o.extra["y0"]
        x1, y1 = o.extra["x1"], o.extra["y1"]
        style = o.extra.get("style", "run")
        width = int(max(2, o.w/10))
        dash = None
        if style == "pass":
            dash = (10,6)
        elif style == "dribble":
            dash = (2,6)
        self.canvas.create_line(x0, y0, x1, y1, fill=o.color, width=width, dash=dash, smooth=True)
        ang = math.atan2(y1-y0, x1-x0)
        L, a = 16, math.radians(25)
        p1 = (x1, y1)
        p2 = (x1 - L*math.cos(ang-a), y1 - L*math.sin(ang-a))
        p3 = (x1 - L*math.cos(ang+a), y1 - L*math.sin(ang+a))
        self.canvas.create_polygon(p1, p2, p3, fill=o.color, outline=o.color)

    def _draw_text(self, o):
        txt = o.extra.get("text","")
        self.canvas.create_text(o.x, o.y, text=txt, fill=o.color,
                                font=("Segoe UI", max(10, int(o.h/1.5)), "bold"))

    def _draw_overlay(self, o):
        x0,y0,x1,y1 = o.bbox()
        fill = o.extra.get("fill", "#f8e71c")
        self.canvas.create_rectangle(x0,y0,x1,y1, outline=fill, width=2, fill=fill, stipple="gray25")

    def _draw_freepath(self, o):
        pts = o.extra.get("points", [])
        if len(pts) >= 2:
            flat = [c for pt in pts for c in pt]
            th = int(o.extra.get("th", 6))
            self.canvas.create_line(*flat, fill=o.color, width=th, dash=(10,6), smooth=True)

    def _draw_id_badge(self, o):
        _id = o.extra.get("id")
        if _id is None: return
        x0,y0,x1,y1 = o.bbox()
        tx, ty = o.x, y0 - 10
        self.canvas.create_text(tx, ty, text=f"#{_id}", fill="#111", font=("Segoe UI", 9, "bold"))

    def on_click(self, e):
        tool = self.tool.get()
        idx = self.hit_test(e.x, e.y)
        if tool == "move":
            self.selected = idx
            if idx is not None:
                o = self.objects[idx]
                self.drag_offset = (o.x - e.x, o.y - e.y)
                self.is_dragging = True
        elif tool in ("player","ball","cone","goal","text"):
            self.add_object(tool, e.x, e.y)
        elif tool == "line":
            if self.start_line is None:
                self.start_line = (e.x, e.y)
            else:
                x0,y0 = self.start_line
                style = self.ask_line_style()
                self.add_line(x0,y0,e.x,e.y,style)
                self.start_line = None
        elif tool == "overlay":
            self.start_line = (e.x, e.y)
        elif tool == "free_dashed":
            self.temp_path_points = [(e.x, e.y)]
            if self.preview_item:
                self.canvas.delete(self.preview_item); self.preview_item = None
        self._draw_all()

    def on_drag(self, e):
        if self.tool.get() == "move" and self.selected is not None and self.is_dragging:
            o = self.objects[self.selected]
            dx, dy = self.drag_offset
            o.x = clamp(e.x + dx, 0, W)
            o.y = clamp(e.y + dy, 0, H)
            self._draw_all()
        elif self.tool.get() == "overlay" and self.start_line is not None:
            self._draw_all()
            x0,y0 = self.start_line
            if self.preview_item:
                self.canvas.delete(self.preview_item)
            self.preview_item = self.canvas.create_rectangle(x0,y0,e.x,e.y, outline=self.cur_color, dash=(4,3))
        elif self.tool.get() == "free_dashed" and self.temp_path_points is not None:
            self.temp_path_points.append((e.x, e.y))
            self._draw_all()
            flat = [c for pt in self.temp_path_points for c in pt]
            self.preview_item = self.canvas.create_line(*flat, fill=self.cur_color, width=6, dash=(10,6), smooth=True)

    def on_release(self, e):
        if self.tool.get() == "move" and self.is_dragging:
            self.is_dragging = False
            self._push_undo()
        elif self.tool.get() == "overlay" and self.start_line is not None:
            x0,y0 = self.start_line
            x1,y1 = e.x, e.y
            cx = (x0+x1)/2; cy = (y0+y1)/2
            w = abs(x1-x0); h = abs(y1-y0)
            if w>5 and h>5:
                o = BaseObj("overlay", cx, cy, max(10,w), max(10,h), self.cur_color, 0,
                            {"fill": self.cur_color, "alpha": 0.25, "oval": self.overlay_is_oval,
                             "id": self._next_id()})
                self.objects.append(o)
                self.selected = len(self.objects)-1
                self._push_undo()
            self.start_line = None
            if self.preview_item:
                self.canvas.delete(self.preview_item); self.preview_item = None
            self._draw_all()
        elif self.tool.get() == "free_dashed" and self.temp_path_points is not None:
            pts = self.temp_path_points[:]
            if len(pts) >= 2:
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                cx = (min(xs)+max(xs))/2; cy = (min(ys)+max(ys))/2
                w = max(12, (max(xs)-min(xs)))
                h = max(12, (max(ys)-min(ys)))
                o = BaseObj("freepath", cx, cy, w, h, self.cur_color, 0,
                            {"points": pts, "th": 6, "style": "free_dashed", "id": self._next_id()})
                self.objects.append(o)
                self.selected = len(self.objects)-1
                self._push_undo()
            self.temp_path_points = None
            if self.preview_item:
                self.canvas.delete(self.preview_item); self.preview_item = None
            self._draw_all()

    def hit_test(self, x, y):
        for i in range(len(self.objects)-1, -1, -1):
            if self.objects[i].contains(x,y):
                return i
        return None

    def _next_id(self):
        cur = self.seq
        self.seq += 1
        return cur

    def add_object(self, kind, x, y):
        if kind == "player":
            num = simpledialog.askinteger("Oyuncu No", "Numara (isteğe bağlı):", minvalue=0, maxvalue=99)
            o = BaseObj("player", x, y, 44, 44, self.cur_color, 0, {"num": num, "id": self._next_id()})
        elif kind == "ball":
            o = BaseObj("ball", x, y, 22, 22, "#111", 0, {"id": self._next_id()})
        elif kind == "cone":
            o = BaseObj("cone", x, y, 36, 40, "#ff7f0e", 0, {"id": self._next_id()})
        elif kind == "goal":
            o = BaseObj("goal", x, y, 100, 70, "#ffffff", 0, {"id": self._next_id()})
        elif kind == "text":
            txt = simpledialog.askstring("Metin", "Yazı:")
            if not txt: return
            o = BaseObj("text", x, y, 10, 26, self.cur_color, 0, {"text": txt, "id": self._next_id()})
        else:
            return
        self.objects.append(o)
        self.selected = len(self.objects)-1
        self._push_undo()

    def add_line(self, x0,y0,x1,y1,style):
        cx, cy = (x0+x1)/2, (y0+y1)/2
        length = math.dist((x0,y0),(x1,y1))
        o = BaseObj("line", cx, cy, max(20,length), 8, self.cur_color, 0,
                    {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "style": style, "id": self._next_id()})
        self.objects.append(o)
        self.selected = len(self.objects)-1
        self._push_undo()

    def new(self):
        self.objects.clear()
        self.selected = None
        self.seq = 1
        self._push_undo()
        self._draw_all()

    def open_json(self):
        p = filedialog.askopenfilename(title="Aç (.json)", filetypes=[("JSON","*.json")])
        if not p: return
        try:
            with open(p,"r",encoding="utf-8") as f:
                data = json.load(f)
            self.objects = [BaseObj.from_dict(o) for o in data.get("objects",[])]
            max_id = 0
            for o in self.objects:
                oid = o.extra.get("id", 0)
                if oid > max_id: max_id = oid
            self.seq = max_id + 1
            self.current_file = p
            self.selected = None
            self.undo_stack.clear(); self.redo_stack.clear(); self._push_undo()
            self._draw_all()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def save_json(self):
        p = filedialog.asksaveasfilename(title="Kaydet (.json)", defaultextension=".json",
                                         filetypes=[("JSON","*.json")])
        if not p: return
        try:
            data = {"objects":[o.to_dict() for o in self.objects]}
            with open(p,"w",encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.current_file = p
            messagebox.showinfo("Kaydedildi", p)
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def export_png(self):
        p = filedialog.asksaveasfilename(title="PNG Dışa Aktar", defaultextension=".png",
                                         filetypes=[("PNG","*.png")])
        if not p: return
        img = self.render_pillow()
        img.save(p)
        messagebox.showinfo("PNG", "Kaydedildi:\n"+p)

    def export_pdf(self):
        p = filedialog.asksaveasfilename(title="PDF Dışa Aktar", defaultextension=".pdf",
                                         filetypes=[("PDF","*.pdf")])
        if not p: return
        img = self.render_pillow().convert("RGB")
        img.save(p, "PDF", resolution=150.0)
        messagebox.showinfo("PDF", "Kaydedildi:\n"+p)

    def render_pillow(self):
        img = Image.new("RGB", (W, H), "#77b255" if self.pitch.get() else "#e9ecef")
        drw = ImageDraw.Draw(img)

        if self.pitch.get():
            pad = 30
            x0, y0 = pad, pad
            x1, y1 = W - pad, H - pad
            drw.rectangle([x0,y0,x1,y1], outline="#3d7a3b", width=2)
            drw.line([((x0+x1)/2, y0), ((x0+x1)/2, y1)], fill="#ffffff", width=2)
            drw.ellipse([(x0+x1)/2-60, (y0+y1)/2-60, (x0+x1)/2+60, (y0+y1)/2+60], outline="#ffffff", width=2)
            box_w, box_h = 160, 300
            drw.rectangle([x0, (y0+y1)/2-box_h/2, x0+box_w, (y0+y1)/2+box_h/2], outline="#ffffff", width=2)
            drw.rectangle([x1-box_w, (y0+y1)/2-box_h/2, x1, (y0+y1)/2+box_h/2], outline="#ffffff", width=2)
            g_w, g_h = 60, 180
            drw.rectangle([x0, (y0+y1)/2-g_h/2, x0+g_w, (y0+y1)/2+g_h/2], outline="#ffffff", width=2)
            drw.rectangle([x1-g_w, (y0+y1)/2-g_h/2, x1, (y0+y1)/2+g_h/2], outline="#ffffff", width=2)
            drw.ellipse([x0+110-3, (y0+y1)/2-3, x0+110+3, (y0+y1)/2+3], fill="#ffffff", outline=None)
            drw.ellipse([x1-110-3, (y0+y1)/2-3, x1-110+3, (y0+y1)/2+3], fill="#ffffff", outline=None)

        for o in self.objects:
            self._render_obj(drw, o)
            self._render_id(drw, o)

        return img

    def _render_obj(self, drw, o):
        if o.kind == "player":
            r = o.w/2
            drw.ellipse([o.x-r, o.y-r, o.x+r, o.y+r], fill=o.color, outline="#222", width=2)
            num = o.extra.get("num")
            if num is not None:
                try:
                    font = ImageFont.truetype("arial.ttf", int(r*0.9))
                except Exception:
                    font = ImageFont.load_default()
                bbox = drw.textbbox((0,0), str(num), font=font)
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                drw.text((o.x - tw/2, o.y - th/2), str(num), fill="#ffffff", font=font)
        elif o.kind == "ball":
            r = o.w/2
            drw.ellipse([o.x-r, o.y-r, o.x+r, o.y+r], fill="#ffffff", outline="#111", width=2)
            drw.line([o.x-r/2, o.y, o.x+r/2, o.y], fill="#111", width=1)
            drw.line([o.x, o.y-r/2, o.x, o.y+r/2], fill="#111", width=1)
        elif o.kind == "cone":
            w,h = o.w, o.h
            pts = [(o.x, o.y - h/2), (o.x - w/2, o.y + h/2), (o.x + w/2, o.y + h/2)]
            pts = [rotate_point(px,py,o.x,o.y,o.rot) for (px,py) in pts]
            drw.polygon(pts, fill=o.color, outline="#222")
        elif o.kind == "goal":
            x0,y0,x1,y1 = o.bbox()
            drw.rectangle([x0,y0,x1,y1], outline=o.color, width=4)
            step = max(8, int(o.w/6))
            for i in range(int(o.w//step)+1):
                x = x0 + i*step
                drw.line([x,y0,x,y1], fill="#cccccc", width=1)
            for j in range(int(o.h//step)+1):
                y = y0 + j*step
                drw.line([x0,y,x1,y], fill="#cccccc", width=1)
        elif o.kind == "line":
            x0,y0 = o.extra["x0"], o.extra["y0"]
            x1,y1 = o.extra["x1"], o.extra["y1"]
            style = o.extra.get("style","run")
            width = int(max(2, o.w/10))
            if style == "run":
                drw.line([x0,y0,x1,y1], fill=o.color, width=width)
            elif style == "pass":
                self._draw_dashed(drw, (x0,y0,x1,y1), o.color, width, 14, 8)
            else:
                self._draw_dashed(drw, (x0,y0,x1,y1), o.color, width, 4, 10)
            ang = math.atan2(y1-y0, x1-x0)
            L, a = 16, math.radians(25)
            p1 = (x1, y1)
            p2 = (x1 - L*math.cos(ang-a), y1 - L*math.sin(ang-a))
            p3 = (x1 - L*math.cos(ang+a), y1 - L*math.sin(ang+a))
            drw.polygon([p1,p2,p3], fill=o.color, outline=o.color)
        elif o.kind == "text":
            txt = o.extra.get("text","")
            try:
                font = ImageFont.truetype("arial.ttf", max(12, int(o.h)))
            except Exception:
                font = ImageFont.load_default()
            drw.text((o.x, o.y), txt, fill=o.color, font=font, anchor="mm")
        elif o.kind == "overlay":
            x0,y0,x1,y1 = o.bbox(); fill = o.extra.get("fill","#f8e71c")
            drw.rectangle([x0,y0,x1,y1], outline=fill, width=2)
            for k in range(0, int(x1-x0), 6):
                drw.line([x0+k, y0, x0+k, y1], fill=fill, width=1)
        elif o.kind == "freepath":
            pts = o.extra.get("points", [])
            th = int(o.extra.get("th", 6))
            for i in range(len(pts)-1):
                x0,y0 = pts[i]; x1,y1 = pts[i+1]
                self._draw_dashed(drw, (x0,y0,x1,y1), o.color, th, 10, 6)

    def _render_id(self, drw, o):
        _id = o.extra.get("id")
        if _id is None: return
        x0,y0,x1,y1 = o.bbox()
        tx, ty = o.x, y0 - 10
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except Exception:
            font = ImageFont.load_default()
        drw.text((tx, ty), f"#{_id}", fill="#111", font=font, anchor="mm")

    def _draw_dashed(self, drw, line, color, width, dash_len, gap_len):
        x0,y0,x1,y1 = line
        total = math.dist((x0,y0),(x1,y1))
        if total == 0: return
        dx = (x1-x0)/total; dy=(y1-y0)/total
        dist = 0
        while dist < total:
            x_start = x0 + dx*dist
            y_start = y0 + dy*dist
            x_end = x0 + dx*min(total, dist+dash_len)
            y_end = y0 + dy*min(total, dist+dash_len)
            drw.line([x_start,y_start,x_end,y_end], fill=color, width=width)
            dist += dash_len + gap_len

    def _push_undo(self):
        state = json.dumps([o.to_dict() for o in self.objects])
        self.undo_stack.append(state)
        if len(self.undo_stack) > UNDO_LIMIT:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) <= 1: return
        cur = self.undo_stack.pop()
        self.redo_stack.append(cur)
        prev = self.undo_stack[-1]
        self.objects = [BaseObj.from_dict(o) for o in json.loads(prev)]
        self.selected = None
        self._draw_all()

    def redo(self):
        if not self.redo_stack: return
        nxt = self.redo_stack.pop()
        self.undo_stack.append(nxt)
        self.objects = [BaseObj.from_dict(o) for o in json.loads(nxt)]
        self.selected = None
        self._draw_all()

    def toggle_overlay_tool(self):
        if self.tool.get() != "overlay":
            self.tool.set("overlay")
        else:
            self.overlay_is_oval = not self.overlay_is_oval
            messagebox.showinfo("Overlay", "Şekil: " + ("Oval" if self.overlay_is_oval else "Dikdörtgen"))

    def choose_color(self):
        c = colorchooser.askcolor(color=self.cur_color)[1]
        if c:
            self.cur_color = c
            if self.selected is not None:
                self.objects[self.selected].color = c
                self._draw_all(); self._push_undo()

    def cycle_color(self):
        try:
            i = TEAM_COLORS.index(self.cur_color)
            self.cur_color = TEAM_COLORS[(i+1)%len(TEAM_COLORS)]
        except ValueError:
            self.cur_color = TEAM_COLORS[0]
        if self.selected is not None:
            self.objects[self.selected].color = self.cur_color
            self._draw_all(); self._push_undo()

    def rotate_selected(self, deg):
        if self.selected is None: return
        o = self.objects[self.selected]
        o.rot = (o.rot + deg) % 360
        self._draw_all(); self._push_undo()

    def scale_selected(self, factor):
        if self.selected is None: return
        o = self.objects[self.selected]
        o.w = clamp(o.w * factor, 8, 400)
        o.h = clamp(o.h * factor, 8, 400)
        self._draw_all(); self._push_undo()

    def delete_selected(self):
        if self.selected is None: return
        self.objects.pop(self.selected)
        self.selected = None
        self._draw_all(); self._push_undo()

    def _show_shortcuts(self):
        msg = ("Kısayollar:\n"
               "m: move/taşı\nr: rotate\n+: büyüt, -: küçült\n"
               "d: sil\nt: metin\nl: çizgi/ok\no: overlay (oval/dikdörtgen toggle)\n"
               "f: serbest kesikli çizgi\n"
               "p: renk döngüsü\nz: geri al\ny: ileri al")
        messagebox.showinfo("Shortcuts", msg)

if __name__ == "__main__":
    app = App()
    app.mainloop()
