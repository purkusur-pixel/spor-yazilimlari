import sys
import os
import sqlite3
import cv2
import numpy as np
import datetime
import shutil

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QFileDialog, QMessageBox, QSlider, QGroupBox, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt

# MEVCUT DOSYAYI MODÜL OLARAK İÇE AKTARIYORUZ
import yeni12 

# ===========================================================
# VERİTABANI İŞLEMLERİ
# ===========================================================
def init_db():
    conn = sqlite3.connect("termal_veri.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hastalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT,
            tc_no TEXT,
            hissedilen_agri INTEGER,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            orijinal_resim_yolu TEXT,
            islenmis_resim_yolu TEXT
        )
    """)
    conn.commit()
    conn.close()

def kayit_ekle(ad, tc, agri, orj, isl):
    conn = sqlite3.connect("termal_veri.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hastalar (ad_soyad, tc_no, hissedilen_agri, orijinal_resim_yolu, islenmis_resim_yolu) VALUES (?, ?, ?, ?, ?)", 
                   (ad, tc, agri, orj, isl))
    conn.commit()
    conn.close()

# ===========================================================
# GUI SINIFI
# ===========================================================
class TermalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Termal Analiz Sistemi (Yeni12 Entegrasyonu)")
        self.setGeometry(50, 50, 1400, 900)
        
        init_db()
        self.current_img_path = None
        self.temp_img_name = "temp_process_image.jpg" # Türkçe karakter sorunu için geçici dosya
        
        self.init_ui()

    def init_ui(self):
        # Ana Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # --- SOL PANEL ---
        left_panel = QGroupBox("Hasta Bilgileri")
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(320)

        # Girişler
        left_layout.addWidget(QLabel("Ad Soyad:"))
        self.input_name = QLineEdit()
        left_layout.addWidget(self.input_name)

        left_layout.addWidget(QLabel("TC Kimlik No:"))
        self.input_tc = QLineEdit()
        left_layout.addWidget(self.input_tc)

        # Slider
        left_layout.addSpacing(15)
        left_layout.addWidget(QLabel("Ağrı Düzeyi (VAS 0-10):"))
        slider_box = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 10)
        self.lbl_slider_val = QLabel("0")
        self.lbl_slider_val.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_slider_val.setStyleSheet("color: red")
        self.slider.valueChanged.connect(lambda v: self.lbl_slider_val.setText(str(v)))
        slider_box.addWidget(self.slider)
        slider_box.addWidget(self.lbl_slider_val)
        left_layout.addLayout(slider_box)

        left_layout.addSpacing(20)
        
        # Butonlar
        self.btn_load = QPushButton("📂 Resim Yükle")
        self.btn_load.setStyleSheet("padding: 10px; background-color: #3498db; color: white; font-weight: bold;")
        self.btn_load.clicked.connect(self.load_image)
        left_layout.addWidget(self.btn_load)

        self.btn_process = QPushButton("⚡ Analiz Et ve Kaydet")
        self.btn_process.setStyleSheet("padding: 10px; background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_process.clicked.connect(self.run_logic)
        self.btn_process.setEnabled(False)
        left_layout.addWidget(self.btn_process)

        left_layout.addStretch()
        
        # --- SAĞ PANEL ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.lbl_display = QLabel("Görüntü bekleniyor...")
        self.lbl_display.setAlignment(Qt.AlignCenter)
        self.lbl_display.setStyleSheet("background-color: #2c3e50; color: white;")
        scroll.setWidget(self.lbl_display)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(scroll, stretch=1)

    def load_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Resim Seç", "", "Resim Dosyaları (*.jpg *.png *.jpeg)")
        if fname:
            self.current_img_path = fname
            self.btn_process.setEnabled(True)
            
            # Önizleme (Binary okuma ile Türkçe karakter desteği)
            try:
                with open(fname, "rb") as f: data = f.read()
                arr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                self.show_image(img)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Resim açılamadı: {e}")

    def show_image(self, cv_img):
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.lbl_display.setPixmap(pix.scaled(self.lbl_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def run_logic(self):
        """
        Bu fonksiyon yeni12.py içindeki main() fonksiyonunun mantığını
        GUI içinde adım adım çalıştırır.
        """
        ad = self.input_name.text()
        tc = self.input_tc.text()
        if not ad or not tc:
            QMessageBox.warning(self, "Uyarı", "Lütfen Ad ve TC giriniz.")
            return

        # 1. GÜVENLİ DOSYA OLUŞTURMA (Türkçe karakter sorununu aşmak için)
        # Resmi binary okuyup, basit bir isimle (temp_process_image.jpg) kaydediyoruz.
        # Böylece yeni12.py içindeki cv2.imread hata vermez.
        try:
            with open(self.current_img_path, "rb") as f:
                img_data = f.read()
            with open(self.temp_img_name, "wb") as f:
                f.write(img_data)
        except Exception as e:
            QMessageBox.critical(self, "Dosya Hatası", f"Geçici dosya oluşturulamadı: {e}")
            return

        try:
            # =========================================================================
            # YENI12 MANTIĞI (Main fonksiyonunun GUI'ye uyarlanmış hali)
            # =========================================================================
            
            # A) Segmentasyon
            # yeni12.py dosyasındaki fonksiyonları çağırıyoruz
            img, final_mask, bbox, symmetry_x = yeni12.segment_thermal_to_binary(self.temp_img_name)
            
            if img is None: raise ValueError("Görüntü işlenemedi.")

            ust_diz_l, ust_diz_r, bilek_l, bilek_r, ayak_bilek_l, ayak_bilek_r, y_hips, person = \
                yeni12.extract_lower_from_binary_mask(final_mask)

            kasik_x, kasik_y = yeni12.find_groin_from_components(person, bbox)
            GROIN = (kasik_x, kasik_y)

            ALT_DIZ_L, ALT_DIZ_R = yeni12.find_mid_leg_points(
                ust_diz_l, ust_diz_r, bilek_l, bilek_r, person, img)

            TOE_L, TOE_R = yeni12.find_toes_from_person_mask(person)

            # B) Kırmızı/Sıcak Bölge Filtreleri (Logic from main)
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            lower_red1 = np.array([0, 70, 80], dtype=np.uint8)
            upper_red1 = np.array([10, 255, 255], dtype=np.uint8)
            lower_red2 = np.array([170, 70, 80], dtype=np.uint8)
            upper_red2 = np.array([180, 255, 255], dtype=np.uint8)
            mask_red = cv2.bitwise_or(cv2.inRange(hsv_img, lower_red1, upper_red1), 
                                      cv2.inRange(hsv_img, lower_red2, upper_red2))
            
            mask_white = cv2.inRange(hsv_img, np.array([0, 0, 180]), np.array([180, 80, 255]))
            mask_kirmizi_ham = cv2.bitwise_or(mask_red, mask_white)

            person_bool = (person > 0).astype(np.uint8) * 255
            person_kirmizi = cv2.bitwise_and(mask_kirmizi_ham, person_bool)

            k = np.ones((5, 5), np.uint8)
            person_kirmizi = cv2.morphologyEx(person_kirmizi, cv2.MORPH_OPEN, k)
            person_kirmizi = cv2.morphologyEx(person_kirmizi, cv2.MORPH_CLOSE, k)

            # Eller/Kollar Filtreleme (Main logic)
            H_p, W_p = person_kirmizi.shape
            x0 = int(symmetry_x)
            x0 = max(0, min(W_p - 1, x0))
            kasik_y_local = int(kasik_y)
            bx, by, bw, bh = bbox
            half_band = int(bw * 0.35)
            x1_band = max(0, x0 - half_band)
            x2_band = min(W_p - 1, x0 + half_band)
            band_mask = np.zeros_like(person_kirmizi)
            band_mask[0:kasik_y_local, x1_band:x2_band] = 255
            band_mask[kasik_y_local:H_p, :] = 255
            person_kirmizi = cv2.bitwise_and(person_kirmizi, band_mask)

            # C) Çizim İşlemleri (Vis)
            vis = img.copy()

            # Yardımcı çiziciler
            def draw_pt(p, color):
                if p: cv2.circle(vis, (int(p[0]), int(p[1])), 6, color, -1)
            
            def draw_ln(p1, p2, color):
                if p1 and p2:
                    cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, 2)
                    mx, my = (p1[0]+p2[0])//2, (p1[1]+p2[1])//2
                    cv2.circle(vis, (mx, my), 6, color, -1)

            draw_pt(GROIN, (255, 0, 255))
            draw_ln(ust_diz_l, ust_diz_r, (0, 255, 0))

            # Alt Bacak Bölme ve Renklendirme
            if ALT_DIZ_L and ALT_DIZ_R and bilek_l and bilek_r:
                base_mask = person_kirmizi if np.any(person_kirmizi > 0) else person
                y_top = int((ALT_DIZ_L[1] + ALT_DIZ_R[1]) / 2)
                y_bot = int((bilek_l[1] + bilek_r[1]) / 2)

                # SOL
                row = base_mask[y_top, :] > 0
                xs = np.where(row)[0]
                xs_sol = xs[xs <= GROIN[0]]
                if xs_sol.size > 5:
                    x_spl, _ = yeni12.split_lower_leg_area(base_mask, y_top, y_bot, int(xs_sol[0]), int(xs_sol[-1]))
                    if x_spl:
                        cv2.line(vis, (x_spl, y_top), (x_spl, y_bot), (255,255,0), 2)
                        bounds = [int(xs_sol[0]), x_spl, int(xs_sol[-1])]
                        cols = [(0,0,255), (0,255,0)]
                        for i in range(2):
                            ov = vis.copy()
                            cv2.rectangle(ov, (bounds[i], y_top), (bounds[i+1], y_bot), cols[i], -1)
                            clp = cv2.bitwise_and(ov, ov, mask=base_mask)
                            vis[clp>0] = cv2.addWeighted(vis, 0.72, clp, 0.28, 0)[clp>0]
                            cx, cy = (bounds[i]+bounds[i+1])//2, (y_top+y_bot)//2
                            cv2.putText(vis, str(i+1), (cx-5, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

                # SAĞ
                xs_sag = xs[xs >= GROIN[0]]
                if xs_sag.size > 5:
                    x_spl, _ = yeni12.split_lower_leg_area(base_mask, y_top, y_bot, int(xs_sag[0]), int(xs_sag[-1]))
                    if x_spl:
                        cv2.line(vis, (x_spl, y_top), (x_spl, y_bot), (0,255,255), 2)
                        bounds = [int(xs_sag[0]), x_spl, int(xs_sag[-1])]
                        cols = [(255,0,0), (0,255,255)]
                        for i in range(2):
                            ov = vis.copy()
                            cv2.rectangle(ov, (bounds[i], y_top), (bounds[i+1], y_bot), cols[i], -1)
                            clp = cv2.bitwise_and(ov, ov, mask=base_mask)
                            vis[clp>0] = cv2.addWeighted(vis, 0.72, clp, 0.28, 0)[clp>0]
                            cx, cy = (bounds[i]+bounds[i+1])//2, (y_top+y_bot)//2
                            cv2.putText(vis, str(i+1), (cx-8, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

            # Çizgiler
            if ALT_DIZ_L and ALT_DIZ_R:
                y = int((ALT_DIZ_L[1] + ALT_DIZ_R[1]) / 2)
                l, r = yeni12.horizontal_leg_line(base_mask, y)
                if l and r: 
                    cv2.line(vis, l, r, (255,165,0), 2)
                    draw_pt(l, (255,165,0)); draw_pt(r, (255,165,0))

            if bilek_l and bilek_r:
                y = int((bilek_l[1] + bilek_r[1]) / 2)
                l, r = yeni12.horizontal_leg_line(base_mask, y)
                if l and r:
                    cv2.line(vis, l, r, (0,255,255), 2)
                    draw_pt(l, (0,255,255)); draw_pt(r, (0,255,255))
            
            if TOE_L and TOE_R:
                y = int((TOE_L[1] + TOE_R[1]) / 2)
                l, r = yeni12.horizontal_leg_line(base_mask, y)
                if l and r:
                    cv2.line(vis, l, r, (255,128,0), 2)
                    draw_pt(l, (255,128,0)); draw_pt(r, (255,128,0))

            yeni12.draw_groin_ellipses_clipped(vis, GROIN, person, person_kirmizi)

            # Üst Bacak Bölmeleri (Sağ ve Sol Logic from Main)
            def draw_upper_splits(u_diz, is_right):
                if not u_diz or not person_kirmizi is not None: return
                y_u, gx = int(u_diz[1]), int(GROIN[0])
                # Üst limit bul
                top_lim = 0
                for yy in range(y_u-1, -1, -1):
                    row = person_kirmizi[yy, :] > 0
                    xs = np.where(row)[0]
                    xs = xs[xs >= gx] if is_right else xs[xs <= gx]
                    if xs.size > 3: top_lim = yy
                    else: break
                if top_lim == 0: top_lim = max(0, y_u - 80)
                
                # Bölme
                row = person_kirmizi[y_u, :] > 0
                xs = np.where(row)[0]
                xs = xs[xs >= gx] if is_right else xs[xs <= gx]
                
                if xs.size > 3:
                    x_s, x_e = int(xs[0]), int(xs[-1])
                    xr = np.arange(x_s, x_e + 1)
                    h_arr = np.zeros_like(xr, dtype=np.int64)
                    for i, x in enumerate(xr):
                        h_arr[i] = (person_kirmizi[top_lim:y_u+1, x]>0).sum()
                    
                    tot = h_arr.sum()
                    if tot > 0:
                        cum = np.cumsum(h_arr)
                        b1 = int(xr[int(np.searchsorted(cum, tot/3.0))])
                        b2 = int(xr[int(np.searchsorted(cum, 2*tot/3.0))])
                        
                        bounds = [x_s, b1, b2, x_e]
                        cols = [(0,0,255), (0,255,0), (255,0,0)]
                        for idx in range(3):
                            ov = vis.copy()
                            cv2.rectangle(ov, (bounds[idx], top_lim), (bounds[idx+1], y_u), cols[idx], -1)
                            vis[:] = cv2.addWeighted(ov, 0.3, vis, 0.7, 0)
                            cv2.line(vis, (bounds[idx+1], top_lim), (bounds[idx+1], y_u), (255,255,255), 2)
                            cx = (bounds[idx]+bounds[idx+1])//2
                            cy = (top_lim+y_u)//2
                            cv2.putText(vis, str(idx+1), (cx-5, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

            draw_upper_splits(ust_diz_r, True)
            draw_upper_splits(ust_diz_l, False)

            # =========================================================================
            # SONUÇLARI KAYDET VE GÖSTER
            # =========================================================================
            
            # Ekran
            self.show_image(vis)
            
            # Dosya İsimleri
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = ad.replace(" ", "_")
            out_main = f"analiz_{safe_name}_{timestamp}.png"
            
            # Kaydet (Türkçe karakter destekli)
            is_success, im_buf = cv2.imencode(".png", vis)
            if is_success:
                with open(out_main, "wb") as f: im_buf.tofile(f)
            
            # DB Kayıt
            kayit_ekle(ad, tc, self.slider.value(), self.current_img_path, out_main)

            QMessageBox.information(self, "Başarılı", f"Analiz tamamlandı.\nDosya: {out_main}")

        except Exception as e:
            QMessageBox.critical(self, "Analiz Hatası", str(e))
        
        finally:
            # GEÇİCİ DOSYAYI SİL (Temizlik)
            if os.path.exists(self.temp_img_name):
                os.remove(self.temp_img_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TermalApp()
    window.show()
    sys.exit(app.exec_())