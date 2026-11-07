import sys
import os
import tempfile
import random
import sqlite3
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import folium
from folium.features import DivIcon
import matplotlib.pyplot as plt
from io import BytesIO
import base64

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QTextEdit, QLabel, QTabWidget, QComboBox, QFormLayout, QLineEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QSpinBox, QCheckBox, QHeaderView, QFileDialog, QProgressBar, QInputDialog, QMenu, QAction
)
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtGui import QFont, QPixmap

# ==========================
#   SABİTLER
# ==========================

MAP_CENTER = (40.9165, 41.0560)
DB_PATH = "rescue_system_pro_full.db"

# ==========================
#   SQLITE VERİTABANI
# ==========================

class RescueDatabase:
    """Veritabanı işlemlerini yönetir: sporcular, merkezler, personel, parkurlar"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        """Veritabanı bağlantısı oluşturur"""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Veritabanı tablolarını oluşturur ve varsayılan verileri ekler"""
        conn = self._connect()
        cur = conn.cursor()
        
        # Sporcular tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS athletes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                device_id TEXT,
                phone TEXT,
                age INTEGER,
                blood_type TEXT,
                medical_info TEXT,
                emergency_contact TEXT,
                speed REAL DEFAULT 0.001,
                direction REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Merkezler tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                type TEXT NOT NULL,
                capacity INTEGER,
                contact_phone TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Personel tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS personnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                center_id INTEGER,
                role TEXT NOT NULL,
                phone TEXT,
                specialty TEXT,
                is_available BOOLEAN DEFAULT 1,
                FOREIGN KEY (center_id) REFERENCES centers (id)
            )
        """)
        
        # --- YENİ: Parkur Grupları Tablosu ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS course_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Parkur işaretleri tablosu (group_id ile güncellendi)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS course_markers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                description TEXT,
                group_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Hareket geçmişi tablosu
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movement_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                athlete_id INTEGER,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (athlete_id) REFERENCES athletes (id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        self._update_table_schema()
        self._insert_default_data()

    def _update_table_schema(self):
        """Mevcut tablo şemasını günceller - speed, direction ve group_id ekler"""
        conn = self._connect()
        cur = conn.cursor()
        
        try:
            # Sporcular tablosu kontrolü
            cur.execute("PRAGMA table_info(athletes)")
            columns = [column[1] for column in cur.fetchall()]
            
            if 'speed' not in columns:
                cur.execute("ALTER TABLE athletes ADD COLUMN speed REAL DEFAULT 0.001")
            
            if 'direction' not in columns:
                cur.execute("ALTER TABLE athletes ADD COLUMN direction REAL DEFAULT 0")

            # Parkur tablosu kontrolü
            cur.execute("PRAGMA table_info(course_markers)")
            cols = [c[1] for c in cur.fetchall()]
            if 'group_id' not in cols:
                cur.execute("ALTER TABLE course_markers ADD COLUMN group_id INTEGER DEFAULT 1")
                
        except sqlite3.Error as e:
            print(f"Tablo güncelleme hatası: {e}")
        finally:
            conn.commit()
            conn.close()

    def _insert_default_data(self):
        """Varsayılan verileri ekler"""
        conn = self._connect()
        cur = conn.cursor()
        
        # Varsayılan Parkur Grubu
        cur.execute("INSERT OR IGNORE INTO course_groups (id, name) VALUES (1, 'Ana Parkur')")

        # Sporcu kontrolü
        cur.execute("SELECT COUNT(*) FROM athletes")
        if cur.fetchone()[0] == 0:
            default_athletes = [
                ("Sporcu 1", 40.9165, 41.0560, "DEV001", "555-0101", 25, "A+", "Alerji: Penisilin", "Ahmet Yılmaz - 555-0202", 0.0005, 45),
                ("Sporcu 2", 40.9120, 41.0450, "DEV002", "555-0102", 32, "0+", "Hipertansiyon", "Mehmet Demir - 555-0203", 0.0003, 120),
                ("Sporcu 3", 40.9205, 41.0650, "DEV003", "555-0103", 28, "B+", "Astım", "Ayşe Kaya - 555-0204", 0.0004, 300),
            ]
            cur.executemany(
                "INSERT INTO athletes (name, lat, lon, device_id, phone, age, blood_type, medical_info, emergency_contact, speed, direction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                default_athletes,
            )

        # Merkez kontrolü
        cur.execute("SELECT COUNT(*) FROM centers")
        if cur.fetchone()[0] == 0:
            default_centers = [
                ("Ana Kurtarma Merkezi", 40.9150, 41.0550, "rescue", 50, "555-1001", "Ana operasyon merkezi"),
                ("Yamaç İstasyonu", 40.9050, 41.0650, "base", 20, "555-1002", "Yamaç gözlem istasyonu"),
                ("Medikal Merkez", 40.9250, 41.0450, "medical", 10, "555-1003", "Acil sağlık hizmetleri"),
            ]
            cur.executemany(
                "INSERT INTO centers (name, lat, lon, type, capacity, contact_phone, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                default_centers,
            )

        # Personel kontrolü
        cur.execute("SELECT COUNT(*) FROM personnel")
        if cur.fetchone()[0] == 0:
            default_personnel = [
                ("Ali Yıldız", 1, "Operasyon Lideri", "555-2001", "Dağ Kurtarma", 1),
                ("Zeynep Kaya", 1, "Koordinatör", "555-2002", "İletişim", 1),
                ("Mehmet Şen", 2, "Gözlemci", "555-2003", "Meteoroloji", 1),
                ("Dr. Ayşe Demir", 3, "Doktor", "555-2004", "Acil Tıp", 1),
            ]
            cur.executemany(
                "INSERT INTO personnel (name, center_id, role, phone, specialty, is_available) VALUES (?, ?, ?, ?, ?, ?)",
                default_personnel,
            )
        
        conn.commit()
        conn.close()

    # Sporcu işlemleri
    def get_all_athletes(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM athletes ORDER BY name")
        athletes = [dict(row) for row in cur.fetchall()]
        conn.close()
        return athletes

    def update_athlete_position(self, athlete_id: int, lat: float, lon: float):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE athletes SET lat=?, lon=? WHERE id=?", (lat, lon, athlete_id))
        cur.execute("INSERT INTO movement_history (athlete_id, lat, lon) VALUES (?, ?, ?)", (athlete_id, lat, lon))
        conn.commit()
        conn.close()

    def add_athlete(self, athlete_data: Dict[str, Any]):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO athletes (name, lat, lon, device_id, phone, age, blood_type, medical_info, emergency_contact, speed, direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                athlete_data['name'], athlete_data['lat'], athlete_data['lon'],
                athlete_data.get('device_id', ''), athlete_data.get('phone', ''),
                athlete_data.get('age', 0), athlete_data.get('blood_type', ''),
                athlete_data.get('medical_info', ''), athlete_data.get('emergency_contact', ''),
                athlete_data.get('speed', 0.001), athlete_data.get('direction', 0)
            )
        )
        conn.commit()
        conn.close()

    def update_athlete(self, athlete_id: int, athlete_data: Dict[str, Any]):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE athletes 
            SET name=?, lat=?, lon=?, device_id=?, phone=?, age=?, blood_type=?, medical_info=?, emergency_contact=?, speed=?, direction=?
            WHERE id=?
            """,
            (
                athlete_data['name'], athlete_data['lat'], athlete_data['lon'],
                athlete_data.get('device_id', ''), athlete_data.get('phone', ''),
                athlete_data.get('age', 0), athlete_data.get('blood_type', ''),
                athlete_data.get('medical_info', ''), athlete_data.get('emergency_contact', ''),
                athlete_data.get('speed', 0.001), athlete_data.get('direction', 0),
                athlete_id
            )
        )
        conn.commit()
        conn.close()

    def delete_athlete(self, athlete_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM athletes WHERE id=?", (athlete_id,))
        conn.commit()
        conn.close()

    # --- PARKUR VE GRUP İŞLEMLERİ (YENİ) ---
    def add_course_group(self, name: str):
        conn = self._connect()
        try:
            conn.execute("INSERT INTO course_groups (name) VALUES (?)", (name,))
            conn.commit()
        except: pass
        conn.close()

    def get_course_groups(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM course_groups ORDER BY id")
        groups = [dict(row) for row in cur.fetchall()]
        conn.close()
        return groups

    def save_course_marker(self, marker_type: str, lat: float, lon: float, description: str, group_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO course_markers (type, lat, lon, description, group_id) VALUES (?, ?, ?, ?, ?)",
            (marker_type, lat, lon, description, group_id)
        )
        conn.commit()
        conn.close()

    def get_course_markers_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM course_markers WHERE group_id=? ORDER BY id", (group_id,))
        markers = [dict(row) for row in cur.fetchall()]
        conn.close()
        return markers
    
    # Geriye dönük uyumluluk
    def get_course_markers(self):
        return self.get_course_markers_by_group(1)

    def clear_course_markers(self, group_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM course_markers WHERE group_id=?", (group_id,))
        conn.commit()
        conn.close()

    def delete_marker(self, marker_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM course_markers WHERE id=?", (marker_id,))
        conn.commit()
        conn.close()

    def update_marker_position(self, marker_id: int, lat: float, lon: float):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE course_markers SET lat=?, lon=? WHERE id=?", (lat, lon, marker_id))
        conn.commit()
        conn.close()

    # Diğer metodlar
    def get_all_centers(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM centers ORDER BY name")
        centers = [dict(row) for row in cur.fetchall()]
        conn.close()
        return centers

    def add_center(self, center_data: Dict[str, Any]):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO centers (name, lat, lon, type, capacity, contact_phone, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                center_data['name'], center_data['lat'], center_data['lon'],
                center_data['type'], center_data.get('capacity', 0),
                center_data.get('contact_phone', ''), center_data.get('description', '')
            )
        )
        conn.commit()
        conn.close()

    def delete_center(self, center_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM centers WHERE id=?", (center_id,))
        conn.commit()
        conn.close()

    def update_center_position(self, center_id: int, lat: float, lon: float):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE centers SET lat=?, lon=? WHERE id=?", (lat, lon, center_id))
        conn.commit()
        conn.close()

    def get_personnel_by_center(self, center_id: int) -> List[Dict[str, Any]]:
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM personnel WHERE center_id=? ORDER BY name", (center_id,))
        personnel = [dict(row) for row in cur.fetchall()]
        conn.close()
        return personnel

    def add_personnel(self, personnel_data: Dict[str, Any]):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO personnel (name, center_id, role, phone, specialty, is_available)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                personnel_data['name'], personnel_data['center_id'],
                personnel_data['role'], personnel_data.get('phone', ''),
                personnel_data.get('specialty', ''), personnel_data.get('is_available', True)
            )
        )
        conn.commit()
        conn.close()

    def delete_personnel(self, personnel_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM personnel WHERE id=?", (personnel_id,))
        conn.commit()
        conn.close()

# ==========================
#   HARİTA YÖNETİMİ
# ==========================

class MapManager:
    """Harita oluşturma ve yönetim işlemlerini gerçekleştirir"""

    def __init__(self, database: RescueDatabase):
        self.db = database
        self.map_center = MAP_CENTER
        self.current_tile_key = "OpenStreetMap"

        # Harita Ayarları - 3 Farklı Harita Tipi
        self.tiles_config = {
            "OpenStreetMap": {
                "tiles": "OpenStreetMap",
                "attr": None
            },
            "Satellite": {
                "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "attr": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
            },
            "Terrain": {
                "tiles": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                "attr": "Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)"
            }
        }

    def change_tile(self, tile_name: str):
        if tile_name in self.tiles_config:
            self.current_tile_key = tile_name
        else:
            print(f"Uyarı: '{tile_name}' bulunamadı, OpenStreetMap kullanılıyor.")
            self.current_tile_key = "OpenStreetMap"

    def create_map(self, show_trails: bool = False, active_group_id: int = None, draw_lines: bool = True) -> str:
        """
        Sporcular, merkezler ve parkur işaretleri ile interaktif harita oluşturur
        """
        config = self.tiles_config.get(self.current_tile_key, self.tiles_config["OpenStreetMap"])

        fmap = folium.Map(
            location=self.map_center,
            zoom_start=13,
            tiles=config["tiles"],
            attr=config["attr"],
            control_scale=True,
        )

        # ---------- SPORCULAR (Hareketli, Sürüklenemez) ----------
        athletes = self.db.get_all_athletes()
        for athlete in athletes:
            popup_text = (
                f"<b>🏃 {athlete['name']}</b><br>"
                f"📍 Lat: {athlete['lat']:.5f}<br>"
                f"📍 Lon: {athlete['lon']:.5f}<br>"
                f"📱 Cihaz: {athlete.get('device_id', 'N/A')}<br>"
                f"📞 Tel: {athlete.get('phone', 'N/A')}<br>"
                f"🩸 Kan Grubu: {athlete.get('blood_type', 'N/A')}<br>"
                f"🏥 Tıbbi Bilgi: {athlete.get('medical_info', 'N/A')}<br>"
                f"🏃‍♂️ Hız: {athlete.get('speed', 0):.5f}<br>"
                f"🧭 Yön: {athlete.get('direction', 0):.1f}°"
            )
            # Title ID'yi JS'e göndermek için kullanıyoruz
            folium.Marker(
                location=(athlete["lat"], athlete["lon"]),
                popup=popup_text,
                tooltip=f"🏃 {athlete['name']}",
                title=str(athlete['id']),
                icon=folium.Icon(color="red", icon="user", prefix="fa"),
            ).add_to(fmap)

        # ---------- MERKEZLER (Sürüklenebilir) ----------
        center_icons = {
            "rescue": ("blue", "flag", "🚑 Kurtarma"),
            "base": ("green", "home", "🏔️ İstasyon"),
            "medical": ("orange", "plus", "🏥 Medikal")
        }

        centers = self.db.get_all_centers()
        for center in centers:
            color, icon, prefix = center_icons.get(center['type'], ("gray", "info-sign", "Merkez"))
            popup_text = (
                f"<b>{prefix} - {center['name']}</b><br>"
                f"📍 Lat: {center['lat']:.5f}<br>"
                f"📍 Lon: {center['lon']:.5f}<br>"
                f"📞 Tel: {center.get('contact_phone', 'N/A')}<br>"
                f"👥 Kapasite: {center.get('capacity', 'N/A')}<br>"
                f"📝 Açıklama: {center.get('description', 'N/A')}"
            )
            folium.Marker(
                location=(center["lat"], center["lon"]),
                popup=popup_text,
                # Tooltip formatı: CENTER:ID:NAME
                tooltip=f"CENTER:{center['id']}:{center['name']}",
                icon=folium.Icon(color=color, icon=icon),
                draggable=True
            ).add_to(fmap)

        # ---------- PARKUR İŞARETLERİ (Gruba Göre, Sürüklenebilir) ----------
        if active_group_id is None:
            groups = self.db.get_course_groups()
            if groups:
                active_group_id = groups[0]['id']
        
        if active_group_id:
            course_markers = self.db.get_course_markers_by_group(active_group_id)
            marker_types = {
                "start": ("green", "play", "🎯 Başlangıç"),
                "finish": ("red", "stop", "🏁 Bitiş"),
                "drum": ("orange", "record", "🚧 Duba"),
                "checkpoint": ("purple", "flag", "📍 Kontrol Noktası")
            }
            
            points = []
            for marker in course_markers:
                points.append([marker['lat'], marker['lon']])
                color, icon, prefix = marker_types.get(marker['type'], ("gray", "info-sign", "İşaret"))
                
                folium.Marker(
                    location=(marker["lat"], marker["lon"]),
                    popup=f"<b>{prefix}</b><br>{marker.get('description', '')}",
                    # Tooltip formatı: MARKER:ID:TYPE
                    tooltip=f"MARKER:{marker['id']}:{marker['type']}",
                    icon=folium.Icon(color=color, icon=icon),
                    draggable=True
                ).add_to(fmap)

            # Çizgileri çiz (kullanıcı seçeneğine bağlı)
            if draw_lines and len(points) > 1:
                folium.PolyLine(
                    points, color="blue", weight=3, opacity=0.7, popup="Parkur Güzergahı"
                ).add_to(fmap)

        # Hareket izleri
        if show_trails:
            self._add_movement_trails(fmap, athletes)

        # Haritayı kaydet
        tmp_dir = tempfile.gettempdir()
        map_path = os.path.join(tmp_dir, "kackar_harita.html")
        fmap.save(map_path)
        
        # JS Enjeksiyonu (Sürükle-Bırak ve Canlı Takip)
        self._inject_smart_js(map_path)
        
        return map_path

    def _inject_smart_js(self, map_path):
        """HTML dosyasına Marker güncelleme ve sürükleme scriptlerini ekler"""
        js_code = """
        <script>
        // Marker ID'si (1, 2, 3...) ile sıralama yapmak için yardımcı fonksiyon
        function getMarkerId(layer) {
            var content = layer.getTooltip().getContent(); // "MARKER:5:start"
            if (content.startsWith("MARKER:")) {
                return parseInt(content.split(":")[1]);
            }
            return -1;
        }
        
        // 1. Simülasyon için Python'dan çağrılır
        function updateMarkerPosition(id, lat, lon) {
            var mapInstance = null;
            for(var key in window) { if (window[key] instanceof L.Map) { mapInstance = window[key]; break; } }
            if(!mapInstance) return;

            mapInstance.eachLayer(function(layer) {
                if(layer instanceof L.Marker && layer.options.title === id.toString()) {
                    var newLatLng = new L.LatLng(lat, lon);
                    layer.setLatLng(newLatLng);
                }
            });
        }

        // 2. Sürükle-Bırak Dinleyicisi
        document.addEventListener("DOMContentLoaded", function() {
            setTimeout(function() {
                var map = null;
                for(var k in window) { if(window[k] instanceof L.Map) { map = window[k]; break; } }
                if(!map) return;

                var polyline = null;
                // Haritadaki Polyline'ı bul (İlk bulduğunu parkur çizgisi varsayıyoruz)
                map.eachLayer(function(l) { if(l instanceof L.Polyline && !(l instanceof L.Polygon)) polyline = l; });

                map.eachLayer(function(layer) {
                    if(layer instanceof L.Marker && layer.dragging) {
                        
                        // DRAG END: Veritabanı güncellemesi için Python'a sinyal
                        layer.on('dragend', function(e) {
                            var lat = e.target.getLatLng().lat;
                            var lng = e.target.getLatLng().lng;
                            var tooltip = e.target.getTooltip();
                            if (tooltip) {
                                console.log("DRAG_UPDATE|" + tooltip.getContent() + "|" + lat + "|" + lng);
                            }
                        });

                        // DRAG: Çizgiyi anlık güncelle (Lastik efekti)
                        layer.on('drag', function(e) {
                            if(!polyline) return;
                            
                            // Tüm markerları topla
                            var markers = [];
                            map.eachLayer(function(l) {
                                if(l instanceof L.Marker && l.getTooltip()) {
                                    var mid = getMarkerId(l);
                                    if(mid > 0) {
                                        markers.push({id: mid, latlng: l.getLatLng()});
                                    }
                                }
                            });

                            // ID'ye göre sırala (Çizginin doğru sırayla çizilmesi için)
                            markers.sort(function(a, b) { return a.id - b.id; });

                            // Yeni koordinatları çıkar
                            var latlngs = markers.map(function(m) { return m.latlng; });
                            
                            // Çizgiyi güncelle
                            polyline.setLatLngs(latlngs);
                        });
                    }
                });
            }, 1500); // Harita tam yüklensin diye bekle
        });
        </script>
        """
        with open(map_path, "a", encoding="utf-8") as f:
            f.write(js_code)

    def _add_movement_trails(self, fmap, athletes):
        """Sporcuların hareket izlerini haritaya ekler"""
        conn = self.db._connect()
        cur = conn.cursor()

        for athlete in athletes:
            cur.execute(
                "SELECT lat, lon FROM movement_history WHERE athlete_id=? "
                "ORDER BY timestamp DESC LIMIT 10",
                (athlete['id'],)
            )
            points = cur.fetchall()
            if len(points) > 1:
                folium.PolyLine(
                    points,
                    color="red",
                    weight=2,
                    opacity=0.5,
                    popup=f"{athlete['name']} Hareket İzi"
                ).add_to(fmap)

        conn.close()

    def export_to_png(self, map_html_path: str, output_path: str):
        """
        Haritayı PNG formatında kaydeder (basit scatter/çizgi grafiği)
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))

            athletes = self.db.get_all_athletes()
            centers = self.db.get_all_centers()
            markers = self.db.get_course_markers()

            # Sporcuları çiz
            for athlete in athletes:
                ax.plot(athlete['lon'], athlete['lat'], 'ro', markersize=8, label='Sporcu')
                ax.text(athlete['lon'] + 0.0005, athlete['lat'], athlete['name'], fontsize=8)

            # Merkezleri çiz
            for center in centers:
                ax.plot(center['lon'], center['lat'], 'bs', markersize=8, label='Merkez')
                ax.text(center['lon'] + 0.0005, center['lat'], center['name'], fontsize=8)

            # Parkur işaretlerini çiz
            for marker in markers:
                ax.plot(marker['lon'], marker['lat'], 'g^', markersize=8, label='İşaret')

            # Parkur çizgisi
            if len(markers) > 1:
                lats = [m['lat'] for m in markers]
                lons = [m['lon'] for m in markers]
                ax.plot(lons, lats, 'b-', alpha=0.5, linewidth=2)

            ax.set_title("Kaçkar Dağları - Arama Kurtarma Haritası")
            ax.set_xlabel("Boylam")
            ax.set_ylabel("Enlem")
            ax.grid(True, alpha=0.3)

            # Tekrarlanan etiketleri kaldır
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys())

            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            return True
        except Exception as e:
            print(f"❌ PNG kaydetme hatası: {e}")
            return False

# ===================================
#   CİHAZ / SİMÜLASYON VERİ FONKSİYONU
# ===================================

def get_device_data_for_athlete(athlete: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sporcu cihazından simüle edilmiş verileri okur
    """
    temperature = round(random.uniform(35.5, 39.5), 1)
    altitude = random.randint(1800, 3200)
    emergency_flag = random.choice([0, 0, 0, 1])
    battery = random.randint(20, 100)
    heart_rate = random.randint(60, 180)
    oxygen_saturation = random.randint(85, 99)

    data = {
        "athlete_id": athlete["id"],
        "name": athlete["name"],
        "lat": athlete["lat"],
        "lon": athlete["lon"],
        "temperature": temperature,
        "altitude": altitude,
        "emergency": bool(emergency_flag),
        "battery": battery,
        "heart_rate": heart_rate,
        "oxygen_saturation": oxygen_saturation,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    return data

def simulate_movement(athlete: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Sporcunun hareketini simüle eder ve yeni konumu döndürür
    """
    speed = athlete.get('speed', 0.001)
    direction = athlete.get('direction', 0)
    
    # Rastgele küçük yön değişiklikleri
    direction += random.uniform(-15, 15)
    direction %= 360
    
    # Yeni konumu hesapla
    lat_change = speed * math.cos(math.radians(direction))
    lon_change = speed * math.sin(math.radians(direction))
    
    new_lat = athlete['lat'] + lat_change
    new_lon = athlete['lon'] + lon_change
    
    # Konumu Kaçkar bölgesi içinde tut (Genişletildi)
    new_lat = max(40.80, min(41.00, new_lat))
    new_lon = max(41.00, min(41.15, new_lon))
    
    return new_lat, new_lon, direction

# ==========================
#   ÖZEL WEB SAYFASI (JS LOG YAKALAYICI)
# ==========================
class CustomWebEnginePage(QWebEnginePage):
    """JS Konsol mesajlarını yakalar (Sürükleme işlemi için kritik)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Mesaj formatı: DRAG_UPDATE|MARKER:5:start|40.12|41.34
        if message.startswith("DRAG_UPDATE"):
            try:
                parts = message.split("|")
                info = parts[1]
                lat = float(parts[2])
                lon = float(parts[3])
                self.parent_window.handle_drag_update(info, lat, lon)
            except Exception as e:
                print(f"Drag Error: {e}")

# ==========================
#   ANA UYGULAMA
# ==========================

class ModernMainWindow(QMainWindow):
    """Ana uygulama penceresi ve kullanıcı arayüzü"""
    
    def __init__(self):
        super().__init__()
        self.db = RescueDatabase()
        self.map_manager = MapManager(self.db)
        self.athletes = self.db.get_all_athletes()
        self.centers = self.db.get_all_centers()
        self.current_edit_id = None
        self.current_center_id = None
        self.is_movement_active = False
        self.movement_timer = QTimer()
        self.show_trails = False
        self.draw_lines = True
        
        self._init_ui()
        self._setup_timers()
        self.reload_data()

    def _create_styled_button(self, text: str, color: str) -> QPushButton:
        """Stilize edilmiş buton oluşturur"""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
        """)
        return btn
    
    def _get_button_style(self, color: str) -> str:
        """Buton stili döndürür (String olarak)"""
        return f"""
            QPushButton {{
                background-color: {color}; color: white; border: none;
                border-radius: 6px; padding: 8px 12px; font-weight: bold; min-height: 20px;
            }}
            QPushButton:hover {{ background-color: {self._darken_color(color)}; }}
        """

    def _darken_color(self, color: str) -> str:
        """Rengi koyulaştırır"""
        colors = {
            "#3498DB": "#2980B9", "#27AE60": "#219653", "#E74C3C": "#C0392B",
            "#F39C12": "#D35400", "#95A5A6": "#7F8C8D", "#9B59B6": "#8E44AD"
        }
        return colors.get(color, color)

    def _init_ui(self):
        """Kullanıcı arayüzünü başlatır"""
        self.setWindowTitle("🏔️ Kaçkar Dağları - İleri Arama Kurtarma Sistemi")
        self.resize(1400, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f6fa; }
            QTabWidget::pane {
                border: 1px solid #C2C7CB; background-color: white; border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #E1E8ED; padding: 8px 16px; margin-right: 2px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
            }
            QTabBar::tab:selected { background-color: #3498DB; color: white; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # SOL: HARİTA
        self.webview = QWebEngineView()
        # Özel sayfa yapısını ata (JS logları için)
        self.custom_page = CustomWebEnginePage(self)
        self.webview.setPage(self.custom_page)
        self.webview.setMinimumWidth(800)
        main_layout.addWidget(self.webview, stretch=3)

        # SAĞ: TABS
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=2)

        title_label = QLabel("🏔️ Arama Kurtarma Sistemi")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px; font-weight: bold; padding: 12px; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498DB, stop:1 #2C3E50);
            color: white; border-radius: 8px; margin-bottom: 10px;
        """)
        right_panel.addWidget(title_label)

        self.tabs = QTabWidget()
        right_panel.addWidget(self.tabs)

        # SEKME SIRALAMASI
        self._init_control_tab()      # Operasyon
        self._init_settings_tab()     # Ayarlar (YENİ)
        self._init_course_tab()       # Parkur (YENİLENMİŞ)
        self._init_athletes_tab()     # Sporcular
        self._init_centers_tab()      # Merkezler
        self._init_personnel_tab()    # Personel

    # ---------------------------------------------------------
    # 1. KONTROL SEKMESİ (OPERASYON)
    # ---------------------------------------------------------
    def _init_control_tab(self):
        """Kontrol sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Sporcu İşlemleri
        athlete_group = QGroupBox("🏃 Sporcu İşlemleri")
        athlete_layout = QVBoxLayout(athlete_group)
        
        form_layout = QFormLayout()
        self.combo_athletes = QComboBox()
        self.btn_athlete_details = self._create_styled_button("📋 Sporcu Detayları", "#95A5A6")
        self.btn_athlete_details.clicked.connect(self.show_athlete_details)
        form_layout.addRow("Sporcu Seç:", self.combo_athletes)
        form_layout.addRow("", self.btn_athlete_details)
        athlete_layout.addLayout(form_layout)

        self.btn_get_data = self._create_styled_button("📡 Seçili Sporcu Verilerini Al", "#3498DB")
        self.btn_get_data.clicked.connect(self.handle_single_athlete)
        self.btn_scan_all = self._create_styled_button("🔄 Tüm Sporcuları Tara", "#27AE60")
        self.btn_scan_all.clicked.connect(self.handle_scan_all)
        self.btn_show_emergencies = self._create_styled_button("🚨 Acil Durumları Tara", "#E74C3C")
        self.btn_show_emergencies.clicked.connect(self.handle_show_emergencies)
        self.btn_refresh_map = self._create_styled_button("🗺️ Haritayı Yenile", "#F39C12")
        self.btn_refresh_map.clicked.connect(self.reload_map)

        for btn in [self.btn_get_data, self.btn_scan_all, self.btn_show_emergencies, self.btn_refresh_map]:
            athlete_layout.addWidget(btn)

        layout.addWidget(athlete_group)

        # Log Alanı
        log_group = QGroupBox("📝 Sistem Logları")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2C3E50; color: #ECF0F1; border: 1px solid #34495E;
                border-radius: 4px; padding: 8px; font-family: 'Courier New'; font-size: 10pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        self.tabs.addTab(widget, "🎮 Kontrol")

    # ---------------------------------------------------------
    # 2. AYARLAR SEKMESİ (SİMÜLASYON + HARİTA)
    # ---------------------------------------------------------
    def _init_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Hareket Simülasyonu Grubu
        movement_group = QGroupBox("🎯 Hareket Simülasyonu Ayarları")
        movement_layout = QVBoxLayout(movement_group)
        
        self.btn_toggle_movement = self._create_styled_button("▶️ Hareketi Başlat", "#27AE60")
        self.btn_toggle_movement.clicked.connect(self.toggle_movement)
        
        movement_progress_layout = QHBoxLayout()
        self.movement_status = QLabel("Hareket: DURUYOR")
        self.movement_status.setStyleSheet("font-weight: bold; color: #7F8C8D;")
        self.progress_movement = QProgressBar()
        self.progress_movement.setVisible(False)
        
        movement_progress_layout.addWidget(self.movement_status)
        movement_progress_layout.addWidget(self.progress_movement)
        
        movement_layout.addWidget(self.btn_toggle_movement)
        movement_layout.addLayout(movement_progress_layout)

        # Harita Kontrolü Grubu
        map_group = QGroupBox("🗺️ Harita Görünüm Ayarları")
        map_layout = QVBoxLayout(map_group)
        
        tile_layout = QHBoxLayout()
        self.combo_tiles = QComboBox()
        self.combo_tiles.addItems(["OpenStreetMap", "Satellite", "Terrain"])
        self.btn_change_tile = self._create_styled_button("Katmanı Değiştir", "#3498DB")
        self.btn_change_tile.clicked.connect(self.change_map_tile)
        
        tile_layout.addWidget(self.combo_tiles)
        tile_layout.addWidget(self.btn_change_tile)
        
        self.btn_export_png = self._create_styled_button("📸 Haritayı Resim Olarak Kaydet (PNG)", "#9B59B6")
        self.btn_export_png.clicked.connect(self.export_map_to_png)
        self.btn_show_trails = self._create_styled_button("🛤️ Sporcu İzlerini Göster / Gizle", "#F39C12")
        self.btn_show_trails.clicked.connect(self.toggle_trails)
        
        map_layout.addLayout(tile_layout)
        map_layout.addWidget(self.btn_export_png)
        map_layout.addWidget(self.btn_show_trails)

        # Layout'a ekle
        layout.addWidget(movement_group)
        layout.addWidget(map_group)
        layout.addStretch() 

        self.tabs.addTab(widget, "⚙️ Ayarlar")

    # ---------------------------------------------------------
    # 3. PARKUR SEKMESİ (GRUPLAMA + ÇİZİM)
    # ---------------------------------------------------------
    def _init_course_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grup Seçimi
        group_box = QGroupBox("📁 Parkur Grubu")
        group_layout = QHBoxLayout(group_box)
        
        self.combo_course_groups = QComboBox()
        self.btn_add_group = self._create_styled_button("➕ Yeni Grup", "#3498DB")
        
        group_layout.addWidget(QLabel("Aktif Parkur:"))
        group_layout.addWidget(self.combo_course_groups)
        group_layout.addWidget(self.btn_add_group)
        
        layout.addWidget(group_box)

        # Parkur Çizimi
        course_group = QGroupBox("🎯 İşaret Ekle")
        course_layout = QVBoxLayout(course_group)
        
        marker_buttons_layout = QHBoxLayout()
        self.btn_add_start = self._create_styled_button("🎯 Başlangıç", "#27AE60")
        self.btn_add_finish = self._create_styled_button("🏁 Bitiş", "#E74C3C")
        self.btn_add_drum = self._create_styled_button("🚧 Duba", "#F39C12")
        self.btn_add_checkpoint = self._create_styled_button("📍 Kontrol", "#9B59B6")
        
        marker_buttons_layout.addWidget(self.btn_add_start)
        marker_buttons_layout.addWidget(self.btn_add_finish)
        marker_buttons_layout.addWidget(self.btn_add_drum)
        marker_buttons_layout.addWidget(self.btn_add_checkpoint)
        
        # Çizgileri çiz butonu (YENİ)
        control_buttons_layout = QHBoxLayout()
        self.chk_lines = QCheckBox("Çizgileri Göster"); self.chk_lines.setChecked(True); self.chk_lines.toggled.connect(self.toggle_lines)
        self.btn_redraw_lines = self._create_styled_button("🔄 Çizgileri Birleştir / Yenile", "#8E44AD")
        
        control_buttons_layout.addWidget(self.chk_lines)
        control_buttons_layout.addWidget(self.btn_redraw_lines)
        
        course_layout.addLayout(marker_buttons_layout)
        course_layout.addLayout(control_buttons_layout)

        # Liste
        markers_group = QGroupBox("📋 İşaret Listesi")
        markers_layout = QVBoxLayout(markers_group)
        self.table_course_markers = QTableWidget()
        self.table_course_markers.setColumnCount(4)
        self.table_course_markers.setHorizontalHeaderLabels(["ID", "Tip", "Konum", "Grup"])
        self.table_course_markers.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_course_markers.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Sağ Tık Menüsü (YENİ)
        self.table_course_markers.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_course_markers.customContextMenuRequested.connect(self.context_menu_course)
        
        markers_layout.addWidget(self.table_course_markers)
        
        # Silme Butonu
        self.btn_del_marker = self._create_styled_button("❌ Seçili Noktayı Sil", "#C0392B")
        self.btn_del_marker.clicked.connect(self.delete_selected_marker)
        markers_layout.addWidget(self.btn_del_marker)
        
        self.btn_clear_course = self._create_styled_button("🗑️ Tüm Grubu Temizle", "#95A5A6")
        self.btn_clear_course.clicked.connect(self.clear_course_markers)
        markers_layout.addWidget(self.btn_clear_course)

        layout.addWidget(course_group)
        layout.addWidget(markers_group)

        self.tabs.addTab(widget, "🎯 Parkur")

        # Sinyaller
        self.btn_add_group.clicked.connect(self.handle_add_course_group)
        self.combo_course_groups.currentIndexChanged.connect(self.handle_group_change)
        self.btn_add_start.clicked.connect(lambda: self.add_course_marker("start"))
        self.btn_add_finish.clicked.connect(lambda: self.add_course_marker("finish"))
        self.btn_add_drum.clicked.connect(lambda: self.add_course_marker("drum"))
        self.btn_add_checkpoint.clicked.connect(lambda: self.add_course_marker("checkpoint"))
        self.btn_redraw_lines.clicked.connect(self.reload_map)
        
        # Başlangıçta grupları yükle
        self.load_course_groups()

    # ---------------------------------------------------------
    # DİĞER SEKMELER (SPORCULAR, MERKEZLER, PERSONEL)
    # ---------------------------------------------------------
    def _init_athletes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form_group = QGroupBox("👤 Sporcu Bilgileri")
        form_layout = QFormLayout(form_group)

        self.input_name = QLineEdit()
        self.input_lat = QDoubleSpinBox()
        self.input_lon = QDoubleSpinBox()
        self.input_device_id = QLineEdit()
        self.input_phone = QLineEdit()
        self.input_age = QSpinBox()
        self.input_blood_type = QComboBox()
        self.input_medical_info = QTextEdit()
        self.input_emergency_contact = QTextEdit()
        self.input_speed = QDoubleSpinBox()
        self.input_direction = QDoubleSpinBox()

        self.input_lat.setDecimals(6)
        self.input_lon.setDecimals(6)
        self.input_lat.setRange(-90.0, 90.0)
        self.input_lon.setRange(-180.0, 180.0)
        self.input_lat.setValue(MAP_CENTER[0])
        self.input_lon.setValue(MAP_CENTER[1])
        self.input_age.setRange(1, 100)
        self.input_blood_type.addItems(["", "A+", "A-", "B+", "B-", "AB+", "AB-", "0+", "0-"])
        self.input_medical_info.setMaximumHeight(60)
        self.input_emergency_contact.setMaximumHeight(60)
        self.input_speed.setRange(0.0001, 0.01)
        self.input_speed.setDecimals(5)
        self.input_speed.setValue(0.001)
        self.input_direction.setRange(0, 360)
        self.input_direction.setValue(0)

        form_layout.addRow("İsim *:", self.input_name)
        form_layout.addRow("Enlem:", self.input_lat)
        form_layout.addRow("Boylam:", self.input_lon)
        form_layout.addRow("Cihaz ID:", self.input_device_id)
        form_layout.addRow("Telefon:", self.input_phone)
        form_layout.addRow("Yaş:", self.input_age)
        form_layout.addRow("Kan Grubu:", self.input_blood_type)
        form_layout.addRow("Tıbbi Bilgiler:", self.input_medical_info)
        form_layout.addRow("Acil Durum İletişim:", self.input_emergency_contact)
        form_layout.addRow("Hız:", self.input_speed)
        form_layout.addRow("Yön (derece):", self.input_direction)

        layout.addWidget(form_group)

        btn_layout = QHBoxLayout()
        self.btn_add_update_athlete = self._create_styled_button("💾 Kaydet / Güncelle", "#27AE60")
        self.btn_clear_athlete = self._create_styled_button("🗑️ Formu Temizle", "#95A5A6")
        self.btn_delete_athlete = self._create_styled_button("❌ Sporcuyu Sil", "#E74C3C")

        btn_layout.addWidget(self.btn_add_update_athlete)
        btn_layout.addWidget(self.btn_clear_athlete)
        btn_layout.addWidget(self.btn_delete_athlete)
        layout.addLayout(btn_layout)

        self.table_athletes = QTableWidget()
        self.table_athletes.setColumnCount(6)
        self.table_athletes.setHorizontalHeaderLabels(["ID", "İsim", "Konum", "Cihaz", "Yaş", "Kan Grubu"])
        self.table_athletes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_athletes.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_athletes)

        self.tabs.addTab(widget, "🏃 Sporcular")

        self.btn_add_update_athlete.clicked.connect(self.handle_save_athlete)
        self.btn_clear_athlete.clicked.connect(self.clear_athlete_form)
        self.btn_delete_athlete.clicked.connect(self.handle_delete_athlete)
        self.table_athletes.itemSelectionChanged.connect(self.handle_athlete_table_selection)

    def _init_centers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form_group = QGroupBox("🏕️ Merkez Bilgileri")
        form_layout = QFormLayout(form_group)

        self.input_center_name = QLineEdit()
        self.input_center_lat = QDoubleSpinBox()
        self.input_center_lon = QDoubleSpinBox()
        self.input_center_type = QComboBox()
        self.input_center_capacity = QSpinBox()
        self.input_center_phone = QLineEdit()
        self.input_center_desc = QTextEdit()

        self.input_center_lat.setDecimals(6)
        self.input_center_lon.setDecimals(6)
        self.input_center_lat.setValue(MAP_CENTER[0])
        self.input_center_lon.setValue(MAP_CENTER[1])
        self.input_center_capacity.setRange(1, 1000)
        self.input_center_type.addItems(["rescue", "base", "medical"])
        self.input_center_desc.setMaximumHeight(60)

        form_layout.addRow("Merkez Adı *:", self.input_center_name)
        form_layout.addRow("Enlem:", self.input_center_lat)
        form_layout.addRow("Boylam:", self.input_center_lon)
        form_layout.addRow("Tip:", self.input_center_type)
        form_layout.addRow("Kapasite:", self.input_center_capacity)
        form_layout.addRow("İletişim:", self.input_center_phone)
        form_layout.addRow("Açıklama:", self.input_center_desc)

        layout.addWidget(form_group)

        center_btn_layout = QHBoxLayout()
        self.btn_add_center = self._create_styled_button("🏕️ Merkez Ekle", "#3498DB")
        self.btn_delete_center = self._create_styled_button("❌ Merkezi Sil", "#E74C3C")

        center_btn_layout.addWidget(self.btn_add_center)
        center_btn_layout.addWidget(self.btn_delete_center)
        layout.addLayout(center_btn_layout)

        self.table_centers = QTableWidget()
        self.table_centers.setColumnCount(5)
        self.table_centers.setHorizontalHeaderLabels(["ID", "Ad", "Tip", "Kapasite", "Konum"])
        self.table_centers.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_centers.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_centers)

        self.tabs.addTab(widget, "🏕️ Merkezler")

        self.btn_add_center.clicked.connect(self.handle_add_center)
        self.btn_delete_center.clicked.connect(self.handle_delete_center)
        self.table_centers.itemSelectionChanged.connect(self.handle_center_table_selection)

    def _init_personnel_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form_group = QGroupBox("👥 Personel Ekle")
        form_layout = QFormLayout(form_group)

        self.input_personnel_name = QLineEdit()
        self.combo_personnel_center = QComboBox()
        self.input_personnel_role = QLineEdit()
        self.input_personnel_phone = QLineEdit()
        self.input_personnel_specialty = QLineEdit()
        self.check_personnel_available = QCheckBox("Mevcut")

        form_layout.addRow("Ad Soyad *:", self.input_personnel_name)
        form_layout.addRow("Merkez *:", self.combo_personnel_center)
        form_layout.addRow("Görev *:", self.input_personnel_role)
        form_layout.addRow("Telefon:", self.input_personnel_phone)
        form_layout.addRow("Uzmanlık:", self.input_personnel_specialty)
        form_layout.addRow("", self.check_personnel_available)

        layout.addWidget(form_group)

        personnel_btn_layout = QHBoxLayout()
        self.btn_add_personnel = self._create_styled_button("👥 Personel Ekle", "#9B59B6")
        self.btn_delete_personnel = self._create_styled_button("❌ Personeli Sil", "#E74C3C")

        personnel_btn_layout.addWidget(self.btn_add_personnel)
        personnel_btn_layout.addWidget(self.btn_delete_personnel)
        layout.addLayout(personnel_btn_layout)

        self.table_personnel = QTableWidget()
        self.table_personnel.setColumnCount(6)
        self.table_personnel.setHorizontalHeaderLabels(["ID", "Ad", "Merkez", "Görev", "Uzmanlık", "Durum"])
        self.table_personnel.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_personnel.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_personnel)

        self.tabs.addTab(widget, "👥 Personel")

        self.btn_add_personnel.clicked.connect(self.handle_add_personnel)
        self.btn_delete_personnel.clicked.connect(self.handle_delete_personnel)
        self.combo_personnel_center.currentIndexChanged.connect(self.handle_center_selection)

    # --- MANTIK VE İŞLEMLER ---

    def _setup_timers(self):
        self.movement_timer.timeout.connect(self.update_movements)
        self.movement_timer.setInterval(2000)

    def toggle_movement(self):
        self.is_movement_active = not self.is_movement_active
        if self.is_movement_active:
            self.movement_timer.start()
            self.btn_toggle_movement.setText("⏸️ Hareketi Durdur")
            self.btn_toggle_movement.setStyleSheet(self._get_button_style("#E74C3C"))
            self.movement_status.setText("Hareket: AKTİF")
            self.movement_status.setStyleSheet("font-weight: bold; color: #27AE60;")
            self.progress_movement.setVisible(True)
            self.log("🎯 Hareket simülasyonu BAŞLATILDI")
        else:
            self.movement_timer.stop()
            self.btn_toggle_movement.setText("▶️ Hareketi Başlat")
            self.btn_toggle_movement.setStyleSheet(self._get_button_style("#27AE60"))
            self.movement_status.setText("Hareket: DURUYOR")
            self.movement_status.setStyleSheet("font-weight: bold; color: #7F8C8D;")
            self.progress_movement.setVisible(False)
            self.log("⏸️ Hareket simülasyonu DURDURULDU")

    def update_map_markers_js(self):
        athletes = self.db.get_all_athletes()
        for athlete in athletes:
            js_code = f"updateMarkerPosition('{athlete['id']}', {athlete['lat']}, {athlete['lon']});"
            self.webview.page().runJavaScript(js_code)

    def update_movements(self):
        if not self.is_movement_active:
            return

        athletes = self.db.get_all_athletes()
        for athlete in athletes:
            new_lat, new_lon, new_direction = simulate_movement(athlete)
            self.db.update_athlete_position(athlete['id'], new_lat, new_lon)
            
            athlete_data = {
                'name': athlete['name'], 'lat': new_lat, 'lon': new_lon,
                'device_id': athlete.get('device_id', ''), 'phone': athlete.get('phone', ''),
                'age': athlete.get('age', 0), 'blood_type': athlete.get('blood_type', ''),
                'medical_info': athlete.get('medical_info', ''), 'emergency_contact': athlete.get('emergency_contact', ''),
                'speed': athlete.get('speed', 0.001), 'direction': new_direction
            }
            self.db.update_athlete(athlete['id'], athlete_data)

        self.update_map_markers_js()
        self.progress_movement.setValue((self.progress_movement.value() + 10) % 100)

    def handle_drag_update(self, info, lat, lon):
        parts = info.split(":") # MARKER:ID:TYPE veya CENTER:ID:AD
        if len(parts) >= 2:
            obj_type = parts[0]
            obj_id = int(parts[1])
            
            if obj_type == "MARKER":
                self.db.update_marker_position(obj_id, lat, lon)
                self.log(f"📍 Parkur Noktası Taşındı: ID {obj_id}")
                # Sadece tabloyu güncelle, haritayı YENİLEME (titreşim olmasın)
                self.load_course_markers() 
            elif obj_type == "CENTER":
                self.db.update_center_position(obj_id, lat, lon)
                self.log(f"🏕️ Merkez Taşındı: ID {obj_id}")
                self.populate_center_table()
                self.populate_center_combo() 

    # --- PARKUR YÖNETİMİ (YENİ) ---
    def load_course_groups(self):
        self.combo_course_groups.clear()
        groups = self.db.get_course_groups()
        for group in groups:
            self.combo_course_groups.addItem(group['name'], group['id'])
        
        if self.combo_course_groups.count() > 0:
            self.reload_map_with_group()

    def handle_add_course_group(self):
        text, ok = QInputDialog.getText(self, 'Yeni Grup', 'Parkur Grubu Adı:')
        if ok and text:
            self.db.add_course_group(text)
            self.load_course_groups()
            self.combo_course_groups.setCurrentText(text)

    def handle_group_change(self):
        self.load_course_markers()
        self.reload_map_with_group()

    def reload_map_with_group(self):
        group_id = self.combo_course_groups.currentData()
        path = self.map_manager.create_map(show_trails=self.show_trails, active_group_id=group_id, draw_lines=self.draw_lines)
        self.webview.load(QUrl.fromLocalFile(os.path.abspath(path)))

    def add_course_marker(self, marker_type: str):
        group_id = self.combo_course_groups.currentData()
        if not group_id:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir parkur grubu seçin.")
            return

        base_lat, base_lon = MAP_CENTER
        current_markers = self.db.get_course_markers_by_group(group_id)
        offset = len(current_markers) * 0.002
        lat = base_lat + offset * math.cos(len(current_markers))
        lon = base_lon + offset * math.sin(len(current_markers))
        
        description = marker_type
        self.db.save_course_marker(marker_type, lat, lon, description, group_id)
        self.log(f"🎯 İşaret eklendi ({marker_type}) -> {self.combo_course_groups.currentText()}")
        self.handle_group_change()

    def clear_course_markers(self):
        group_id = self.combo_course_groups.currentData()
        if not group_id: return
        
        reply = QMessageBox.question(
            self, "Onay", "Seçili parkur grubundaki TÜM işaretleri silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.clear_course_markers(group_id)
            self.log("🗑️ Parkur işaretleri temizlendi")
            self.handle_group_change()

    def delete_selected_marker(self):
        """Tablodan seçili satırı ve veritabanından veriyi siler"""
        selected = self.table_course_markers.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için tablodan bir satır seçin.")
            return
        
        # Tablo sütun sırasına göre 0. indeks ID'yi tutuyor
        row = selected[0].row()
        marker_id = int(self.table_course_markers.item(row, 0).text())
        
        self.db.delete_marker(marker_id)
        self.log(f"🗑️ Marker silindi: ID {marker_id}")
        
        # Listeyi ve Haritayı güncelle
        self.load_course_markers()
        self.reload_map_with_group()

    def context_menu_course(self, pos):
        """Parkur tablosu için sağ tık menüsü"""
        menu = QMenu()
        act_delete = menu.addAction("❌ Bu Noktayı Sil")
        action = menu.exec_(self.table_course_markers.mapToGlobal(pos))
        if action == act_delete:
            self.delete_selected_marker()

    def load_course_markers(self):
        group_id = self.combo_course_groups.currentData()
        if not group_id:
            self.table_course_markers.setRowCount(0)
            return
            
        markers = self.db.get_course_markers_by_group(group_id)
        self.table_course_markers.setRowCount(len(markers))
        
        for row, marker in enumerate(markers):
            self.table_course_markers.setItem(row, 0, QTableWidgetItem(str(marker["id"])))
            self.table_course_markers.setItem(row, 1, QTableWidgetItem(marker["type"]))
            self.table_course_markers.setItem(row, 2, QTableWidgetItem(f"{marker['lat']:.4f}, {marker['lon']:.4f}"))
            self.table_course_markers.setItem(row, 3, QTableWidgetItem(self.combo_course_groups.currentText()))

    # --- DİĞER YARDIMCI FONKSİYONLAR ---

    def save_course(self):
        # Veritabanına zaten anlık kaydediyoruz
        QMessageBox.information(self, "Bilgi", "Parkur değişiklikleri veritabanına otomatik kaydedilmektedir.")

    def change_map_tile(self):
        try:
            tile_name = self.combo_tiles.currentText()
            self.map_manager.change_tile(tile_name)
            self.log(f"🗺️ Harita katmanı değiştirildi: {tile_name}")
            self.reload_map_with_group()
        except Exception as e:
            self.log(f"❌ Harita değiştirme hatası: {str(e)}")

    def reload_map(self):
        self.reload_map_with_group()

    def export_map_to_png(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Haritayı PNG Olarak Kaydet", "", "PNG Files (*.png)")
        if file_path:
            if self.map_manager.export_to_png("", file_path):
                self.log(f"📸 Harita PNG olarak kaydedildi: {file_path}")
                QMessageBox.information(self, "Başarılı", f"Harita başarıyla kaydedildi:\n{file_path}")
            else:
                self.log("❌ PNG kaydetme başarısız")

    def toggle_trails(self):
        self.show_trails = not self.show_trails
        self.log(f"🛤️ Hareket izleri: {'AÇIK' if self.show_trails else 'KAPALI'}")
        self.reload_map_with_group()

    def toggle_lines(self):
        self.draw_lines = self.chk_lines.isChecked()
        self.reload_map_with_group()

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")

    def reload_data(self):
        self.athletes = self.db.get_all_athletes()
        self.centers = self.db.get_all_centers()
        self.populate_athlete_combo()
        self.populate_athlete_table()
        self.populate_center_combo()
        self.populate_center_table()
        self.load_personnel_for_center()
        self.load_course_groups() # Parkuru da yükle
        self.log("🔄 Tüm veriler yenilendi")

    def populate_athlete_combo(self):
        self.combo_athletes.clear()
        for athlete in self.athletes:
            self.combo_athletes.addItem(f"{athlete['name']} (ID: {athlete['id']})", athlete["id"])

    def populate_athlete_table(self):
        self.table_athletes.setRowCount(len(self.athletes))
        for row, athlete in enumerate(self.athletes):
            self.table_athletes.setItem(row, 0, QTableWidgetItem(str(athlete["id"])))
            self.table_athletes.setItem(row, 1, QTableWidgetItem(athlete["name"]))
            self.table_athletes.setItem(row, 2, QTableWidgetItem(f"{athlete['lat']:.4f}, {athlete['lon']:.4f}"))
            self.table_athletes.setItem(row, 3, QTableWidgetItem(athlete.get('device_id', 'N/A')))
            self.table_athletes.setItem(row, 4, QTableWidgetItem(str(athlete.get('age', 'N/A'))))
            self.table_athletes.setItem(row, 5, QTableWidgetItem(athlete.get('blood_type', 'N/A')))

    def populate_center_combo(self):
        self.combo_personnel_center.clear()
        for center in self.centers:
            self.combo_personnel_center.addItem(f"{center['name']} (ID: {center['id']})", center["id"])

    def populate_center_table(self):
        self.table_centers.setRowCount(len(self.centers))
        for row, center in enumerate(self.centers):
            self.table_centers.setItem(row, 0, QTableWidgetItem(str(center["id"])))
            self.table_centers.setItem(row, 1, QTableWidgetItem(center["name"]))
            self.table_centers.setItem(row, 2, QTableWidgetItem(center["type"]))
            self.table_centers.setItem(row, 3, QTableWidgetItem(str(center.get('capacity', 'N/A'))))
            self.table_centers.setItem(row, 4, QTableWidgetItem(f"{center['lat']:.4f}, {center['lon']:.4f}"))

    def handle_single_athlete(self):
        athlete_id = self.combo_athletes.currentData()
        athlete = next((a for a in self.athletes if a["id"] == athlete_id), None)
        if not athlete: return
        self.log(f"📡 {athlete['name']} verileri alınıyor...")
        data = get_device_data_for_athlete(athlete)
        msg = f"✅ {data['name']} | 📍({data['lat']:.5f}, {data['lon']:.5f}) | 🌡️{data['temperature']}°C | 🔋{data['battery']}%"
        self.log(msg)

    def handle_scan_all(self):
        self.log("🔄 Tüm sporcular taranıyor...")
        for athlete in self.athletes:
            data = get_device_data_for_athlete(athlete)
            msg = f"✅ {data['name']} | 📍({data['lat']:.5f}, {data['lon']:.5f}) | 🔋{data['battery']}%"
            self.log(msg)
        self.log("✅ Tarama tamamlandı")

    def handle_show_emergencies(self):
        self.log("🚨 Acil durum taraması...")
        emergencies = []
        for athlete in self.athletes:
            data = get_device_data_for_athlete(athlete)
            if data["emergency"]:
                emergencies.append(data)
                self.log(f"🚨 ACİL! {data['name']} | 🔋{data['battery']}%")
        if not emergencies: self.log("✅ Acil durum yok")

    def show_athlete_details(self):
        athlete_id = self.combo_athletes.currentData()
        athlete = next((a for a in self.athletes if a["id"] == athlete_id), None)
        if athlete:
            details = f"🏃 {athlete['name']}\n📍 Konum: {athlete['lat']:.5f}, {athlete['lon']:.5f}\n📱 Cihaz: {athlete.get('device_id', 'N/A')}\n📞 Tel: {athlete.get('phone', 'N/A')}"
            QMessageBox.information(self, "Sporcu Detayları", details)

    def clear_athlete_form(self):
        self.current_edit_id = None
        self.input_name.clear()
        self.input_lat.setValue(MAP_CENTER[0])
        self.input_lon.setValue(MAP_CENTER[1])

    def handle_save_athlete(self):
        athlete_data = {
            'name': self.input_name.text().strip(), 'lat': self.input_lat.value(), 'lon': self.input_lon.value(),
            'device_id': self.input_device_id.text().strip(), 'phone': self.input_phone.text().strip(),
            'age': self.input_age.value(), 'blood_type': self.input_blood_type.currentText(),
            'medical_info': self.input_medical_info.toPlainText().strip(),
            'emergency_contact': self.input_emergency_contact.toPlainText().strip(),
            'speed': self.input_speed.value(), 'direction': self.input_direction.value()
        }
        if not athlete_data['name']: return
        try:
            if self.current_edit_id is None:
                self.db.add_athlete(athlete_data)
            else:
                self.db.update_athlete(self.current_edit_id, athlete_data)
            self.clear_athlete_form()
            self.reload_data()
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def handle_delete_athlete(self):
        if self.current_edit_id:
            self.db.delete_athlete(self.current_edit_id)
            self.clear_athlete_form()
            self.reload_data()

    def handle_athlete_table_selection(self):
        selected = self.table_athletes.selectedItems()
        if selected:
            athlete_id = int(self.table_athletes.item(selected[0].row(), 0).text())
            athlete = next((a for a in self.athletes if a["id"] == athlete_id), None)
            if athlete:
                self.current_edit_id = athlete_id
                self.input_name.setText(athlete['name'])
                self.input_lat.setValue(athlete['lat'])
                self.input_lon.setValue(athlete['lon'])
                self.input_device_id.setText(athlete.get('device_id', ''))
                self.input_phone.setText(athlete.get('phone', ''))
                self.input_age.setValue(athlete.get('age', 25))
                self.input_blood_type.setCurrentText(athlete.get('blood_type', ''))
                self.input_medical_info.setPlainText(athlete.get('medical_info', ''))
                self.input_emergency_contact.setPlainText(athlete.get('emergency_contact', ''))

    def handle_add_center(self):
        center_data = {
            'name': self.input_center_name.text().strip(), 'lat': self.input_center_lat.value(),
            'lon': self.input_center_lon.value(), 'type': self.input_center_type.currentText(),
            'capacity': self.input_center_capacity.value(), 'contact_phone': self.input_center_phone.text().strip(),
            'description': self.input_center_desc.toPlainText().strip()
        }
        if center_data['name']:
            self.db.add_center(center_data)
            self.reload_data()

    def handle_delete_center(self):
        if self.current_center_id:
            self.db.delete_center(self.current_center_id)
            self.reload_data()

    def handle_center_table_selection(self):
        selected = self.table_centers.selectedItems()
        if not selected:
            self.current_center_id = None
            return
        self.current_center_id = int(self.table_centers.item(selected[0].row(), 0).text())

    def handle_center_selection(self):
        self.load_personnel_for_center()

    def load_personnel_for_center(self):
        center_id = self.combo_personnel_center.currentData()
        if center_id:
            personnel = self.db.get_personnel_by_center(center_id)
            self.table_personnel.setRowCount(len(personnel))
            for row, person in enumerate(personnel):
                self.table_personnel.setItem(row, 0, QTableWidgetItem(str(person["id"])))
                self.table_personnel.setItem(row, 1, QTableWidgetItem(person["name"]))
                center_name = next((c['name'] for c in self.centers if c['id'] == person['center_id']), 'N/A')
                self.table_personnel.setItem(row, 2, QTableWidgetItem(center_name))
                self.table_personnel.setItem(row, 3, QTableWidgetItem(person["role"]))
                self.table_personnel.setItem(row, 4, QTableWidgetItem(person.get("specialty", "N/A")))
                status = "✅ Mevcut" if person.get("is_available", True) else "❌ Mevcut Değil"
                self.table_personnel.setItem(row, 5, QTableWidgetItem(status))

    def handle_add_personnel(self):
        center_id = self.combo_personnel_center.currentData()
        if center_id:
            data = {
                'name': self.input_personnel_name.text().strip(), 'center_id': center_id,
                'role': self.input_personnel_role.text().strip(), 'phone': self.input_personnel_phone.text().strip(),
                'specialty': self.input_personnel_specialty.text().strip(),
                'is_available': self.check_personnel_available.isChecked()
            }
            self.db.add_personnel(data)
            self.load_personnel_for_center()

    def handle_delete_personnel(self):
        selected = self.table_personnel.selectedItems()
        if selected:
            pid = int(self.table_personnel.item(selected[0].row(), 0).text())
            self.db.delete_personnel(pid)
            self.load_personnel_for_center()

def main():
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    window = ModernMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()