import time
import random
import sys
import tkinter as tk

# Global değişkenler
dogru_tiklama = False
tiklama_oldu = False

def on_click(event):
    global dogru_tiklama, tiklama_oldu
    tiklama_oldu = True
    dx = event.x - daire_x
    dy = event.y - daire_y
    if dx**2 + dy**2 <= (daire_r ** 2):
        dogru_tiklama = True
    root.destroy()

# Bekleme (örnek için 3 saniye)
time.sleep(3)

# Tkinter pencere
root = tk.Tk()
root.attributes("-topmost", True)
root.attributes("-fullscreen", True)

# Arka planı şeffaflaştırmak için
root.config(bg='pink')  # şeffaf yapılacak renk
root.wm_attributes("-transparentcolor", "pink")  # sadece kırmızı daire görünsün

canvas = tk.Canvas(root, bg='pink', highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Daire koordinatları
root.update()  # ekran boyutlarını almak için
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
daire_r = 48
daire_x = random.randint(daire_r, screen_width - daire_r)
daire_y = random.randint(daire_r, screen_height - daire_r)

# Kırmızı daire çiz
canvas.create_oval(daire_x - daire_r, daire_y - daire_r,
                   daire_x + daire_r, daire_y + daire_r,
                   fill="red", outline="")

canvas.bind("<Button-1>", on_click)

# 3 saniye sonra pencereyi kapat
root.after(3000, root.destroy)
root.mainloop()

# Sonucu C#'a ilet
if tiklama_oldu:
    if dogru_tiklama:
        print("dogru")
    else:
        print("yanlis")
else:
    print("tiklanmadi")

sys.stdout.flush()
