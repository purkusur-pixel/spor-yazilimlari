using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Reflection;
using System.Windows.Forms;

namespace SporcuTakip
{
    public partial class Form_performans : Form
    {
        public Form_performans()
        {
            InitializeComponent();
        }

        // === DB ===
        private string DbPath => Path.Combine(Application.StartupPath, "goruntu_isleme.db");
        private string ConnStr => $"Data Source={DbPath};Version=3;";

        private void EnsureDb()
        {
            if (!File.Exists(DbPath))
                SQLiteConnection.CreateFile(DbPath);

            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();

                using (var cmd = new SQLiteCommand(@"
CREATE TABLE IF NOT EXISTS kisiler_forcedesk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    soyad TEXT,
    notlar TEXT,
    aktif INTEGER NOT NULL DEFAULT 1
);", con))
                {
                    cmd.ExecuteNonQuery();
                }

                using (var cmd = new SQLiteCommand(@"
CREATE TABLE IF NOT EXISTS test_sonuclari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kisi_id INTEGER NOT NULL,
    test_adi TEXT NOT NULL,
    tarih TEXT NOT NULL,
    notlar TEXT,
    peak_power REAL,
    rsi_modified REAL,
    jump_height_cm REAL,
    FOREIGN KEY(kisi_id) REFERENCES kisiler_forcedesk(id)
);", con))
                {
                    cmd.ExecuteNonQuery();
                }
            }
        }

        private void LoadKisiler()
        {
            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var da = new SQLiteDataAdapter(@"
SELECT id,
       TRIM(COALESCE(ad,'')) ||
       CASE WHEN COALESCE(soyad,'')<>'' THEN ' '||TRIM(soyad) ELSE '' END AS adsoy
FROM kisiler_forcedesk
WHERE aktif=1
ORDER BY ad, soyad;", con))
                {
                    var dt = new DataTable();
                    da.Fill(dt);
                    comboKisi.DataSource = dt;
                    comboKisi.ValueMember = "id";
                    comboKisi.DisplayMember = "adsoy";
                }
            }
        }

        private void LoadSonuclarGrid()
        {
            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var da = new SQLiteDataAdapter(@"
SELECT ts.id,
       k.ad || CASE WHEN COALESCE(k.soyad,'')<>'' THEN ' '||k.soyad ELSE '' END AS Kisi,
       ts.test_adi AS Test,
       ts.tarih    AS Tarih,
       ROUND(ts.peak_power,1)     AS PeakPowerW,
       ROUND(ts.rsi_modified,3)   AS RSI_Mod,
       ROUND(ts.jump_height_cm,1) AS JumpHeight_cm
FROM test_sonuclari ts
JOIN kisiler_forcedesk k ON k.id = ts.kisi_id
ORDER BY ts.id DESC
LIMIT 100;", con))
                {
                    var dt = new DataTable();
                    da.Fill(dt);
                    gridSonuclar.DataSource = dt;
                }
            }
        }

        // === Seri Port / Akış ===
        private SerialPort _serialPort;
        private readonly Queue<string> _serialBuffer = new Queue<string>();
        private readonly object _serialLock = new object();

        private const int BaudRate = 115200;   // Cihazla aynı olmalı
        private const double Dt = 0.02;        // Örnek başına varsayılan zaman
        private const int CALIB_SAMPLES = 200; // Ham format için kalibrasyon örnek sayısı

        private bool _isRunning = false;

        // Kalibrasyon (8 kolon ham format için)
        private bool _calibrated = false;
        private int _calibCount = 0;
        private double _s1Sum = 0.0;
        private double _s2Sum = 0.0;
        private double _s1Offset = 0.0;
        private double _s2Offset = 0.0;

        // Zaman & pencere
        private double _t = 0.0;
        private double _xWindow = 10.0; // son 10 sn

        private Timer _timer;

        // Grafik serileri
        private readonly List<PointF> seriesLeft = new List<PointF>();   // s1_zero
        private readonly List<PointF> seriesRight = new List<PointF>();  // s2_zero
        private readonly List<PointF> seriesVert = new List<PointF>();   // s1_zero + s2_zero

        // Y ekseni için yumuşatma (titreme azaltma)
        private float _yMinSmooth = -200f;
        private float _yMaxSmooth = 800f;

        // === Form Load ===
        private void Form_performans_Load(object sender, EventArgs e)
        {
            EnsureDb();
            if (comboTest.Items.Count > 0) comboTest.SelectedIndex = 0;
            LoadKisiler();
            LoadSonuclarGrid();
            LoadComPorts();

            // panelCanvas için double-buffer aç (flicker azaltır)
            typeof(Panel)
                .GetProperty("DoubleBuffered", BindingFlags.Instance | BindingFlags.NonPublic)
                ?.SetValue(panelCanvas, true, null);

            _timer = new Timer
            {
                Interval = 50 // 20ms çok agresifti, 50ms = 20 FPS gayet akıcı
            };
            _timer.Tick += Timer_Tick;
        }

        // === COM listesi ===
        private void LoadComPorts()
        {
            comboPort.Items.Clear();
            var ports = SerialPort.GetPortNames().OrderBy(p => p).ToArray();
            comboPort.Items.AddRange(ports);
            if (comboPort.Items.Count > 0)
                comboPort.SelectedIndex = 0;
        }

        private void OpenSerialOnSelectedPort()
        {
            CloseSerial();

            if (comboPort.SelectedItem == null)
                throw new Exception("Seri port seçili değil.");

            string portName = comboPort.SelectedItem.ToString();

            var sp = new SerialPort(portName, BaudRate, Parity.None, 8, StopBits.One)
            {
                ReadTimeout = 200,
                NewLine = "\n",
                Handshake = Handshake.None,
                DtrEnable = true,
                RtsEnable = true
            };

            sp.DataReceived += SerialPort_DataReceived;
            sp.Open();

            _serialPort = sp;
        }

        private void CloseSerial()
        {
            try
            {
                if (_serialPort != null)
                {
                    _serialPort.DataReceived -= SerialPort_DataReceived;
                    if (_serialPort.IsOpen)
                        _serialPort.Close();
                    _serialPort.Dispose();
                }
            }
            catch { }
            finally
            {
                _serialPort = null;
            }
        }

        private void SerialPort_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            try
            {
                var sp = (SerialPort)sender;
                while (sp.BytesToRead > 0)
                {
                    string line = sp.ReadLine();
                    lock (_serialLock)
                    {
                        _serialBuffer.Enqueue(line);
                        if (_serialBuffer.Count > 5000)
                            _serialBuffer.Dequeue();
                    }
                }
            }
            catch
            {
                // yok say
            }
        }

        // === Parse yardımcıları ===
        private bool TryParseDoubleFlexible(string s, out double value)
        {
            return double.TryParse(s, NumberStyles.Any, CultureInfo.InvariantCulture, out value)
                || double.TryParse(s, NumberStyles.Any, CultureInfo.CurrentCulture, out value);
        }

        /// <summary>
        /// Satırdan s1_zero ve s2_zero çıkar.
        /// Destek:
        /// 1) 11 kolon CSV:
        ///    time,temp1,temp2,s1_raw,s2_raw,s1_zero,s2_zero,ax,ay,az,imu_temp
        /// 2) 8 kolon ham:
        ///    temp1,temp2,s1_raw,s2_raw,ax,ay,az,imu_temp  (ilk CALIB_SAMPLES ile kalibrasyon)
        /// </summary>
        private bool TryGetForcesFromLine(string line, out double s1_zero, out double s2_zero)
        {
            s1_zero = s2_zero = 0;

            if (string.IsNullOrWhiteSpace(line))
                return false;

            line = line.Trim();

            // Header satırlarını at
            if (line.StartsWith("time") || line.StartsWith("temp1"))
                return false;

            // --- 11 kolon CSV dene ---
            var partsComma = line.Split(',');
            if (partsComma.Length >= 11)
            {
                if (TryParseDoubleFlexible(partsComma[5], out double z1) &&
                    TryParseDoubleFlexible(partsComma[6], out double z2))
                {
                    s1_zero = z1;
                    s2_zero = z2;
                    return true; // zaten offsetli
                }
            }

            // --- 8 kolon ham dene ---
            var parts = line
                .Replace(";", " ")
                .Replace(",", " ")
                .Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);

            if (parts.Length < 8)
                return false;

            double[] vals = new double[8];
            for (int i = 0; i < 8; i++)
            {
                if (!TryParseDoubleFlexible(parts[i], out vals[i]))
                    return false;
            }

            double s1_raw = vals[2];
            double s2_raw = vals[3];

            // Kalibrasyon
            if (!_calibrated)
            {
                _s1Sum += s1_raw;
                _s2Sum += s2_raw;
                _calibCount++;

                if (_calibCount >= CALIB_SAMPLES)
                {
                    _s1Offset = _s1Sum / _calibCount;
                    _s2Offset = _s2Sum / _calibCount;
                    _calibrated = true;

                    Debug.WriteLine($"[PERFORMANS] Kalibrasyon OK: s1_offset={_s1Offset:F5}, s2_offset={_s2Offset:F5}");
                    this.Text = $"Performans (ForceDesk - Basit Çizim)  [Kalibre: s1={_s1Offset:F2}, s2={_s2Offset:F2}]";
                }

                return false; // kalibrasyon sürecindeyken çizme
            }

            s1_zero = s1_raw - _s1Offset;
            s2_zero = s2_raw - _s2Offset;
            return true;
        }

        private void ClearAllSeries()
        {
            seriesLeft.Clear();
            seriesRight.Clear();
            seriesVert.Clear();
        }

        // === Timer: buffer -> parse -> çizim serisine ekle ===
        private void Timer_Tick(object sender, EventArgs e)
        {
            bool updated = false;
            int processed = 0;

            // Çok veri geliyorsa tek tick'te sonsuza kadar dönmesin, 200 satır limitle
            while (processed < 200)
            {
                string line = null;
                lock (_serialLock)
                {
                    if (_serialBuffer.Count > 0)
                        line = _serialBuffer.Dequeue();
                }

                if (line == null)
                    break;

                Debug.WriteLine("[SERIAL] " + line);

                if (!TryGetForcesFromLine(line, out double s1_zero, out double s2_zero))
                {
                    processed++;
                    continue;
                }

                double vert = s1_zero + s2_zero;
                _t += Dt;

                seriesLeft.Add(new PointF((float)_t, (float)s1_zero));
                seriesRight.Add(new PointF((float)_t, (float)s2_zero));
                seriesVert.Add(new PointF((float)_t, (float)vert));

                TrimToWindow(seriesLeft);
                TrimToWindow(seriesRight);
                TrimToWindow(seriesVert);

                updated = true;
                processed++;
            }

            if (updated)
                panelCanvas.Invalidate();
        }

        private void TrimToWindow(List<PointF> list)
        {
            float xmin = (float)Math.Max(0, _t - _xWindow);
            int idx = list.FindIndex(p => p.X >= xmin);
            if (idx > 0)
                list.RemoveRange(0, idx);
        }

        // === Testi Başlat / Durdur ===
        private void btnTestiBaslat_Click(object sender, EventArgs e)
        {
            if (comboKisi.SelectedValue == null)
            {
                MessageBox.Show("Lütfen kişi seçiniz.");
                return;
            }

            if (!_isRunning)
            {
                try
                {
                    OpenSerialOnSelectedPort();
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Seri port açılamadı: " + ex.Message);
                    return;
                }

                ClearAllSeries();
                _t = 0;

                _calibrated = false;
                _calibCount = 0;
                _s1Sum = _s2Sum = 0;
                _s1Offset = _s2Offset = 0;
                lock (_serialLock) _serialBuffer.Clear();

                _timer.Start();
                _isRunning = true;
                btnTestiBaslat.Text = "Durdur";
            }
            else
            {
                _timer.Stop();
                _isRunning = false;
                btnTestiBaslat.Text = "Testi Başlat";
                CloseSerial();
            }
        }

        private void btnGrafikTemizle_Click(object sender, EventArgs e)
        {
            ClearAllSeries();
            _t = 0;
            panelCanvas.Invalidate();
        }

        // === Kişi Ekle ===
        private void btnKisiEkle_Click(object sender, EventArgs e)
        {
            using (var dlg = new KisiEkleForm())
            {
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    try
                    {
                        using (var con = new SQLiteConnection(ConnStr))
                        {
                            con.Open();
                            using (var cmd = new SQLiteCommand(
                                "INSERT INTO kisiler_forcedesk(ad, soyad, notlar, aktif) VALUES(@a, @s, @n, 1);", con))
                            {
                                cmd.Parameters.AddWithValue("@a", dlg.Ad);
                                cmd.Parameters.AddWithValue("@s",
                                    string.IsNullOrWhiteSpace(dlg.Soyad) ? (object)DBNull.Value : dlg.Soyad);
                                cmd.Parameters.AddWithValue("@n",
                                    string.IsNullOrWhiteSpace(dlg.Notlar) ? (object)DBNull.Value : dlg.Notlar);
                                cmd.ExecuteNonQuery();
                            }
                        }

                        LoadKisiler();
                        MessageBox.Show("Kişi eklendi.", "Bilgi");
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Kişi eklenemedi: " + ex.Message, "Hata");
                    }
                }
            }
        }

        // === Canvas Resize ===
        private void panelCanvas_Resize(object sender, EventArgs e)
        {
            panelCanvas.Invalidate();
        }

        // === Canvas Çizim (yumuşatılmış autoscale + double buffer sayesinde titreme az) ===
        private void panelCanvas_Paint(object sender, PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            g.Clear(Color.White);

            Rectangle r = panelCanvas.ClientRectangle;
            if (r.Width <= 40 || r.Height <= 40) return;

            int lm = 50, rm = 10, tm = 10, bm = 28;
            Rectangle plot = new Rectangle(
                r.Left + lm, r.Top + tm,
                r.Width - lm - rm,
                r.Height - tm - bm);

            if (plot.Width <= 1 || plot.Height <= 1) return;

            float xmin = (float)Math.Max(0, _t - _xWindow);
            float xmax = (float)Math.Max(_xWindow, _t);

            // --- Y aralığı: yumuşatılmış autoscale ---
            float ymin = _yMinSmooth;
            float ymax = _yMaxSmooth;

            var all = seriesVert.Concat(seriesLeft).Concat(seriesRight).ToList();
            if (all.Count > 0)
            {
                float dataMin = all.Min(p => p.Y);
                float dataMax = all.Max(p => p.Y);
                if (Math.Abs(dataMax - dataMin) < 1e-3f)
                {
                    dataMax = dataMin + 1f;
                }

                // padding
                float pad = (dataMax - dataMin) * 0.15f + 10f;
                float targetMin = Math.Min(0, dataMin - pad);
                float targetMax = dataMax + pad;

                // smooth (exponential)
                float alpha = 0.2f;
                _yMinSmooth = _yMinSmooth + alpha * (targetMin - _yMinSmooth);
                _yMaxSmooth = _yMaxSmooth + alpha * (targetMax - _yMaxSmooth);

                ymin = _yMinSmooth;
                ymax = _yMaxSmooth;
            }

            if (ymax - ymin < 1f)
            {
                ymax = ymin + 1f;
            }

            using (var penAxis = new Pen(Color.Gray, 1))
            using (var penGrid = new Pen(Color.FromArgb(40, Color.Gray), 1))
            using (var brLabel = new SolidBrush(Color.Black))
            using (var font = new Font("Segoe UI", 8f))
            {
                penGrid.DashStyle = System.Drawing.Drawing2D.DashStyle.Dot;

                // Dikey grid (Zaman)
                int xTicks = 10;
                for (int i = 0; i <= xTicks; i++)
                {
                    float tx = xmin + i * (xmax - xmin) / xTicks;
                    int px = XToPx(tx, xmin, xmax, plot);
                    g.DrawLine(penGrid, px, plot.Top, px, plot.Bottom);
                    string s = tx.ToString("0.0");
                    var sz = g.MeasureString(s, font);
                    g.DrawString(s, font, brLabel,
                        px - sz.Width / 2f, plot.Bottom + 4);
                }

                // Yatay grid (Kuvvet)
                int yTicks = 6;
                for (int i = 0; i <= yTicks; i++)
                {
                    float ty = ymin + i * (ymax - ymin) / yTicks;
                    int py = YToPx(ty, ymin, ymax, plot);
                    g.DrawLine(penGrid, plot.Left, py, plot.Right, py);
                    string s = ty.ToString("0");
                    var sz = g.MeasureString(s, font);
                    g.DrawString(s, font, brLabel,
                        plot.Left - sz.Width - 6, py - sz.Height / 2f);
                }

                // Çerçeve
                g.DrawRectangle(penAxis, plot);

                // Seriler
                DrawSeries(g, seriesLeft, xmin, xmax, ymin, ymax, plot, Pens.Blue);
                DrawSeries(g, seriesRight, xmin, xmax, ymin, ymax, plot, Pens.Green);
                DrawSeries(g, seriesVert, xmin, xmax, ymin, ymax, plot, Pens.Red);

                // Eksen yazıları
                g.DrawString("Zaman (s)", font, brLabel,
                    plot.Left + plot.Width / 2 - 30, plot.Bottom + 16);
                g.DrawString("Kuvvet [N]", font, brLabel,
                    plot.Left - 44, plot.Top - 2);
            }
        }

        private void DrawSeries(Graphics g, List<PointF> list,
                                float xmin, float xmax, float ymin, float ymax,
                                Rectangle plot, Pen pen)
        {
            if (list.Count < 2) return;

            PointF prev = list[0];
            int prevX = XToPx(prev.X, xmin, xmax, plot);
            int prevY = YToPx(prev.Y, ymin, ymax, plot);

            for (int i = 1; i < list.Count; i++)
            {
                PointF p = list[i];

                if (p.X < xmin) continue;
                if (p.X > xmax) break;

                int x = XToPx(p.X, xmin, xmax, plot);
                int y = YToPx(p.Y, ymin, ymax, plot);
                g.DrawLine(pen, prevX, prevY, x, y);
                prevX = x;
                prevY = y;
            }
        }

        private static int XToPx(float x, float xmin, float xmax, Rectangle plot)
        {
            if (xmax - xmin <= 0) return plot.Left;
            return plot.Left + (int)((x - xmin) * plot.Width / (xmax - xmin));
        }

        private static int YToPx(float y, float ymin, float ymax, Rectangle plot)
        {
            if (ymax - ymin <= 0) return plot.Bottom;
            return plot.Bottom - (int)((y - ymin) * plot.Height / (ymax - ymin));
        }

        // === Kaydet ===
        private void btnKaydet_Click(object sender, EventArgs e)
        {
            if (comboKisi.SelectedValue == null)
            {
                MessageBox.Show("Lütfen kişi seçiniz.");
                return;
            }

            if (comboTest.SelectedItem == null)
            {
                MessageBox.Show("Lütfen test seçiniz.");
                return;
            }

            int kisiId = Convert.ToInt32(comboKisi.SelectedValue);
            string testAdi = comboTest.Text;

            double peakPower = EstimatePeakPowerFromSeries(seriesVert);
            double rsiMod = EstimateRsiFromSeries(seriesVert);
            double jumpHeight = EstimateJumpHeightFromSeries(seriesVert, Dt);

            try
            {
                using (var con = new SQLiteConnection(ConnStr))
                {
                    con.Open();
                    using (var cmd = new SQLiteCommand(@"
INSERT INTO test_sonuclari (kisi_id, test_adi, tarih, notlar, peak_power, rsi_modified, jump_height_cm)
VALUES (@kid, @test, @tarih, @not, @pp, @rsi, @jh);", con))
                    {
                        cmd.Parameters.AddWithValue("@kid", kisiId);
                        cmd.Parameters.AddWithValue("@test", testAdi);
                        cmd.Parameters.AddWithValue("@tarih", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
                        cmd.Parameters.AddWithValue("@not", DBNull.Value);
                        cmd.Parameters.AddWithValue("@pp", peakPower);
                        cmd.Parameters.AddWithValue("@rsi", rsiMod);
                        cmd.Parameters.AddWithValue("@jh", jumpHeight);
                        cmd.ExecuteNonQuery();
                    }
                }

                LoadSonuclarGrid();
                MessageBox.Show("Kayıt eklendi.", "Bilgi");
            }
            catch (Exception ex)
            {
                MessageBox.Show("Kayıt eklenemedi: " + ex.Message, "Hata");
            }
        }

        private static double EstimatePeakPowerFromSeries(List<PointF> s)
        {
            if (s.Count == 0) return 0;
            double maxF = s.Max(p => p.Y);
            return maxF * 2.1;
        }

        private static double EstimateRsiFromSeries(List<PointF> s)
        {
            if (s.Count < 5) return 0;
            double avg = s.Average(p => p.Y);
            double std = Math.Sqrt(s.Average(p => Math.Pow(p.Y - avg, 2)));
            return Math.Min(0.7, Math.Max(0, std / 2000.0));
        }

        private static double EstimateJumpHeightFromSeries(List<PointF> s, double dt)
        {
            if (s.Count < 2) return 0;
            double impulse = 0;
            for (int i = 1; i < s.Count; i++)
                impulse += (s[i - 1].Y + s[i].Y) * 0.5 * dt; // N*s
            return Math.Min(60.0, impulse / 1000.0); // cm
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            _timer?.Stop();
            CloseSerial();
            base.OnFormClosing(e);
        }
    }

    // === Kişi Ekle Dialog ===
    internal class KisiEkleForm : Form
    {
        public string Ad => txtAd.Text.Trim();
        public string Soyad => txtSoyad.Text.Trim();
        public string Notlar => txtNotlar.Text.Trim();

        private TextBox txtAd, txtSoyad, txtNotlar;
        private Button btnOk, btnCancel;

        public KisiEkleForm()
        {
            Text = "Kişi Ekle";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MaximizeBox = false;
            MinimizeBox = false;
            ClientSize = new Size(360, 200);

            var tl = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 4,
                Padding = new Padding(10)
            };

            tl.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 90));
            tl.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            tl.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
            tl.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
            tl.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            tl.RowStyles.Add(new RowStyle(SizeType.Absolute, 36));

            tl.Controls.Add(new Label
            {
                Text = "Ad:",
                TextAlign = ContentAlignment.MiddleRight,
                Dock = DockStyle.Fill
            }, 0, 0);

            txtAd = new TextBox { Dock = DockStyle.Fill };
            tl.Controls.Add(txtAd, 1, 0);

            tl.Controls.Add(new Label
            {
                Text = "Soyad:",
                TextAlign = ContentAlignment.MiddleRight,
                Dock = DockStyle.Fill
            }, 0, 1);

            txtSoyad = new TextBox { Dock = DockStyle.Fill };
            tl.Controls.Add(txtSoyad, 1, 1);

            tl.Controls.Add(new Label
            {
                Text = "Notlar:",
                TextAlign = ContentAlignment.MiddleRight,
                Dock = DockStyle.Fill
            }, 0, 2);

            txtNotlar = new TextBox
            {
                Dock = DockStyle.Fill,
                Multiline = true,
                ScrollBars = ScrollBars.Vertical
            };
            tl.Controls.Add(txtNotlar, 1, 2);

            var flow = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.RightToLeft
            };

            btnOk = new Button
            {
                Text = "Ekle",
                DialogResult = DialogResult.OK,
                Width = 80
            };
            btnCancel = new Button
            {
                Text = "Vazgeç",
                DialogResult = DialogResult.Cancel,
                Width = 80
            };

            flow.Controls.Add(btnOk);
            flow.Controls.Add(btnCancel);

            tl.Controls.Add(flow, 0, 3);
            tl.SetColumnSpan(flow, 2);

            Controls.Add(tl);

            AcceptButton = btnOk;
            CancelButton = btnCancel;
        }
    }
}
