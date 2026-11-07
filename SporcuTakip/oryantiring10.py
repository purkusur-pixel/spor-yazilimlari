import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QComboBox, QGroupBox,
                             QMessageBox, QHeaderView, QTabWidget, QTextEdit,
                             QLineEdit, QFormLayout, QDialog, QCheckBox, QFileDialog, QSpinBox)
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QFont, QColor, QPixmap
import serial
import serial.tools.list_ports
from datetime import datetime
import sqlite3
import csv
import random
import json

# Sabitler
HARITA_IMAGE_PATH = ''
KONUM_KAYIT_DOSYASI = 'merkez_konumlari.json'

# ----------------------------------------------------------------------
# 1. VERİTABANI YÖNETİCİSİ (DatabaseManager)
# ----------------------------------------------------------------------

class DatabaseManager:
    """SQLite veritabanı yöneticisi"""
    def __init__(self, db_name='orienteering.db'):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                number TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid TEXT NOT NULL,
                center_id INTEGER NOT NULL,
                passage_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rfid) REFERENCES participants(rfid)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passages_rfid ON passages(rfid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passages_center ON passages(center_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passages_time ON passages(passage_time)')

        conn.commit()
        conn.close()

    def add_participant(self, rfid, name, number):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO participants (rfid, name, number) VALUES (?, ?, ?)', (rfid, name, number))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception:
            return False

    def update_participant(self, rfid, name, number):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE participants SET name=?, number=? WHERE rfid=?', (name, number, rfid))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_participant(self, rfid):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM passages WHERE rfid=?', (rfid,))
            cursor.execute('DELETE FROM participants WHERE rfid=?', (rfid,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_participant(self, rfid):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT rfid, name, number FROM participants WHERE rfid=?', (rfid,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {'rfid': result[0], 'name': result[1], 'number': result[2]}
        return None

    def get_all_participants(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT rfid, name, number FROM participants ORDER BY number')
        results = cursor.fetchall()
        conn.close()

        return [{'rfid': r[0], 'name': r[1], 'number': r[2]} for r in results]

    def add_passage(self, rfid, center_id, passage_time=None):
        if passage_time is None:
            passage_time = datetime.now()

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO passages (rfid, center_id, passage_time) VALUES (?, ?, ?)',
                (rfid, center_id, passage_time)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_participant_passages(self, rfid):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT center_id, passage_time 
            FROM passages 
            WHERE rfid=? 
            ORDER BY passage_time
        ''', (rfid,))
        results = cursor.fetchall()
        conn.close()

        passages = {}
        for center_id, passage_time in results:
            if center_id not in passages:
                passages[center_id] = []
            passages[center_id].append(datetime.fromisoformat(passage_time))

        return passages

    def get_center_passages(self, center_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.rfid, pt.name, pt.number, p.passage_time
            FROM passages p
            JOIN participants pt ON p.rfid = pt.rfid
            WHERE p.center_id = ?
            ORDER BY p.passage_time DESC
        ''', (center_id,))
        results = cursor.fetchall()
        conn.close()

        return [{'rfid': r[0], 'name': r[1], 'number': r[2],
                 'time': datetime.fromisoformat(r[3])} for r in results]

    def get_all_results(self, completed_only=False, total_centers=14):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT 
                pt.rfid, 
                pt.name, 
                pt.number,
                COUNT(DISTINCT p.center_id) as completed_centers,
                MAX(p.passage_time) as last_passage
            FROM participants pt
            LEFT JOIN passages p ON pt.rfid = p.rfid
            GROUP BY pt.rfid, pt.name, pt.number
        '''

        if completed_only:
            query += f" HAVING completed_centers = {total_centers}"

        query += " ORDER BY completed_centers DESC, last_passage ASC"

        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        return [{'rfid': r[0], 'name': r[1], 'number': r[2],
                 'completed': r[3],
                 'last_time': datetime.fromisoformat(r[4]) if r[4] else None}
                for r in results]

# ----------------------------------------------------------------------
# 2. SERİ PORT YÖNETİCİSİ (SerialManager)
# ----------------------------------------------------------------------

class SerialManager:
    """RFID okuyucu ile seri port iletişimini yöneten sınıf"""
    def __init__(self):
        self.connection = None
        self.is_connected = False

    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port, baudrate=9600):
        try:
            self.connection = serial.Serial(port, baudrate, timeout=1)
            self.is_connected = True
            return True
        except Exception:
            self.is_connected = False
            return False

    def disconnect(self):
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False

    def read_rfid(self):
        if self.connection and self.is_connected:
            try:
                if self.connection.in_waiting > 0:
                    data = self.connection.readline().decode('utf-8').strip()
                    return data
            except Exception:
                pass
        return None

# ----------------------------------------------------------------------
# 3. KATILIMCI DİYALOĞU (ParticipantDialog)
# ----------------------------------------------------------------------

class ParticipantDialog(QDialog):
    """Katılımcı ekleme/düzenleme diyalogu"""
    def __init__(self, parent=None, rfid=None, name=None, number=None):
        super().__init__(parent)
        self.setWindowTitle("Katılımcı Kaydet" if not rfid else "Katılımcı Düzenle")
        self.setModal(True)
        self.setMinimumWidth(450)

        layout = QFormLayout()

        rfid_layout = QHBoxLayout()
        self.rfid_input = QLineEdit()
        self.rfid_input.setPlaceholderText("RFID numarasını girin veya yüzüğü okutun")
        if rfid:
            self.rfid_input.setText(rfid)
            self.rfid_input.setReadOnly(True)
        rfid_layout.addWidget(self.rfid_input)

        self.scan_btn = QPushButton("📡 Yüzük Okut (Seri Port Gerekir)")
        self.scan_btn.clicked.connect(self.scan_rfid)
        rfid_layout.addWidget(self.scan_btn)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ad Soyad")
        if name:
            self.name_input.setText(name)

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Yarışma Numarası (örn: 101)")
        if number:
            self.number_input.setText(number)

        layout.addRow("RFID:", rfid_layout)
        layout.addRow("Ad Soyad:", self.name_input)
        layout.addRow("Numara:", self.number_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Kaydet")
        self.save_btn.setStyleSheet("background-color: #28a745; color: white; padding: 8px;")
        self.cancel_btn = QPushButton("❌ İptal")

        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        self.scan_mode = False
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.check_scan)

    def scan_rfid(self):
        if not self.scan_mode:
            self.scan_mode = True
            self.scan_btn.setText("⏹ Okumayı Durdur")
            self.scan_btn.setStyleSheet("background-color: #dc3545; color: white;")
            self.rfid_input.setPlaceholderText("Yüzüğü okutun...")
            self.scan_timer.start(100)
        else:
            self.stop_scan()

    def stop_scan(self):
        self.scan_mode = False
        self.scan_btn.setText("📡 Yüzük Okut (Seri Port Gerekir)")
        self.scan_btn.setStyleSheet("")
        self.rfid_input.setPlaceholderText("RFID numarasını girin veya yüzüğü okutun")
        self.scan_timer.stop()

    def check_scan(self):
        main_window = self.parent()
        if main_window and hasattr(main_window, 'last_scanned_rfid'):
            if main_window.last_scanned_rfid:
                self.rfid_input.setText(main_window.last_scanned_rfid)
                main_window.last_scanned_rfid = None
                self.stop_scan()

    def validate_and_accept(self):
        if not self.rfid_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "RFID numarası boş olamaz!")
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Ad Soyad boş olamaz!")
            return
        if not self.number_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Numara boş olamaz!")
            return

        self.accept()

    def get_data(self):
        return {
            'rfid': self.rfid_input.text().strip(),
            'name': self.name_input.text().strip(),
            'number': self.number_input.text().strip()
        }

# Harita üzerinde varsayılan merkez konumları (Yüzdesel)
MERKEZ_KONUMLARI = {
    1: [48, 54], 2: [85, 45], 3: [85, 30], 4: [70, 20], 5: [45, 25],
    6: [20, 30], 7: [15, 55], 8: [30, 70], 9: [50, 75], 10: [70, 70],
    11: [65, 55], 12: [35, 40], 13: [55, 10], 14: [25, 65]
}

# ----------------------------------------------------------------------
# 4A. MERKEZ BUTONU SINIFI
# ----------------------------------------------------------------------

class CenterButton(QPushButton):
    """Harita üzerindeki merkez butonu (sürükle-bırak destekli)"""
    def __init__(self, center_id, map_widget):
        super().__init__(str(center_id), map_widget.map_label)
        self.center_id = center_id
        self.map_widget = map_widget
        self.setProperty('center_id', center_id)
        self.dragging = False
        self.drag_offset = QPoint()

        # Yazı boyutu ve kalınlık
        font = self.font()
        font.setPointSize(14)      # İstersen 16–18 yapabilirsin
        font.setBold(True)
        self.setFont(font)

        # Buton boyutu ve renkleri (çok daha okunaklı)
        self.setFixedSize(46, 46)
        self.setStyleSheet("""
            QPushButton {
                border-radius: 23px;
                border: 2px solid #ffffff;
                font-weight: bold;
                font-size: 16px;
                background-color: rgba(0, 0, 0, 200);   /* Koyu arka plan */
                color: #ffffff;                          /* Beyaz yazı */
            }
            QPushButton:hover {
                border: 2px solid #ffd700;
            }
            QPushButton:checked {
                background-color: rgba(220, 53, 69, 230); /* Kırmızımsı */
                color: #ffffff;
                border: 2px solid #ffffff;
            }
        """)

        # Üzerine gelince tooltip
        self.setToolTip(f"Merkez {center_id}")

    def mousePressEvent(self, event):
        if self.map_widget.move_mode_active and event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()
            self.map_widget.setCursor(Qt.ClosedHandCursor)
            self.map_widget.map_label.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.map_widget.move_mode_active and self.dragging and (event.buttons() & Qt.LeftButton):
            # Yeni konumu, parent (map_label) koordinat sistemine göre ayarla
            new_pos = self.pos() + (event.pos() - self.drag_offset)
            parent_rect = self.parent().rect()
            x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
            y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))
            self.move(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.map_widget.move_mode_active and self.dragging and event.button() == Qt.LeftButton:
            self.dragging = False
            # Buton merkez koordinatlarını map_label içinde kaydet
            center_x = self.x() + self.width() // 2
            center_y = self.y() + self.height() // 2
            self.map_widget.update_center_location(self.center_id, center_x, center_y)
            self.map_widget.setCursor(Qt.OpenHandCursor)
            self.map_widget.map_label.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    """Harita üzerindeki merkez butonu (sürükle-bırak destekli)"""
    def __init__(self, center_id, map_widget):
        super().__init__(str(center_id), map_widget.map_label)
        self.center_id = center_id
        self.map_widget = map_widget
        self.setProperty('center_id', center_id)
        self.dragging = False
        self.drag_offset = QPoint()

    def mousePressEvent(self, event):
        if self.map_widget.move_mode_active and event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()
            self.map_widget.setCursor(Qt.ClosedHandCursor)
            self.map_widget.map_label.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.map_widget.move_mode_active and self.dragging and (event.buttons() & Qt.LeftButton):
            # Yeni konumu, parent (map_label) koordinat sistemine göre ayarla
            new_pos = self.pos() + (event.pos() - self.drag_offset)
            parent_rect = self.parent().rect()
            x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
            y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))
            self.move(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.map_widget.move_mode_active and self.dragging and event.button() == Qt.LeftButton:
            self.dragging = False
            # Buton merkez koordinatlarını map_label içinde kaydet
            center_x = self.x() + self.width() // 2
            center_y = self.y() + self.height() // 2
            self.map_widget.update_center_location(self.center_id, center_x, center_y)
            self.map_widget.setCursor(Qt.OpenHandCursor)
            self.map_widget.map_label.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

# ----------------------------------------------------------------------
# 4B. İNTERAKTİF HARİTA WIDGET'I (InteractiveMapWidget)
# ----------------------------------------------------------------------

from PyQt5.QtCore import pyqtSignal

class InteractiveMapWidget(QWidget):
    """Harita görüntüsünü yükleyen ve interaktif merkez noktalarını gösteren Widget"""

    center_selected = pyqtSignal(int)

    def __init__(self, parent=None, total_centers=14, image_path=''):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        self.buttons = {}
        self.selected_center = 1
        self.total_centers = total_centers
        self.image_path = image_path
        self.custom_locations = self.load_locations()  # Kayıtlı konumları yükle
        self.move_mode_active = False  # Taşıma modu aktif mi?

        self.setMouseTracking(True)
        self.setup_ui()
        self.update_map_image(image_path)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignCenter)
        self.map_label.setScaledContents(True)
        layout.addWidget(self.map_label)
        self.setLayout(layout)
        self.setMinimumSize(750, 550)

    def load_locations(self):
        """Kaydedilmiş özel konumları JSON dosyasından yükler."""
        try:
            with open(KONUM_KAYIT_DOSYASI, 'r') as f:
                return {int(k): v for k, v in json.load(f).items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_locations(self):
        """Özel konumları JSON dosyasına kaydeder."""
        try:
            with open(KONUM_KAYIT_DOSYASI, 'w') as f:
                json.dump({str(k): v for k, v in self.custom_locations.items()}, f)
        except Exception:
            pass

    def update_center_location(self, center_id, x, y):
        """Bir merkezin yeni piksel koordinatını kaydet."""
        self.custom_locations[center_id] = [x, y]
        self.save_locations()

    def update_map_image(self, image_path):
        """Harita görselini günceller ve butonları yeniden yerleştirir."""
        self.image_path = image_path
        self.pixmap = QPixmap(image_path)

        if self.pixmap.isNull():
            self.map_label.setText("Harita görseli yüklenemedi. Lütfen Ayarlar sekmesinden yükleyin.")
            self.map_label.clear()
            for btn in self.buttons.values():
                btn.hide()
        else:
            scaled_pixmap = self.pixmap.scaled(self.map_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.map_label.setPixmap(scaled_pixmap)
            self.place_center_buttons()

    def update_center_count(self, new_count):
        """Merkez sayısını günceller ve butonları yönetir."""
        self.total_centers = new_count
        self.place_center_buttons()

    def toggle_move_mode(self):
        """Taşıma modunu açar/kapatır."""
        self.move_mode_active = not self.move_mode_active
        if self.move_mode_active:
            QMessageBox.information(self, "Taşıma Modu", "Taşıma modu aktif (M). Merkez butonlarını harita üzerinde sürükleyip bırakabilirsiniz.")
            self.setCursor(Qt.OpenHandCursor)
            self.map_label.setCursor(Qt.OpenHandCursor)
        else:
            QMessageBox.information(self, "Taşıma Modu", "Taşıma modu kapalı.")
            self.setCursor(Qt.ArrowCursor)
            self.map_label.setCursor(Qt.ArrowCursor)

    def place_center_buttons(self):
        """Merkez butonlarını harita üzerine yerleştirir/günceller."""
        if self.pixmap.isNull():
            map_width = 700
            map_height = 500
        else:
            map_width = max(1, self.map_label.width())
            map_height = max(1, self.map_label.height())

        # --- BUTONLARI OLUŞTUR (SADECE İLK ÇALIŞTIRMADA) ---
        if not self.buttons:
            for center_id in range(1, 15):
                btn = CenterButton(center_id, self)

                btn.setFixedSize(48, 48)      # 40 küçük – 60 büyük → 48 optimum
                font = btn.font()
                font.setPointSize(15)
                font.setBold(True)
                btn.setFont(font)

                btn.setStyleSheet("""
                    QPushButton {
                        border-radius: 24px;               /* 48/2 */
                        border: 2px solid #ffffff;
                        font-weight: bold;
                        font-size: 15px;
                        background-color: rgba(0, 0, 0, 200);
                        color: #ffffff;
                    }
                    QPushButton:hover {
                        border: 2px solid #ffd700;
                    }
                    QPushButton:checked {
                        background-color: rgba(220, 53, 69, 230);
                        color: #ffffff;
                        border: 2px solid #ffffff;
                    }
                """)


                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, c=center_id: self.select_center(c))
                self.buttons[center_id] = btn

        # --- KONUMLANDIRMA KISMI AYNEN DEVAM ---
        for center_id, btn in self.buttons.items():
            location = self.custom_locations.get(center_id, MERKEZ_KONUMLARI.get(center_id))

            if center_id <= self.total_centers and not self.pixmap.isNull() and location:
                if location in MERKEZ_KONUMLARI.values():
                    x_pos = int(map_width * location[0] / 100)
                    y_pos = int(map_height * location[1] / 100)
                else:
                    x_pos, y_pos = location

                btn.move(x_pos - btn.width() // 2, y_pos - btn.height() // 2)
                btn.show()
            else:
                btn.hide()

        if self.selected_center not in self.buttons or self.selected_center > self.total_centers:
            self.selected_center = 1

        if self.selected_center in self.buttons:
            self.buttons[self.selected_center].setChecked(True)

        self.center_selected.emit(self.selected_center)

        """Merkez butonlarını harita üzerine yerleştirir/günceller."""
        if self.pixmap.isNull():
            map_width = 700
            map_height = 500
        else:
            map_width = max(1, self.map_label.width())
            map_height = max(1, self.map_label.height())

        # Butonları oluştur (sadece ilk çalıştırmada)
        if not self.buttons:
            for center_id in range(1, 15):
                btn = CenterButton(center_id, self)
                btn.setFixedSize(40, 40)
                btn.setStyleSheet("""
                    QPushButton {
                        border-radius: 20px;
                        border: 2px solid #000000;
                        font-weight: bold;
                        font-size: 14px;
                        background-color: rgba(255, 255, 0, 220);
                        color: black;
                    }
                    QPushButton:checked {
                        background-color: red;
                        color: white;
                    }
                """)
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, c=center_id: self.select_center(c))
                self.buttons[center_id] = btn

        # Butonları konumlandır ve görünürlüğünü ayarla
        for center_id, btn in self.buttons.items():
            location = self.custom_locations.get(center_id, MERKEZ_KONUMLARI.get(center_id))

            if center_id <= self.total_centers and not self.pixmap.isNull() and location:
                if location in MERKEZ_KONUMLARI.values():
                    # Varsayılan (yüzdesel) konum
                    x_pos = int(map_width * location[0] / 100)
                    y_pos = int(map_height * location[1] / 100)
                else:
                    # Özel (piksel) konum - label koordinat sistemi
                    x_pos, y_pos = location

                # Parent: map_label olduğu için direkt oraya göre yerleştiriyoruz
                btn.move(x_pos - btn.width() // 2, y_pos - btn.height() // 2)
                btn.show()
            else:
                btn.hide()

        if self.selected_center not in self.buttons or self.selected_center > self.total_centers:
            self.selected_center = 1

        if self.selected_center in self.buttons:
            self.buttons[self.selected_center].setChecked(True)

        self.center_selected.emit(self.selected_center)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not self.pixmap.isNull():
            scaled_pixmap = self.pixmap.scaled(self.map_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.map_label.setPixmap(scaled_pixmap)

        self.place_center_buttons()

    def select_center(self, center_id):
        if not self.move_mode_active:  # Taşıma modu kapalıysa seçim yap
            if self.selected_center in self.buttons:
                self.buttons[self.selected_center].setChecked(False)

            self.selected_center = center_id
            if center_id in self.buttons:
                self.buttons[center_id].setChecked(True)

            self.center_selected.emit(center_id)

# ----------------------------------------------------------------------
# 5. ANA UYGULAMA PENCERESİ (OrienteeringSystem)
# ----------------------------------------------------------------------

class OrienteeringSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧭 Oryantiring Takip Sistemi")
        self.setGeometry(100, 100, 1600, 900)

        self.setFocusPolicy(Qt.StrongFocus)

        # Veritabanı
        self.db = DatabaseManager()

        # Seri port
        self.serial_manager = SerialManager()

        # Sistem değişkenleri
        self.center_id = 1
        self.total_centers = 14
        self.last_scanned_rfid = None
        self.harita_yolu = HARITA_IMAGE_PATH

        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Sekmeler
        self.setup_live_tracking_tab()
        self.setup_participant_management_tab()
        self.setup_center_view_tab()
        self.setup_results_tab()
        self.setup_settings_tab()

        # Timer
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.check_rfid)

        self.update_total_centers(self.total_centers)
        self.statusBar().showMessage(f"Sistem Hazır - Yönetici Merkezi: #{self.center_id} | Toplam Merkez: {self.total_centers}")

    def keyPressEvent(self, event):
        """Klavyeden 'M' tuşuna basıldığında taşıma modunu aç/kapat."""
        if event.key() == Qt.Key_M:
            self.map_widget.toggle_move_mode()
            if self.map_widget.move_mode_active:
                self.statusBar().showMessage(f"Taşıma Modu AKTİF (M) | Yeni merkezleri haritada sürükleyin.")
            else:
                self.statusBar().showMessage(f"Sistem Hazır - Yönetici Merkezi: #{self.center_id} | Toplam Merkez: {self.total_centers}")
        super().keyPressEvent(event)

    # --- AYARLAR SEKME FONKSİYONLARI ---

    def setup_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 1. Genel Ayarlar ve Harita Yükleme
        general_group = QGroupBox("⚙️ Genel Ayarlar ve Harita Yönetimi")
        g_layout = QFormLayout()

        self.center_count_spin = QSpinBox()
        self.center_count_spin.setRange(1, len(MERKEZ_KONUMLARI))
        self.center_count_spin.setValue(self.total_centers)
        self.center_count_spin.valueChanged.connect(self.update_total_centers)
        g_layout.addRow(QLabel("Toplam Merkez Sayısı (Max 14):"), self.center_count_spin)

        map_btn = QPushButton("📁 Harita Görseli Yükle (Yüksek Çözünürlüklü Görüntü)")
        map_btn.clicked.connect(self.load_map_image)
        g_layout.addRow(QLabel("Harita Yolu:"), map_btn)

        self.map_status_label = QLabel("Yüklü Değil.")
        g_layout.addRow(QLabel("Durum:"), self.map_status_label)

        general_group.setLayout(g_layout)
        layout.addWidget(general_group)

        # 2. Bağlantı Ayarları Paneli
        connect_group = QGroupBox("📡 Bağlantı Ayarları (Merkez #1 - Yönetici Cihazı)")
        h_layout = QHBoxLayout()

        h_layout.addWidget(QLabel("COM Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        h_layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("🔄 Portları Yenile")
        refresh_btn.clicked.connect(self.refresh_ports)
        h_layout.addWidget(refresh_btn)

        h_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baudrate_combo.setCurrentText("9600")
        h_layout.addWidget(self.baudrate_combo)

        self.connect_btn = QPushButton("Bağlan")
        self.connect_btn.clicked.connect(self.toggle_connection)
        h_layout.addWidget(self.connect_btn)

        self.status_label = QLabel("● Bağlı Değil")
        self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        h_layout.addWidget(self.status_label)

        h_layout.addStretch()
        connect_group.setLayout(h_layout)
        layout.addWidget(connect_group)

        # 3. Seri Port Monitör
        monitor_group = QGroupBox("Seri Port Monitör (RFID Okuma)")
        m_layout = QVBoxLayout()

        self.serial_text = QTextEdit()
        self.serial_text.setReadOnly(True)
        self.serial_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 5px;
            }
        """)
        m_layout.addWidget(self.serial_text)

        clear_btn = QPushButton("🗑 Temizle")
        clear_btn.clicked.connect(self.serial_text.clear)
        m_layout.addWidget(clear_btn)

        monitor_group.setLayout(m_layout)
        layout.addWidget(monitor_group)

        layout.addStretch()
        self.tabs.addTab(tab, "⚙️ Ayarlar & Bağlantı")

    def load_map_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Harita Görseli Seç", "",
                                                   "Görsel Dosyaları (*.png *.jpg *.jpeg *.bmp)", options=options)
        if file_name:
            self.harita_yolu = file_name
            self.map_widget.update_map_image(file_name)
            self.map_status_label.setText(f"Yüklü: {file_name.split('/')[-1]}")
            QMessageBox.information(self, "Harita Yüklendi", f"Harita başarıyla yüklendi: {file_name}")

    def update_total_centers(self, count):
        self.total_centers = count

        self.map_widget.update_center_count(count)

        center_items = [str(i) for i in range(1, self.total_centers + 1)]
        current_manual_center = self.manual_center_combo.currentText()
        current_view_center = self.view_center_combo.currentText()

        self.manual_center_combo.clear()
        self.manual_center_combo.addItems(center_items)
        if current_manual_center in center_items:
            self.manual_center_combo.setCurrentText(current_manual_center)

        self.view_center_combo.clear()
        self.view_center_combo.addItems([f"Merkez {i}" for i in range(1, self.total_centers + 1)])
        if current_view_center in [f"Merkez {i}" for i in range(1, self.total_centers + 1)]:
            self.view_center_combo.setCurrentText(current_view_center)

        self.update_results()
        self.update_center_view()

        self.statusBar().showMessage(f"Sistem Hazır - Yönetici Merkezi: #{self.center_id} | Toplam Merkez: {self.total_centers}")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.serial_manager.get_available_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("Port bulunamadı")

    def toggle_connection(self):
        if not self.serial_manager.is_connected:
            port = self.port_combo.currentText()
            try:
                baudrate = int(self.baudrate_combo.currentText())
            except ValueError:
                QMessageBox.warning(self, "Hata", "Geçersiz Baudrate değeri!")
                return

            if port and port != "Port bulunamadı":
                if self.serial_manager.connect(port, baudrate):
                    self.connect_btn.setText("Bağlantıyı Kes")
                    self.connect_btn.setStyleSheet("background-color: #dc3545; color: white;")
                    self.status_label.setText("● Bağlı")
                    self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
                    self.read_timer.start(100)
                    self.serial_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Bağlantı başarılı: {port} @ {baudrate}")
                else:
                    QMessageBox.warning(self, "Hata", "Bağlantı kurulamadı!")
        else:
            self.serial_manager.disconnect()
            self.connect_btn.setText("Bağlan")
            self.connect_btn.setStyleSheet("")
            self.status_label.setText("● Bağlı Değil")
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            self.read_timer.stop()
            self.serial_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Bağlantı kesildi")

    # --- CANLI TAKİP SEKME FONKSİYONLARI ---

    def setup_live_tracking_tab(self):
        tab = QWidget()
        main_h_layout = QHBoxLayout(tab)

        left_v_layout = QVBoxLayout()
        self.map_widget = InteractiveMapWidget(self, self.total_centers, self.harita_yolu)
        self.map_widget.center_selected.connect(self.select_center_from_map)
        left_v_layout.addWidget(self.map_widget)

        sim_group = QGroupBox("✍️ Manuel Geçiş Kaydı (Merkez Dışı Okumalar)")
        sim_layout = QHBoxLayout()

        sim_layout.addWidget(QLabel("RFID/Yüzük No:"))
        self.manual_rfid_input = QLineEdit()
        self.manual_rfid_input.setPlaceholderText("RFID numarasını girin")
        sim_layout.addWidget(self.manual_rfid_input)

        sim_layout.addWidget(QLabel("Merkez No:"))
        self.manual_center_combo = QComboBox()
        self.manual_center_combo.addItems([str(i) for i in range(1, self.total_centers + 1)])
        self.manual_center_combo.setCurrentText("1")
        sim_layout.addWidget(self.manual_center_combo)

        self.manual_read_btn = QPushButton("➕ Geçişi Kaydet")
        self.manual_read_btn.setObjectName("manual_read_btn")
        self.manual_read_btn.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold;")
        self.manual_read_btn.clicked.connect(self.simulate_manual_read)
        sim_layout.addWidget(self.manual_read_btn)

        self.random_read_btn = QPushButton("🎲 Rastgele Geçiş Ekle (Test)")
        self.random_read_btn.clicked.connect(self.simulate_random_read)
        sim_layout.addWidget(self.random_read_btn)

        sim_group.setLayout(sim_layout)
        left_v_layout.addWidget(sim_group)

        main_h_layout.addLayout(left_v_layout)

        right_v_layout = QVBoxLayout()

        info_group = QGroupBox("📍 Seçilen Merkez Bilgisi ve Son Okuma")
        info_layout = QVBoxLayout()
        self.last_read_label = QLabel("Haritadan bir merkez seçin.")
        self.last_read_label.setFont(QFont("Arial", 14))
        self.last_read_label.setAlignment(Qt.AlignCenter)
        self.last_read_label.setStyleSheet("padding: 25px; background-color: #f8f9fa; border-radius: 8px;")
        info_layout.addWidget(self.last_read_label)
        info_group.setLayout(info_layout)
        right_v_layout.addWidget(info_group)

        self.live_title_label = QLabel("Canlı Geçişler (Merkez #1)")
        self.live_title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.live_title_label.setAlignment(Qt.AlignCenter)
        right_v_layout.addWidget(self.live_title_label)

        self.live_table = QTableWidget()
        self.live_table.setColumnCount(6)
        self.live_table.setHorizontalHeaderLabels(["Zaman", "RFID", "Ad Soyad", "Numara", "Bu Merkez", "Toplam Merkez"])
        self.live_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_v_layout.addWidget(self.live_table)

        main_h_layout.addLayout(right_v_layout)
        self.tabs.addTab(tab, "🗺️ Harita & Canlı Takip")

        self.select_center_from_map(self.center_id)

    def select_center_from_map(self, center_id):
        self.center_id = center_id

        passages = self.db.get_center_passages(center_id)

        if passages:
            last_passage = passages[0]
            participant = self.db.get_participant(last_passage['rfid'])
            p_passages = self.db.get_participant_passages(last_passage['rfid'])
            total_centers = len(p_passages)

            self.last_read_label.setText(
                f"MERKEZ #{center_id} BİLGİSİ\n"
                f"Son Geçen: {participant['name']} ({participant['number']})\n"
                f"Zaman: {last_passage['time'].strftime('%H:%M:%S')}\n"
                f"Toplam Geçiş: {total_centers} farklı merkez"
            )
            self.last_read_label.setStyleSheet("padding: 25px; background-color: #ffe0b2; border-radius: 8px; color: #e65100;")
        else:
            self.last_read_label.setText(f"MERKEZ #{center_id} BİLGİSİ\nBu merkezden henüz geçiş yapılmadı.")
            self.last_read_label.setStyleSheet("padding: 25px; background-color: #f8f9fa; border-radius: 8px;")

        # Canlı tablo başlığını ve içeriğini merkeze göre güncelle
        self.live_title_label.setText(f"Canlı Geçişler (Merkez #{center_id})")
        self.update_live_tracking_for_center(center_id, passages)

    def update_live_tracking_for_center(self, center_id, passages):
        self.live_table.setRowCount(0)

        for passage in passages:
            participant = self.db.get_participant(passage['rfid'])
            p_passages = self.db.get_participant_passages(passage['rfid'])
            center_count = len(p_passages.get(center_id, []))
            total_centers = len(p_passages)

            row = self.live_table.rowCount()
            self.live_table.insertRow(row)

            self.live_table.setItem(row, 0, QTableWidgetItem(passage['time'].strftime('%H:%M:%S')))
            self.live_table.setItem(row, 1, QTableWidgetItem(participant['rfid']))
            self.live_table.setItem(row, 2, QTableWidgetItem(participant['name']))
            self.live_table.setItem(row, 3, QTableWidgetItem(participant['number']))
            self.live_table.setItem(row, 4, QTableWidgetItem(str(center_count)))
            self.live_table.setItem(row, 5, QTableWidgetItem(str(total_centers)))

    # --- DİĞER FONKSİYONLAR ---

    def check_rfid(self):
        rfid_data = self.serial_manager.read_rfid()
        if rfid_data:
            self.serial_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] >> {rfid_data} (Seri Port)")
            self.serial_text.verticalScrollBar().setValue(
                self.serial_text.verticalScrollBar().maximum()
            )
            self.last_scanned_rfid = rfid_data
            # Okuma, şu an seçili merkeze yazılsın
            self.process_rfid(rfid_data, self.center_id)

    def simulate_manual_read(self):
        rfid = self.manual_rfid_input.text().strip()
        center_id = int(self.manual_center_combo.currentText())

        if not rfid:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir RFID/Yüzük Numarası girin!")
            return

        self.serial_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] >> {rfid} (MANUEL Giriş - Merkez {center_id})")
        self.manual_rfid_input.clear()
        self.process_rfid(rfid, center_id)

    def simulate_random_read(self):
        participants = self.db.get_all_participants()
        if not participants:
            QMessageBox.warning(self, "Uyarı", "Önce katılımcı kaydı yapın!")
            return

        random_participant = random.choice(participants)
        rfid = random_participant['rfid']
        center_id = random.randint(1, self.total_centers)

        self.serial_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] >> {rfid} (RASTGELE Test - Merkez {center_id})")
        self.process_rfid(rfid, center_id)

    def process_rfid(self, rfid, center_id):
        participant = self.db.get_participant(rfid)

        if not participant:
            reply = QMessageBox.question(self, 'Katılımcı Bulunamadı',
                                         f'RFID: {rfid}\n\nKatılımcı kaydı oluşturmak ister misiniz?',
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                dialog = ParticipantDialog(self, rfid=rfid)
                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_data()
                    if self.db.add_participant(data['rfid'], data['name'], data['number']):
                        participant = data
                        self.load_participants()
                        QMessageBox.information(self, "Başarılı", "Katılımcı kaydedildi!")
                    else:
                        QMessageBox.warning(self, "Hata", "Katılımcı kaydedilemedi!")
                        return
                else:
                    return
            else:
                return

        timestamp = datetime.now()
        if self.db.add_passage(rfid, center_id, timestamp):
            # Seçili merkezdeki görüntüyü güncelle
            self.select_center_from_map(self.map_widget.selected_center)
            self.load_participants()
            self.update_results()
            self.update_center_view()

            self.serial_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Geçiş kaydedildi: {participant['name']} (Merkez {center_id})")

    # --- DİĞER TABLO YÖNETİM FONKSİYONLARI ---

    def setup_participant_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Yeni Katılımcı")
        add_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px; font-size: 13px;")
        add_btn.clicked.connect(self.add_participant)
        btn_layout.addWidget(add_btn)
        edit_btn = QPushButton("✏️ Düzenle")
        edit_btn.clicked.connect(self.edit_participant)
        btn_layout.addWidget(edit_btn)
        delete_btn = QPushButton("🗑 Sil")
        delete_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 10px;")
        delete_btn.clicked.connect(self.delete_participant)
        btn_layout.addWidget(delete_btn)
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.load_participants)
        btn_layout.addWidget(refresh_btn)
        export_btn = QPushButton("💾 Dışa Aktar")
        export_btn.clicked.connect(self.export_participants)
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.participant_table = QTableWidget()
        self.participant_table.setColumnCount(4)
        self.participant_table.setHorizontalHeaderLabels(["RFID", "Ad Soyad", "Numara", "Toplam Merkez Geçişi"])
        self.participant_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.participant_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.participant_table)

        self.tabs.addTab(tab, "👥 Katılımcılar")
        self.load_participants()

    def setup_center_view_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("İncelenecek Merkez Seç:"))
        self.view_center_combo = QComboBox()
        self.view_center_combo.addItems([f"Merkez {i}" for i in range(1, self.total_centers + 1)])
        self.view_center_combo.currentIndexChanged.connect(self.update_center_view)
        select_layout.addWidget(self.view_center_combo)
        select_layout.addStretch()
        layout.addLayout(select_layout)

        self.center_table = QTableWidget()
        self.center_table.setColumnCount(5)
        self.center_table.setHorizontalHeaderLabels(["Sıra", "RFID", "Ad Soyad", "Numara", "Geçiş Saati"])
        self.center_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.center_table)

        self.tabs.addTab(tab, "📍 Merkez Görünümü")
        self.update_center_view()

    def setup_results_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        filter_group = QGroupBox("Filtreler")
        filter_layout = QHBoxLayout()

        self.completed_only = QCheckBox("Sadece Tamamlayanlar (14 Merkez)")
        self.completed_only.clicked.connect(self.update_results)
        filter_layout.addWidget(self.completed_only)

        update_btn = QPushButton("🔄 Güncelle")
        update_btn.clicked.connect(self.update_results)
        filter_layout.addWidget(update_btn)

        export_btn = QPushButton("💾 Sonuçları Dışa Aktar")
        export_btn.clicked.connect(self.export_results)
        filter_layout.addWidget(export_btn)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Sıra", "Ad Soyad", "Numara", "Tamamlanan Merkez", "Son Geçiş"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)

        self.tabs.addTab(tab, "🏆 Sonuçlar")
        self.update_results()

    def update_center_view(self):
        current_index = self.view_center_combo.currentIndex()
        if current_index == -1:
            return

        center_idx = current_index + 1
        self.center_table.setRowCount(0)

        passages = self.db.get_center_passages(center_idx)

        for idx, passage in enumerate(passages, 1):
            row = self.center_table.rowCount()
            self.center_table.insertRow(row)

            self.center_table.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.center_table.setItem(row, 1, QTableWidgetItem(passage['rfid']))
            self.center_table.setItem(row, 2, QTableWidgetItem(passage['name']))
            self.center_table.setItem(row, 3, QTableWidgetItem(passage['number']))
            self.center_table.setItem(row, 4, QTableWidgetItem(passage['time'].strftime('%H:%M:%S')))

    def load_participants(self):
        self.participant_table.setRowCount(0)
        participants = self.db.get_all_participants()

        for participant in participants:
            row = self.participant_table.rowCount()
            self.participant_table.insertRow(row)

            passages = self.db.get_participant_passages(participant['rfid'])
            total_centers = len(passages)

            self.participant_table.setItem(row, 0, QTableWidgetItem(participant['rfid']))
            self.participant_table.setItem(row, 1, QTableWidgetItem(participant['name']))
            self.participant_table.setItem(row, 2, QTableWidgetItem(participant['number']))
            self.participant_table.setItem(row, 3, QTableWidgetItem(str(total_centers)))

    def update_results(self):
        self.results_table.setRowCount(0)

        completed_only = self.completed_only.isChecked()
        results = self.db.get_all_results(completed_only=completed_only, total_centers=self.total_centers)

        for idx, result in enumerate(results, 1):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            self.results_table.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.results_table.setItem(row, 1, QTableWidgetItem(result['name']))
            self.results_table.setItem(row, 2, QTableWidgetItem(result['number']))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{result['completed']}/{self.total_centers}"))

            last_time_str = result['last_time'].strftime('%H:%M:%S') if result['last_time'] else "-"
            self.results_table.setItem(row, 4, QTableWidgetItem(last_time_str))

            if result['completed'] == self.total_centers:
                for col in range(5):
                    self.results_table.item(row, col).setBackground(QColor(212, 237, 218))

    def add_participant(self):
        dialog = ParticipantDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if self.db.add_participant(data['rfid'], data['name'], data['number']):
                self.load_participants()
                self.update_results()
                QMessageBox.information(self, "Başarılı", "Katılımcı eklendi!")
            else:
                QMessageBox.warning(self, "Hata", "Bu RFID zaten kayıtlı veya bir hata oluştu!")

    def edit_participant(self):
        selected = self.participant_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek katılımcıyı seçin!")
            return

        row = selected[0].row()
        rfid = self.participant_table.item(row, 0).text()
        name = self.participant_table.item(row, 1).text()
        number = self.participant_table.item(row, 2).text()

        dialog = ParticipantDialog(self, rfid, name, number)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if self.db.update_participant(data['rfid'], data['name'], data['number']):
                self.load_participants()
                self.update_results()
                self.update_center_view()
                QMessageBox.information(self, "Başarılı", "Katılımcı güncellendi!")
            else:
                QMessageBox.warning(self, "Hata", "Güncelleme başarısız!")

    def delete_participant(self):
        selected = self.participant_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek katılımcıyı seçin!")
            return

        row = selected[0].row()
        rfid = self.participant_table.item(row, 0).text()
        name = self.participant_table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            'Silme Onayı',
            f'{name} isimli katılımcıyı ve tüm geçiş kayıtlarını silmek istediğinizden emin misiniz?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.db.delete_participant(rfid):
                self.load_participants()
                self.update_results()
                self.update_center_view()
                self.live_table.setRowCount(0)
                QMessageBox.information(self, "Başarılı", "Katılımcı silindi!")
            else:
                QMessageBox.warning(self, "Hata", "Silme işlemi başarısız!")

    def export_participants(self):
        try:
            filename = f"katilimcilar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            participants = self.db.get_all_participants()

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['RFID', 'Ad Soyad', 'Numara', 'Toplam Merkez Geçişi'])

                for p in participants:
                    passages = self.db.get_participant_passages(p['rfid'])
                    writer.writerow([p['rfid'], p['name'], p['number'], len(passages)])

            QMessageBox.information(self, "Başarılı", f"Veriler {filename} dosyasına aktarıldı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma hatası: {e}")

    def export_results(self):
        try:
            filename = f"sonuclar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            results = self.db.get_all_results()

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Sıra', 'Ad Soyad', 'Numara', 'RFID', 'Tamamlanan Merkez', 'Son Geçiş Zamanı'])

                for idx, result in enumerate(results, 1):
                    last_time_str = result['last_time'].strftime('%Y-%m-%d %H:%M:%S') if result['last_time'] else "-"
                    writer.writerow([
                        idx,
                        result['name'],
                        result['number'],
                        result['rfid'],
                        f"{result['completed']}/{self.total_centers}",
                        last_time_str
                    ])

            QMessageBox.information(self, "Başarılı", f"Sonuçlar {filename} dosyasına aktarıldı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma hatası: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Uygulama stili
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 6px;
            margin-top: 6px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            padding: 8px 15px;
            border-radius: 4px;
            font-size: 12px;
        }
        QPushButton:hover {
            opacity: 0.9;
        }
        #manual_read_btn {
             background-color: #ffc107;
             color: black;
        }
        #manual_read_btn:hover {
             background-color: #e0ac00;
        }
        QTableWidget {
            border: 1px solid #ddd;
            gridline-color: #e0e0e0;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #007bff;
            color: white;
        }
        QHeaderView::section {
            background-color: #f8f9fa;
            padding: 8px;
            border: 1px solid #dee2e6;
            font-weight: bold;
        }
    """)

    window = OrienteeringSystem()
    window.show()
    sys.exit(app.exec_())
