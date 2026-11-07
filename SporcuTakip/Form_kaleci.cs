using Microsoft.Web.WebView2.Core;
using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Text.Json;
using System.Collections.Generic;
using System.Linq;
using System.Data.SQLite;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json.Serialization;
using System.Net.Sockets;
using Newtonsoft.Json.Linq;
using System.Threading;
using System.Net;
using System.Collections.Concurrent;

namespace SporcuTakip
{

    public partial class Form_kaleci : Form
    {
        private ConcurrentBag<StreamWriter> _clientWriters = new ConcurrentBag<StreamWriter>();
        private System.Diagnostics.Process _pointsProc;
        private TcpListener _listener;
        private CancellationTokenSource _cts;
        private Task _acceptTask;
        private const int PointsPort = 5055; // aynısı Python'a geçilecek
        private string PythonExe => "python"; // veya tam yol: @"C:\Python310\python.exe"
        private System.Windows.Forms.Timer _pointsTimer;
        private string _pointsJsonPath = Path.Combine(Path.GetTempPath(), "points_coords.json");
        private class PointJsonItem { public int id { get; set; } public int cx { get; set; } public int cy { get; set; } }
        private class PointJsonRoot { public List<PointJsonItem> points { get; set; } }
        const int MOD_NONE = 0x0000;
        const int WM_HOTKEY = 0x0312;
        const int HOTKEY_ID_F8 = 1001;
        const int VK_F8 = 0x77; // F8 sanal keycode:
        private TextBox[] _boxes;
        private readonly List<Point> _pts = new List<Point>(4);
        private bool _collectOne = false;
        private string DbPath => Path.Combine(Application.StartupPath, "goruntu_isleme.db");
        private string ConnStr => $"Data Source={DbPath};Version=3;";
        private int canlıFrameSayacı = 0;
        private string currentVideo = null;
        private bool isPlaying = false;
        private Stopwatch videoStopwatch = new Stopwatch();
        // WebView2 ekran görüntüsü oturumu için
        private string _screenSessionDir = null;  // ilk buton basışında oluşturulacak klasör
        private int _screenCount = 0;             // kaç screenshot alındı (opsiyonel sayaç)
        private readonly List<Point> _clickPts = new List<Point>();
        private TextBox[] _coordTextBoxes;
        private bool _collectOneClick = false; // Nokta Al butonu her basışta tek tık alır
        // WinAPI
        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, int fsModifiers, int vk);
        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);
        const int MOD_ALT = 0x0001;
        const int MOD_CONTROL = 0x0002;
        const int MOD_SHIFT = 0x0004; // const int MOD_WIN = 0x0008;  // genelde kullanma

        public Form_kaleci()
        {
            InitializeComponent();
            Butonlar();



            this.FormBorderStyle = FormBorderStyle.Sizable;
            this.MaximizeBox = true;
            this.MinimizeBox = true;
            this.StartPosition = FormStartPosition.CenterScreen;
            _boxes = new[] { textBox1, textBox2, textBox3, textBox4, textBox5 };

            //button2.Click += button_noktaAl_Click;
            //button3.Click += button_ciz_Click;
            //button4.Click += button_temizle_Click;
        }


        private static string GetDesktopFramesDir()
        {
            string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string oneDrive = Environment.GetEnvironmentVariable("OneDrive");

            var candidates = new List<string>
    {
        Path.Combine(oneDrive ?? "", "Desktop"),
        Path.Combine(oneDrive ?? "", "Masaüstü"),
        Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
        Path.Combine(home, "Masaüstü")
    };

            foreach (var p in candidates)
                if (!string.IsNullOrWhiteSpace(p) && Directory.Exists(p))
                {
                    string target = Path.Combine(p, "frameler");
                    Directory.CreateDirectory(target);
                    return target;
                }

            string fb = Path.Combine(home, "frameler");
            Directory.CreateDirectory(fb);
            return fb;
        }
        // Eskisi: private void butonlar(object sender, EventArgs e)
        private void Butonlar()
        {
            var grup1 = new[] { radioButton1, radioButton2, radioButton3 };
            var grup2 = new[] { radioButton4, radioButton5 };

            foreach (var rb in grup1)
            {
                rb.CheckedChanged += (s, ev) =>
                {
                    if (((RadioButton)s).Checked)
                    {
                        foreach (var other in grup1)
                            if (!ReferenceEquals(other, s))
                                other.Checked = false;
                    }
                };
            }

            foreach (var rb in grup2)
            {
                rb.CheckedChanged += (s, ev) =>
                {
                    if (((RadioButton)s).Checked)
                    {
                        foreach (var other in grup2)
                            if (!ReferenceEquals(other, s))
                                other.Checked = false;
                    }
                };
            }
        }


        private List<string> LoadKisiler()
        {
            var list = new List<string>();
            if (!File.Exists(DbPath))
            {
                MessageBox.Show("Veritabanı bulunamadı:\n" + DbPath);
                return list;
            }

            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var cmd = new SQLiteCommand("SELECT ad, COALESCE(soyad,'') FROM kisiler     where aktif=1 ORDER BY ad, soyad;", con))
                using (var rd = cmd.ExecuteReader())
                {
                    while (rd.Read())
                    {
                        var ad = rd.IsDBNull(0) ? "" : rd.GetString(0);
                        var soyad = rd.IsDBNull(1) ? "" : rd.GetString(1);
                        var full = string.IsNullOrWhiteSpace(soyad) ? ad : $"{ad} {soyad}";
                        if (!string.IsNullOrWhiteSpace(full)) list.Add(full.Trim());
                    }
                }
            }

            return list.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }
        private List<string> LoadSpinler()
        {
            var list = new List<string>();

            if (!File.Exists(DbPath))
            {
                MessageBox.Show("Veritabanı bulunamadı:\n" + DbPath);
                return list;
            }

            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var cmd = new SQLiteCommand("SELECT ad FROM spinler WHERE aktif = 1 ORDER BY ad;", con))
                using (var rd = cmd.ExecuteReader())
                {
                    while (rd.Read())
                    {
                        var ad = rd.IsDBNull(0) ? "" : rd.GetString(0).Trim();
                        if (!string.IsNullOrWhiteSpace(ad))
                            list.Add(ad);
                    }
                }
            }

            return list.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }
        private void StartSocketServer()
        {
            StopSocketServer(); // varsa kapat
            _cts = new CancellationTokenSource();
            _listener = new TcpListener(IPAddress.Loopback, PointsPort);
            _listener.Start();

            _acceptTask = Task.Run(async () =>
            {
                try
                {
                    while (!_cts.IsCancellationRequested)
                    {
                        var client = await _listener.AcceptTcpClientAsync();
                        _ = HandleClientAsync(client, _cts.Token);
                    }
                }
                catch (ObjectDisposedException) { /* listener stop */ }
                catch (Exception) { /* loglamak istersen buraya */ }
            });
        }
        private async Task HandleClientAsync(TcpClient client, CancellationToken ct)
        {
            using (client)
            using (var ns = client.GetStream())
            using (var sr = new StreamReader(ns))
            {
                client.NoDelay = true; // düşük gecikme
                while (!ct.IsCancellationRequested)
                {
                    string line = await sr.ReadLineAsync();
                    if (line == null) break; // bağlantı kapandı
                                             // Beklenen format: id,cx,cy
                    var parts = line.Split(',');
                    if (parts.Length == 3 &&
                        int.TryParse(parts[0], out int id) &&
                        int.TryParse(parts[1], out int cx) &&
                        int.TryParse(parts[2], out int cy))
                    {
                        SetPointTextBox(id, cx, cy);
                    }
                }
            }
        }
        private void SetPointTextBox(int id, int cx, int cy)
        {
            string txt = $"({cx}, {cy})";
            if (this.InvokeRequired)
            {
                this.BeginInvoke(new Action(() => SetPointTextBox(id, cx, cy)));
                return;
            }
            switch (id)
            {
                case 1: textBox1.Text = txt; break;
                case 2: textBox2.Text = txt; break;
                case 3: textBox3.Text = txt; break;
                case 4: textBox4.Text = txt; break;
                case 5: textBox5.Text = txt; break;
            }
        }
        //private async void button_show_points_Click(object sender, EventArgs e)
        //{
        //    try
        //    {
        //        string pyPath = Path.Combine(GetProjectRoot(), "test_corners.py"); // yeni dosya adı
        //        if (!File.Exists(pyPath))
        //        {
        //            MessageBox.Show("test_corners.py bulunamadı:\n" + pyPath, "Hata");
        //            return;
        //        }

        //        // Eski süreç varsa kapat
        //        try { if (_pointsProc != null && !_pointsProc.HasExited) _pointsProc.Kill(); } catch { }

        //        // TCP sunucuyu başlat
        //        StartSocketServer();

        //        // Python argümanları: host:port + nokta boyutu
        //        int dotSize = 3;
        //        string args = $"\"{pyPath}\" --socket 127.0.0.1:{PointsPort} --dot {dotSize} --screen cursor";

        //        var psi = new System.Diagnostics.ProcessStartInfo
        //        {
        //            FileName = PythonExe,
        //            Arguments = args,
        //            WorkingDirectory = GetProjectRoot(),
        //            UseShellExecute = false,
        //            RedirectStandardError = false,  // kilitlenmesin
        //            RedirectStandardOutput = false,
        //            CreateNoWindow = true
        //        };

        //        _pointsProc = System.Diagnostics.Process.Start(psi);

        //        // İsteğe bağlı: süreç bittiğinde sunucuyu durdur
        //        if (_pointsProc != null)
        //        {
        //            _pointsProc.EnableRaisingEvents = true;
        //            _pointsProc.Exited += (s2, e2) => { try { StopSocketServer(); } catch { } };
        //        }

        //        await Task.Delay(200); // Python’un bağlanması için minicik bekleme (zorunlu değil)
        //    }
        //    catch (Exception ex)
        //    {
        //        MessageBox.Show("Noktaları başlatma hatası:\n" + ex.Message, "Hata");
        //    }
        //}
        private async void button_show_points_Click(object sender, EventArgs e)
        {
            try
            {
                // test_corners.py yolu
                string root = GetProjectRoot();
                string pyPath = Path.Combine(root, "test_corners-kaleci.py"); // 5 noktalı yeni dosya

                if (!File.Exists(pyPath))
                {
                    MessageBox.Show("test_corners.py bulunamadı:\n" + pyPath, "Hata");
                    return;
                }

                // Eski süreç varsa kapat
                try
                {
                    if (_pointsProc != null && !_pointsProc.HasExited)
                        _pointsProc.Kill();
                }
                catch { }

                // TCP sunucuyu başlat (PointsPort burada kullanılacak)
                StartSocketServer();

                int dotSize = 10; // 3 çok küçük kalıyorsa biraz büyütebilirsin
                string args =
                    $"\"{pyPath}\" --socket 127.0.0.1:{PointsPort} --dot {dotSize} --screen cursor";

                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = PythonExe,           // python.exe tam yolu
                    Arguments = args,
                    WorkingDirectory = root,
                    UseShellExecute = false,
                    RedirectStandardError = false,  // kilitlenmesin diye kapalı
                    RedirectStandardOutput = false, // aynı nedenle kapalı
                    CreateNoWindow = true
                };

                _pointsProc = System.Diagnostics.Process.Start(psi);

                if (_pointsProc != null)
                {
                    _pointsProc.EnableRaisingEvents = true;
                    _pointsProc.Exited += (s2, e2) =>
                    {
                        try { StopSocketServer(); } catch { }
                    };
                }

                // Python’un bağlanması için minicik bekleme
                await Task.Delay(200);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Noktaları başlatma hatası:\n" + ex.Message, "Hata");
            }
        }

        private bool _hotkeyRegistered = false;
        private void EnsureF8Registered()
        {
            if (_hotkeyRegistered) return;
            bool ok = RegisterHotKey(this.Handle, HOTKEY_ID_F8, MOD_NONE, VK_F8);
            if (!ok)
            {
                int err = Marshal.GetLastWin32Error();
                MessageBox.Show("F8 hotkey kaydı başarısız. Hata kodu: " + err);
            }
            else _hotkeyRegistered = true;
        }
        private void UnregisterF8()
        {
            if (_hotkeyRegistered)
            {
                UnregisterHotKey(this.Handle, HOTKEY_ID_F8);
                _hotkeyRegistered = false;
            }
        }

        private void StopSocketServer()
        {
            try { _cts?.Cancel(); } catch { }
            try { _listener?.Stop(); } catch { }
            _cts = null;
            _listener = null;
            _acceptTask = null;
        }
        private void SetupCombos(IEnumerable<string> kisiler, IEnumerable<string> vurusStilleri)
        {
            // Kişiler
            var kList = kisiler.ToList();
            comboBox_kisi1.DataSource = new List<string>(kList);
            comboBox_kisi2.DataSource = new List<string>(kList);
            if (kList.Count > 0) comboBox_kisi1.SelectedIndex = 0;
            if (kList.Count > 1) comboBox_kisi2.SelectedIndex = 1;

            // Vuruş stilleri
            var vList = vurusStilleri.ToList();
            comboBox_vurus.DataSource = new List<string>(vList);
            if (vList.Count > 0) comboBox_vurus.SelectedIndex = 0;

        }
        private List<string> LoadVurusStilleri()
        {
            var list = new List<string>();
            if (!File.Exists(DbPath))
            {
                MessageBox.Show("Veritabanı bulunamadı:\n" + DbPath);
                return list;
            }

            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var cmd = new SQLiteCommand("SELECT ad FROM vurus_stilleri where aktif=1 ORDER BY ad;", con))
                using (var rd = cmd.ExecuteReader())
                {
                    while (rd.Read())
                    {
                        if (!rd.IsDBNull(0))
                            list.Add(rd.GetString(0).Trim());
                    }
                }
            }
            return list.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }

        private async void CoreWebView2_WebMessageReceived(object sender, CoreWebView2WebMessageReceivedEventArgs e)
        {
            string message = e.TryGetWebMessageAsString();

            // JSON mesajları (frame sayacı, vb.)
            if (!string.IsNullOrEmpty(message) && message.StartsWith("{"))
            {
                try
                {
                    var doc = System.Text.Json.JsonDocument.Parse(message);
                    var root = doc.RootElement;
                    if (root.TryGetProperty("type", out var t))
                    {
                        string type = t.GetString();
                        if (type == "frameCount")
                        {
                            canlıFrameSayacı = root.GetProperty("value").GetInt32();
                            labelFrameSayaci.Text = $"Frame: {canlıFrameSayacı}";
                        }
                        else if (type == "ended")
                        {
                            int total = root.GetProperty("frames").GetInt32();
                            labelFrameSayaci.Text = $"Bitti - Toplam Frame: {total}";
                        }
                    }
                }
                catch { /* yoksay */ }
                return;
            }

            // Oynatma/Duraklatma mesajları
            if (message == "playing")
            {
                if (!isPlaying)
                {
                    isPlaying = true;
                    videoStopwatch.Start();
                }
            }
            else if (message == "paused")
            {
                if (isPlaying)
                {
                    isPlaying = false;
                    videoStopwatch.Stop();
                }

                // === YENİ EKLENEN KISIM (GÜVENİLİR KAYIT İÇİN) ===
                // Video durduğunda o anki saniyeyi al ve label'a yaz.
                try
                {
                    var script = "document.getElementById('videoPlayer')?.currentTime || 0;";
                    string timeStr = await webView21.CoreWebView2.ExecuteScriptAsync(script);

                    // Gelen 'timeStr' "123.456" formatında olabilir
                    if (double.TryParse(timeStr, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double currentTime))
                    {
                        // === DEĞİŞİKLİK BURADA ===
                        // Eğer yeni video yüklenmişse veya currentTime 0'dan büyükse güncelle
                        if (IsNewVideoLoaded() || currentTime > 0)
                        {
                            // DB'ye kaydetmek için label'ı güncelle
                            label_kalinan_zaman.Text = SecondsToTimeString(currentTime);
                        }
                        // Aksi halde (yeni video yüklenmemiş ve currentTime 0'sa) veritabanındaki son değer kalsın
                    }
                }
                catch (Exception ex)
                {
                    Debug.WriteLine("Pause - currentTime alınamadı: " + ex.Message);
                }
                // === YENİ KISIM BİTTİ ===
            }
        }

        // Yeni video yüklenip yüklenmediğini kontrol eden yardımcı metod
        private bool IsNewVideoLoaded()
        {
            // Eğer currentVideo null değilse ve label_video_adi ile aynı değilse yeni video yüklenmiş demektir
            return !string.IsNullOrEmpty(currentVideo) && currentVideo != label_video_adi.Text;
        }
        private static string EnsureDir(string path)
        {
            Directory.CreateDirectory(path);
            return path;
        }
        private static string GetProjectRoot()
        {
            // Mevcut EXE klasörünü baz alıyoruz
            return Application.StartupPath;
        }
        private static string MakeSahaOutputDir()
        {
            // .\frameler\sahalar\<yyyyMMdd_HHmmss>\
            string root = Path.Combine(GetProjectRoot(), "frameler", "sahalar");
            string stamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            return EnsureDir(Path.Combine(root, stamp));
        }
        private async Task<(int exitCode, string stdout, string stderr)> RunPythonAsync(string exePath, string arguments, string workingDir)
        {
            var psi = new ProcessStartInfo
            {
                FileName = exePath,
                Arguments = arguments,
                WorkingDirectory = workingDir,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            using (var pr = new Process { StartInfo = psi })
            {
                pr.Start();
                string stdout = await pr.StandardOutput.ReadToEndAsync();
                string stderr = await pr.StandardError.ReadToEndAsync();
                pr.WaitForExit();
                return (pr.ExitCode, stdout, stderr);
            }
        }
        private async void button_cizgileri_bul_Click(object sender, EventArgs e)
        {
            var sw = Stopwatch.StartNew();

            try
            {
                // 1) Çıktı klasörünü oluştur
                string outDir = MakeSahaOutputDir();

                // 2) WebView2 ekran görüntüsünü kaydet
                string imgPath = Path.Combine(outDir, "saha1.png");
                await SaveWebViewScreenshotAsync(imgPath);

                if (!File.Exists(imgPath))
                {
                    MessageBox.Show("Ekran görüntüsü alınamadı (saha1.png).", "Hata");
                    return;
                }

                // 3) son.py yolunu doğrula
                string sonPy = Path.Combine(GetProjectRoot(), "son.py");
                if (!File.Exists(sonPy))
                {
                    MessageBox.Show("son.py bulunamadı:\n" + sonPy, "Hata");
                    return;
                }

                // 4) Python çağrısı
                string args = $"\"{sonPy}\" --img \"{imgPath}\" --out \"{outDir}\"";
                var (exitCode, stdout, stderr) = await RunPythonAsync(PythonExe, args, GetProjectRoot());

                if (!string.IsNullOrWhiteSpace(stderr))
                    Debug.WriteLine("[PY STDERR]\n" + stderr);

                if (exitCode != 0)
                {
                    MessageBox.Show("son.py çalışırken hata oluştu:\n" + stderr, "Python Hatası");
                    return;
                }

                // 5) corners.json oku
                string cornersPath = Path.Combine(outDir, "corners.json");
                if (!File.Exists(cornersPath))
                {
                    MessageBox.Show("corners.json bulunamadı. Model 4 köşeyi çıkaramamış olabilir.", "Uyarı");
                    return;
                }

                string json = File.ReadAllText(cornersPath, Encoding.UTF8);
                var corners = JsonSerializer.Deserialize<Corners>(json);

                if (corners?.TL == null || corners?.TR == null ||
                    corners?.BR == null || corners?.BL == null)
                {
                    MessageBox.Show("4 köşe okunamadı (corners.json boş veya eksik).", "Uyarı");
                    return;
                }

                // 6) TextBox’lara yaz
                textBox1.Text = $"({corners.TL[0]:0},{corners.TL[1]:0})";
                textBox2.Text = $"({corners.TR[0]:0},{corners.TR[1]:0})";
                textBox3.Text = $"({corners.BR[0]:0},{corners.BR[1]:0})";
                textBox4.Text = $"({corners.BL[0]:0},{corners.BL[1]:0})";
                textBox4.Text = $"({corners.BL[0]:0},{corners.BL[1]:0})";

                sw.Stop(); // süre ölçümü

                // 7) Mesaj oluştur
                string msg =
                    $"Saha 4 Köşe Koordinatları:\n\n" +
                    $"TL: {textBox1.Text}\n" +
                    $"TR: {textBox2.Text}\n" +
                    $"BR: {textBox3.Text}\n" +
                    $"BL: {textBox4.Text}\n\n" +
                    $"Toplam çalışma süresi: {sw.Elapsed.TotalSeconds:0.0} saniye\n" +
                    $"Klasör: {outDir}";

                try { Clipboard.SetText(msg); } catch { }

                MessageBox.Show(msg, "Çizgiler Bulundu", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show("İşlem hatası:\n" + ex.Message, "Hata");
            }
        }
        // Form_video_oynat sınıfının içinde:
        // Form_video_oynat sınıf alanları:
        private RadioButton[] _g1, _g2;

        private void SetupRadioGroups_NoPanel()
        {
            _g1 = new[] { radioButton1, radioButton2, radioButton3 };
            _g2 = new[] { radioButton4, radioButton5, radioButton6 };

            foreach (var rb in _g1.Concat(_g2))
            {
                rb.AutoCheck = false;            // WinForms'un default tek-grup davranışını kapat
                rb.Click += Radio_Click;         // Mouse tıklaması
                rb.KeyDown += Radio_KeyDown;     // Klavye (Space/Enter) desteği
            }
        }

        private void Radio_Click(object sender, EventArgs e)
        {
            ToggleInGroup((RadioButton)sender);
        }

        private void Radio_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Space || e.KeyCode == Keys.Enter)
            {
                e.Handled = true;
                ToggleInGroup((RadioButton)sender);
            }
        }

        private void ToggleInGroup(RadioButton rb)
        {
            var group = _g1.Contains(rb) ? _g1 : _g2;
            foreach (var r in group) r.Checked = false;
            rb.Checked = true;
        }


        private async void Form_video_oynat_Load(object sender, EventArgs e)
        {
            SetupRadioGroups_NoPanel();

            string htmlPath = Path.Combine(Application.StartupPath, "video_oynat.html");
            await webView21.EnsureCoreWebView2Async();
            webView21.CoreWebView2.Navigate("file:///" + htmlPath.Replace("\\", "/"));

            webView21.CoreWebView2.WebMessageReceived += CoreWebView2_WebMessageReceived;

            try
            {
                var kisiler = LoadKisiler();
                var vuruslar = LoadVurusStilleri();
                SetupCombos(kisiler, vuruslar);
                var spinList = LoadSpinler();
                comboBox_spin.DataSource = spinList;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Kişiler yüklenemedi:\n" + ex.Message);
            }

            // Form açıldığında son video ayarını DB'den çek
            LoadLastVideoAyarFromDb();

            // DB'den yüklenen veriyi kullan
            string sonVideoYolu = label_video_adi.Text?.Trim();
            string sonZaman = label_kalinan_zaman.Text?.Trim();

            if (!string.IsNullOrWhiteSpace(sonVideoYolu) && File.Exists(sonVideoYolu))
            {
                if (TryParseTimeToSeconds(sonZaman, out double sureSn) && sureSn > 0)
                {
                    // Videoyu yükle ve seek yap
                    PlayExternal(sonVideoYolu);
                    try
                    {
                        await Task.Delay(1000);
                        SendCommandObj(new { type = "pause" });
                        SendCommandObj(new { type = "seek", time = sureSn });
                        Debug.WriteLine($"Otomatik yükleme: {sonVideoYolu} - {sureSn}s");
                    }
                    catch (Exception ex)
                    {
                        Debug.WriteLine("Otomatik seek hatası: " + ex.Message);
                    }
                }
                else
                {
                    // Süre 0 ise sadece videoyu yükle
                    PlayExternal(sonVideoYolu);
                }
            }
        }

        private bool TryRegisterF8Hotkey(int modifiers = MOD_NONE)
        {
            // Önce varsa kaldır (yeniden kayıt denemelerinde ERROR_HOTKEY_ALREADY_REGISTERED önler)
            try { UnregisterHotKey(this.Handle, HOTKEY_ID_F8); } catch { }

            bool ok = RegisterHotKey(this.Handle, HOTKEY_ID_F8, modifiers, VK_F8);
            if (!ok)
            {
                int err = Marshal.GetLastWin32Error();
                Debug.WriteLine($"RegisterHotKey(F8) başarısız. Hata: {err}");
            }
            return ok;
        }
        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            // Uygulama genelinde F8’i sürekli açık tutmak istiyorsan:
            TryRegisterF8Hotkey(MOD_NONE);
        }
        private void UnregisterF8Hotkey()
        {
            try { UnregisterHotKey(this.Handle, HOTKEY_ID_F8); } catch { }
        }
        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_HOTKEY && m.WParam.ToInt32() == HOTKEY_ID_F8)
            {
                if (_collectOne)
                {
                    // Ekran koordinatı (mutlak)
                    var p = Cursor.Position;
                    int? idx = NextEmptyIndex();
                    if (idx != null)
                    {
                        _boxes[idx.Value].Text = $"({p.X}, {p.Y})";
                        if (_pts.Count < 4) _pts.Add(p);
                    }
                    _collectOne = false;
                }
            }
            base.WndProc(ref m);
        }
        private int? NextEmptyIndex()
        {
            for (int i = 0; i < _boxes.Length; i++)
                if (string.IsNullOrWhiteSpace(_boxes[i].Text)) return i;
            return null;
        }
        private bool TryParsePoint(string s, out Point p)
        {
            p = new Point();
            if (string.IsNullOrWhiteSpace(s)) return false;
            var t = s.Trim().Replace("(", "").Replace(")", "").Replace(" ", "");
            var parts = t.Split(',');
            if (parts.Length != 2) return false;
            int x, y;
            if (!int.TryParse(parts[0], out x)) return false;
            if (!int.TryParse(parts[1], out y)) return false;
            p = new Point(x, y);
            return true;
        }
        private void button_noktaAl_Click(object sender, EventArgs e)
        {
            if (NextEmptyIndex() == null)
            {
                MessageBox.Show("4 nokta dolu. Temizle'ye basın.");
                return;
            }
            _collectOne = true;
            MessageBox.Show("Nokta almak için F8'e basın (imleç neredeyse o nokta kaydedilir).");
            try { StopSocketServer(); } catch { }
            try { if (_pointsProc != null && !_pointsProc.HasExited) _pointsProc.Kill(); } catch { }
        }
        private Process _overlayProc;   // İster kapatırken temizlemek için saklayalım
                                        // 0..3 arasında dönen yazma imleci
        private int _nextIndex = 0;
        private int? FindNextEmptyFromPointer(TextBox[] order)
        {
            int n = order.Length;
            for (int step = 0; step < n; step++)
            {
                int idx = (_nextIndex + step) % n;
                if (string.IsNullOrWhiteSpace(order[idx].Text))
                    return idx;
            }
            return null; // hiç boş yok
        }


        // Sınıf alanı:
        private volatile bool _allFullNotified = false;

        // UI-thread güvenli set
        private void SafeSetText(TextBox tb, string text)
        {
            if (tb == null) return;
            if (tb.IsDisposed) return;

            if (tb.InvokeRequired)
            {
                try { tb.BeginInvoke(new Action(() => tb.Text = text)); } catch { }
            }
            else
            {
                tb.Text = text;
            }
        }

        // Tüm kutular doluyken uyarıyı sadece 1 kez göster
        private void NotifyAllFullOnce()
        {
            if (_allFullNotified) return;
            _allFullNotified = true;

            if (IsHandleCreated)
                BeginInvoke(new Action(() =>
                    MessageBox.Show("Tüm bölge kutuları dolu. Önce temizleyin veya düzenleyin.", "Uyarı",
                                    MessageBoxButtons.OK, MessageBoxIcon.Information)));
            else
                MessageBox.Show("Tüm bölge kutuları dolu. Önce temizleyin veya düzenleyin.", "Uyarı",
                                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        // Yeni bir çalıştırmaya başlarken sıfırlayın (butonda çağırın)
        private void ResetAllFullFlag() => _allFullNotified = false;

        private void FillNextSlot(string value)
        {
            if (string.IsNullOrWhiteSpace(value)) return;
            value = value.Trim();

            TextBox[] order = {
            textBox_vurulan_bolge,
            textBox_dustugu_bolge,
            textBox_nereden_geldi,
            textBox_bulusulan_bolge
        };

            foreach (var tb in order)
            {
                if (string.IsNullOrWhiteSpace(tb.Text))
                {
                    SafeSetText(tb, value);
                    return; // ilk boşu doldurduk, çık
                }
            }

            // Hepsi dolu: yalnızca bir kez uyar
            NotifyAllFullOnce();
        }


        private async void button_ciz_Click(object sender, EventArgs e)
        {
            // 5 nokta: 1–4 kale, 5 = top
            var pts = new List<Point>(5);

            for (int i = 0; i < 5; i++)
            {
                if (!TryParsePoint(_boxes[i].Text, out Point p))
                {
                    string msg;
                    if (i < 4)
                        msg = "Köşe " + (i + 1) + " boş/hatalı. Ör: 120,250";
                    else
                        msg = "Top noktası boş/hatalı. Ör: 120,250";

                    MessageBox.Show(msg);
                    return;
                }
                pts.Add(p);
            }

            // Kale köşeleri
            Point p1 = pts[0];
            Point p2 = pts[1];
            Point p3 = pts[2];
            Point p4 = pts[3];

            // 5. nokta = top
            Point ball = pts[4];

            int thickness = 3;
            int seconds = 0;  // istersen 30 yaparsın; 0 = sınırsız

            // Eğer projede PythonExe diye bir alan/property varsa onu kullan:
            string pythonExe = PythonExe;   // yoksa "python" bırakabilirsin
            string script = System.IO.Path.Combine(Application.StartupPath, "overlay_rect_kaleci.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("overlay_rect_kaleci.py bulunamadı:\n" + script);
                return;
            }

            // 4 kale köşesi + 5. nokta (top) + kalınlık + süre
            string args =
                $"\"{script}\" " +
                $"{p1.X} {p1.Y} " +
                $"{p2.X} {p2.Y} " +
                $"{p3.X} {p3.Y} " +
                $"{p4.X} {p4.Y} " +
                $"{ball.X} {ball.Y} " +
                $"{thickness} {seconds} " +
                "--pass";

            var psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = args,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WorkingDirectory = System.IO.Path.GetDirectoryName(script)
            };

            try
            {
                // Öncekini kapat (varsa)
                if (_overlayProc != null && !_overlayProc.HasExited)
                {
                    try { _overlayProc.Kill(); } catch { }
                    _overlayProc = null;
                }

                _overlayProc = new Process { StartInfo = psi, EnableRaisingEvents = true };

                // Python’dan gelen her satırı sırayla 4 kutuya yaz (mevcut FillNextSlot mantığın)
                _overlayProc.OutputDataReceived += (s2, e2) =>
                {
                    if (!string.IsNullOrWhiteSpace(e2.Data))
                    {
                        FillNextSlot(e2.Data);
                    }
                };

                _overlayProc.ErrorDataReceived += (s2, e2) =>
                {
                    // İstersen logla
                    // if (!string.IsNullOrWhiteSpace(e2.Data)) Debug.WriteLine("[PY] " + e2.Data);
                };

                _overlayProc.Exited += (s2, e2) =>
                {
                    // Kapanınca yapılacak bir şey varsa ekleyebilirsin
                };

                _overlayProc.Start();
                _overlayProc.BeginOutputReadLine();
                _overlayProc.BeginErrorReadLine();

                // UI kilitlenmesin
                await Task.Run(() => _overlayProc.WaitForExit());
            }
            catch (Exception ex)
            {
                MessageBox.Show("Çalıştırma hatası:\n" + ex.Message);
            }
        }

        //private async void button_ciz_Click(object sender, EventArgs e)
        //{

        //    // 4 nokta oku
        //    var pts = new List<Point>(4);
        //    for (int i = 0; i < 4; i++)
        //    {
        //        if (!TryParsePoint(_boxes[i].Text, out Point p))
        //        {
        //            MessageBox.Show("Köşe " + (i + 1) + " boş/hatalı. Ör: (120, 250)");
        //            return;
        //        }
        //        pts.Add(p);
        //    }

        //    int thickness = 3;
        //    int seconds = 0;  // ister 30 yaparsın; 0 = sınırsız

        //    string pythonExe = "python";
        //    string script = System.IO.Path.Combine(Application.StartupPath, "overlay_rect.py");
        //    if (!System.IO.File.Exists(script))
        //    {
        //        MessageBox.Show("overlay_rect.py bulunamadı:\n" + script);
        //        return;
        //    }

        //    // DİKKAT: --pass YOK (X tuşu için odak gerekli), sadece --silent kullan
        //    string args =
        //        $"\"{script}\" " +
        //        $"{pts[0].X} {pts[0].Y} " +
        //        $"{pts[1].X} {pts[1].Y} " +
        //        $"{pts[2].X} {pts[2].Y} " +
        //        $"{pts[3].X} {pts[3].Y} " +
        //        $"{thickness} {seconds} " +
        //        "--pass";

        //    var psi = new ProcessStartInfo
        //    {
        //        FileName = pythonExe,
        //        Arguments = args,
        //        UseShellExecute = false,
        //        CreateNoWindow = true,
        //        RedirectStandardOutput = true,
        //        RedirectStandardError = true,
        //        WorkingDirectory = System.IO.Path.GetDirectoryName(script)
        //    };

        //    try
        //    {
        //        // Öncekini kapat (varsa)
        //        if (_overlayProc != null && !_overlayProc.HasExited)
        //        {
        //            try { _overlayProc.Kill(); } catch { }
        //            _overlayProc = null;
        //        }

        //        _overlayProc = new Process { StartInfo = psi, EnableRaisingEvents = true };

        //        // Python’dan gelen her satırı sırayla 4 kutuya yaz
        //        _overlayProc.OutputDataReceived += (s2, e2) =>
        //        {
        //            if (!string.IsNullOrWhiteSpace(e2.Data))
        //            {
        //                FillNextSlot(e2.Data);
        //            }
        //        };

        //        _overlayProc.ErrorDataReceived += (s2, e2) =>
        //        {
        //            // İstersen logla
        //            // if (!string.IsNullOrWhiteSpace(e2.Data)) Debug.WriteLine("[PY] " + e2.Data);
        //        };

        //        _overlayProc.Exited += (s2, e2) =>
        //        {
        //            // Kapanınca yapılacak bir şey varsa ekle
        //        };

        //        _overlayProc.Start();
        //        _overlayProc.BeginOutputReadLine();
        //        _overlayProc.BeginErrorReadLine();

        //        // UI kilitlenmesin
        //        await Task.Run(() => _overlayProc.WaitForExit());
        //    }
        //    catch (Exception ex)
        //    {
        //        MessageBox.Show("Çalıştırma hatası:\n" + ex.Message);
        //    }
        //}

        private void button_temizle_Click(object sender, EventArgs e)
        {
            // 1. Orijinal temizleme (4 köşe nokta kutuları)
            foreach (var tb in _boxes) tb.Clear();
            _pts.Clear();
            _collectOne = false; // F8 ile nokta almayı durdur

            // --- İsteğiniz üzerine eklenen kod ---

            // 2. Portla haberleşen "Noktalar" (test_corners.py) sürecini durdur
            try
            {
                if (_pointsProc != null && !_pointsProc.HasExited)
                {
                    _pointsProc.Kill();
                    _pointsProc = null;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine("Nokta süreci kapatılırken hata: " + ex.Message);
            }

            // 3. Nokta sunucusunu (Port 5055) durdur
            try
            {
                StopSocketServer(); // Bu fonksiyon _listener ve _cts'i güvenle kapatır
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine("Socket sunucu kapatılırken hata: " + ex.Message);
            }

            // 4. "Çiz" (overlay_rect.py) sürecini durdur
            try
            {
                if (_overlayProc != null && !_overlayProc.HasExited)
                {
                    _overlayProc.Kill();
                    _overlayProc = null;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine("Overlay süreci kapatılırken hata: " + ex.Message);
            }
        }
        //private void button_temizle_Click(object sender, EventArgs e)
        //{
        //    foreach (var tb in _boxes) tb.Clear();
        //    _pts.Clear();
        //    _collectOne = false;
        //}
        private sealed class Corners
        {
            public float[] TL { get; set; }
            public float[] TR { get; set; }
            public float[] BR { get; set; }
            public float[] BL { get; set; }
        }

        private void PlayExternal(string inputPathOrUrl, double? fps = null)
        {
            string pathToSend;

            if (Uri.IsWellFormedUriString(inputPathOrUrl, UriKind.Absolute))
            {
                pathToSend = inputPathOrUrl;
            }
            else
            {
                if (!File.Exists(inputPathOrUrl))
                {
                    MessageBox.Show("Video bulunamadı:\n" + inputPathOrUrl);
                    return;
                }
                pathToSend = new Uri(inputPathOrUrl).AbsoluteUri;
            }

            // Yeni video yüklendiğinde currentVideo'yu güncelle
            currentVideo = inputPathOrUrl;

            // Label'da video yolunu göster
            //label_video_adi.Text = inputPathOrUrl;
            label_video_adi.Text = Path.GetFileNameWithoutExtension(inputPathOrUrl);

            isPlaying = false;

            if (fps.HasValue && fps.Value > 0)
                SendCommandObj(new { type = "play", path = pathToSend, fps = fps.Value });
            else
                SendCommandObj(new { type = "play", path = pathToSend });
        }

        private void button_dosyaAc_Click(object sender, EventArgs e)
        {
            using (var ofd = new OpenFileDialog
            {
                Title = "Video seç",
                Filter = "Video Dosyaları|*.mp4;*.mkv;*.mov;*.avi;*.webm|Tüm Dosyalar|*.*",
                Multiselect = false
            })
            {
                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    PlayExternal(ofd.FileName);
                    // FPS biliyorsan: PlayExternal(ofd.FileName, 30);
                }
            }
        }
        private void SendCommandObj(object obj)
        {
            string json = JsonSerializer.Serialize(obj);
            webView21.CoreWebView2.PostWebMessageAsJson(json);
        }
        private int? GetKisiIdByFullName(string full)
        {
            if (string.IsNullOrWhiteSpace(full)) return null;
            string ad = full.Trim();
            string soyad = "";
            var parts = ad.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length > 1)
            {
                ad = string.Join(" ", parts.Take(parts.Length - 1));
                soyad = parts.Last();
            }

            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var cmd = new SQLiteCommand(
                    "SELECT id FROM kisiler WHERE ad=@ad AND COALESCE(soyad,'')=COALESCE(@soyad,'') LIMIT 1;", con))
                {
                    cmd.Parameters.AddWithValue("@ad", ad);
                    cmd.Parameters.AddWithValue("@soyad", soyad);
                    var obj = cmd.ExecuteScalar();
                    return obj == null ? (int?)null : Convert.ToInt32(obj);
                }
            }
        }
        private int? GetVurusIdByName(string name)
        {
            if (string.IsNullOrWhiteSpace(name)) return null;
            using (var con = new SQLiteConnection(ConnStr))
            {
                con.Open();
                using (var cmd = new SQLiteCommand(
                    "SELECT id FROM vurus_stilleri WHERE ad=@ad LIMIT 1;", con))
                {
                    cmd.Parameters.AddWithValue("@ad", name.Trim());
                    var obj = cmd.ExecuteScalar();
                    return obj == null ? (int?)null : Convert.ToInt32(obj);
                }
            }
        }
        private int? ParseSpinId(string txt)
        {
            if (string.IsNullOrWhiteSpace(txt)) return null;
            // kendi eşleştirmeni burada düzenleyebilirsin
            txt = txt.Trim().ToLowerInvariant();
            if (txt.Contains("topspin")) return 1;
            if (txt.Contains("backspin") || txt.Contains("slice") || txt.Contains("underspin")) return 2;
            if (txt.Contains("flat")) return 3;
            // doğrudan 1/2/3 seçiliyorsa:
            if (int.TryParse(txt, out var n) && (n == 1 || n == 2 || n == 3)) return n;
            return null;
        }
        private int? ReadGroupValue(RadioButton r1, RadioButton r2, RadioButton r3)
        {
            if (r1.Checked) return 1;
            if (r2.Checked) return 2;
            if (r3.Checked) return 3;
            return null;
        }

        private async void button_kaydet_Click(object sender, EventArgs e)
        {
            try
            {
                // 0) Video ve frame kontrolleri
                if (string.IsNullOrWhiteSpace(currentVideo) || !File.Exists(currentVideo))
                {
                    MessageBox.Show("Video yolu boş/geçersiz. Önce video yükleyin.");
                    return;
                }
                if (!int.TryParse(textBox_frame_bas.Text.Trim(), out var fStart) ||
                    !int.TryParse(textBox_frame_bit.Text.Trim(), out var fEnd))
                {
                    MessageBox.Show("Frame başlangıç/bitiş sayısal olmalı.");
                    return;
                }

                // Radio grupları:
                // 1-2-3 => yukseklik
                // 4-5-6 => kademe
                int? yukseklik = ReadGroupValue(radioButton1, radioButton2, radioButton3);
                int? kademe = ReadGroupValue(radioButton4, radioButton5, radioButton6);

                if (yukseklik == null)
                {
                    MessageBox.Show("Lütfen 1-2-3 grubundan bir yükseklik seçin.");
                    return;
                }
                if (kademe == null)
                {
                    MessageBox.Show("Lütfen 4-5-6 grubundan bir kademe seçin.");
                    return;
                }


                if (fStart > fEnd) (fStart, fEnd) = (fEnd, fStart);

                // 1) Formdan alanları topla
                var kisi1Id = GetKisiIdByFullName(comboBox_kisi1.Text);
                var kisi2Id = GetKisiIdByFullName(comboBox_kisi2.Text);
                var vurusId = GetVurusIdByName(comboBox_vurus.Text);
                var spinId = ParseSpinId(comboBox_spin.Text);
                int basarili = checkBox_atis_basarili_mi.Checked ? 1 : 0;

                if (kisi1Id == null || kisi2Id == null)
                {
                    MessageBox.Show("Kişi(ler) veritabanında bulunamadı. (Kişi kaydı ekleyin veya listeden seçin.)");
                    return;
                }
                if (vurusId == null)
                {
                    MessageBox.Show("Vuruş stili veritabanında bulunamadı. (Stil ekleyin veya listeden seçin.)");
                    return;
                }

                string vurulanBolge = textBox_vurulan_bolge.Text.Trim();
                string dustuguBolge = textBox_dustugu_bolge.Text.Trim();
                string bulusulanBolge = textBox_bulusulan_bolge.Text.Trim();
                string neredenGeldi = textBox_nereden_geldi.Text.Trim();
                int? spinIdFromCombo = null;
                if (comboBox_spin.SelectedItem != null)
                {
                    // "1 - Topspin" → "1"
                    var raw = comboBox_spin.SelectedItem.ToString().Split('-')[0].Trim();
                    if (int.TryParse(raw, out var parsed))
                        spinIdFromCombo = parsed;
                }


                // (opsiyonel) hız textbox'ınız yoksa NULL geçeceğiz:
                object topHizi = DBNull.Value;

                // 2) DB'ye ekle ve yeni id al
                long id;
                using (var con = new SQLiteConnection(ConnStr))
                {
                    con.Open();
                    using (var tr = con.BeginTransaction())


                    using (var cmd = new SQLiteCommand(@"
    INSERT INTO kayitlar
    (kisi_id, kisi2_id, vurus_id,
     frame_baslangic, frame_bitis,
     vurulan_bolge, dustugu_bolge, bulusulan_bolge, nereden_geldi,
     spin_id, atis_basarili_mi, top_hizi,
     video_yolu, kayit_zamani,
     kademe, yukseklik)   -- << EKLENDİ
    VALUES
    (@k1, @k2, @v,
     @fs, @fe,
     @vb, @db, @bb, @ng,
     @spin, @basarili, @hiz,
     @video, @ts,
     @kademe, @yuk)       -- << EKLENDİ
    ;
    SELECT last_insert_rowid();", con, tr))
                    {
                        cmd.Parameters.AddWithValue("@k1", kisi1Id.Value);
                        cmd.Parameters.AddWithValue("@k2", kisi2Id.Value);
                        cmd.Parameters.AddWithValue("@v", vurusId.Value);
                        cmd.Parameters.AddWithValue("@fs", fStart);
                        cmd.Parameters.AddWithValue("@fe", fEnd);
                        cmd.Parameters.AddWithValue("@vb", string.IsNullOrWhiteSpace(vurulanBolge) ? (object)DBNull.Value : vurulanBolge);
                        cmd.Parameters.AddWithValue("@db", string.IsNullOrWhiteSpace(dustuguBolge) ? (object)DBNull.Value : dustuguBolge);
                        cmd.Parameters.AddWithValue("@bb", string.IsNullOrWhiteSpace(bulusulanBolge) ? (object)DBNull.Value : bulusulanBolge);
                        cmd.Parameters.AddWithValue("@ng", string.IsNullOrWhiteSpace(neredenGeldi) ? (object)DBNull.Value : neredenGeldi);

                        // spin_id: istersen SelectedIndex yerine SelectedValue/ID kullanabilirsin
                        cmd.Parameters.AddWithValue("@spin", comboBox_spin.SelectedIndex);
                        cmd.Parameters.AddWithValue("@basarili", basarili);
                        cmd.Parameters.AddWithValue("@hiz", topHizi);
                        cmd.Parameters.AddWithValue("@video", currentVideo);
                        cmd.Parameters.AddWithValue("@ts", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));

                        // << YENİ PARAMETRELER >>
                        cmd.Parameters.AddWithValue("@kademe", kademe.Value);
                        cmd.Parameters.AddWithValue("@yuk", yukseklik.Value);

                        id = (long)(cmd.ExecuteScalar() ?? 0);
                        tr.Commit();
                    }

                }

                // 3) frameler klasöründeki son oluşturulan klasörü bul ve adını id ile değiştir
                string root = GetDesktopFramesDir();
                if (Directory.Exists(root))
                {
                    // Son oluşturulan klasörü bul (CreationTime'e göre)
                    var lastDir = new DirectoryInfo(root)
                        .GetDirectories()
                        .OrderByDescending(d => d.CreationTime)
                        .FirstOrDefault();

                    if (lastDir != null)
                    {
                        string newDirPath = Path.Combine(root, id.ToString());

                        try
                        {
                            // Ad değişikliği yap
                            Directory.Move(lastDir.FullName, newDirPath);
                            MessageBox.Show($"Kayıt (ID={id}) eklendi.\nKlasör yeniden adlandırıldı: {newDirPath}",
                                            "Tamam", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        }
                        catch (Exception ex)
                        {
                            MessageBox.Show($"Klasör adı değiştirilirken hata oluştu:\n{ex.Message}",
                                            "Uyarı", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        }
                    }
                    else
                    {
                        MessageBox.Show("frameler klasöründe hiçbir klasör bulunamadı.", "Uyarı",
                                        MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
                else
                {
                    MessageBox.Show("frameler klasörü bulunamadı.", "Uyarı",
                                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }


                // 4) temizle (isteğe bağlı)
                textBox_frame_bas.Clear();
                textBox_frame_bit.Clear();

                textBox_vurulan_bolge.Clear();
                textBox_dustugu_bolge.Clear();
                textBox_bulusulan_bolge.Clear();
                textBox_nereden_geldi.Clear();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Hata: " + ex.Message, "Hata",
                                MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            DegistirKisiler();
        }
        private async Task<int> GetCurrentFrameAsync()
        {
            if (webView21?.CoreWebView2 == null) return -1;

            var script = @"
    (function(){
        const v = document.getElementById('videoPlayer');
        // 1) overlay yazısından oku (FPS: .. Render: .. Kare: N)
        const fc = document.getElementById('frameCounter');
        if (fc && fc.textContent) {
            const m = fc.textContent.match(/Kare:\s*(\d+)/i);
            if (m) return parseInt(m[1], 10);
        }
        // 2) sayaç değişkenleri
        if (typeof window.__frameCount === 'number') return window.__frameCount;
        if (typeof window.__renderCount === 'number') return window.__renderCount;

        // 3) Playback quality API
        if (v && v.getVideoPlaybackQuality) {
            const q = v.getVideoPlaybackQuality();
            if (q && typeof q.totalVideoFrames === 'number' && q.totalVideoFrames > 0)
                return Math.round(q.totalVideoFrames);
        }

        // 4) fallback: currentTime * fps
        if (!v) return -1;
        let fps = window.__fps;
        if (!(fps > 0)) fps = 25; // tahmini
        return Math.round(v.currentTime * fps);
    })();";

            var res = await webView21.ExecuteScriptAsync(script);
            if (int.TryParse(res?.Trim('"'), out int val)) return val;
            return -1;
        }
        private async Task SaveWebViewScreenshotAsync(string filePath)
        {
            await webView21.EnsureCoreWebView2Async();
            var dir = Path.GetDirectoryName(filePath);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);

            using (var fs = new FileStream(filePath, FileMode.Create, FileAccess.Write))
                await webView21.CoreWebView2
                    .CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, fs);
        }
        private async void button_frame_al_Click(object sender, EventArgs e)
        {
            try
            {
                // 1) O anki frame
                int currentFrame = await GetCurrentFrameAsync();
                if (currentFrame < 0)
                {
                    MessageBox.Show("Anlık frame değeri alınamadı. Video yüklü ve oynatılabilir mi?");
                    return;
                }

                // 2) İlk tıklamada timestamp’li klasör oluştur
                if (string.IsNullOrEmpty(_screenSessionDir))
                {
                    string root = GetDesktopFramesDir();                 // ...\Masaüstü\frameler
                    string stamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                    _screenSessionDir = Path.Combine(root, stamp);
                    Directory.CreateDirectory(_screenSessionDir);
                    _screenCount = 0;
                }

                // 3) Frame değerini textBox'lara yaz
                if (string.IsNullOrWhiteSpace(textBox_frame_bas.Text))
                {
                    textBox_frame_bas.Text = currentFrame.ToString();
                }
                else if (string.IsNullOrWhiteSpace(textBox_frame_bit.Text))
                {
                    textBox_frame_bit.Text = currentFrame.ToString();
                }

                // 4) Dosya adı: f<frame>.png (çakışma önleme ile)
                string fileName = $"f{currentFrame:000000}.png";
                string outPath = Path.Combine(_screenSessionDir, fileName);

                if (File.Exists(outPath))
                {
                    int k = 2;
                    string nameNoExt = Path.GetFileNameWithoutExtension(fileName);
                    string ext = Path.GetExtension(fileName);
                    while (File.Exists(outPath))
                    {
                        outPath = Path.Combine(_screenSessionDir, $"{nameNoExt}_{k}{ext}");
                        k++;
                    }
                }

                // 5) WebView2 ekran görüntüsünü kaydet
                await SaveWebViewScreenshotAsync(outPath);

                _screenCount++;

                // 6) İkinci tıklamadan sonra oturumu bitir
                if (_screenCount >= 2)
                {
                    _screenSessionDir = null;
                    _screenCount = 0;
                    MessageBox.Show("2 frame alındı ve klasör oluşturuldu.",
                                    "Bilgi", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Ekran görüntüsü alınamadı: " + ex.Message,
                    "Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
        private void button_kisi_degistir_Click(object sender, EventArgs e)
        {
            DegistirKisiler();
        }
        private void DegistirKisiler()
        {
            // Seçili değerleri al
            var temp = comboBox_kisi1.SelectedItem;
            comboBox_kisi1.SelectedItem = comboBox_kisi2.SelectedItem;
            comboBox_kisi2.SelectedItem = temp;

            // Eğer SelectedItem yerine metin kullanıyorsan, şu şekilde değiştir:
            // string temp = combobox_kisi1.Text;
            // combobox_kisi1.Text = combobox_kisi2.Text;
            // combobox_kisi2.Text = temp;
        }
        private void BroadcastQuit()
        {
            foreach (var sw in _clientWriters)
            {
                try { sw.WriteLine("QUIT"); } catch { /* yoksay */ }
            }
        }


        // Textbox sırası için indeks (0.._boxes.Length-1)
        private int _slotIndex = 0;

        // Boşsa sırayla doldur, doluysa round-robin


        // UI-thread güvenli sarmalayıcı
        private void FillNextSlotThreadSafe(string line)
        {
            if (IsDisposed) return;
            if (InvokeRequired)
            {
                try { BeginInvoke(new Action(() => FillNextSlot(line))); } catch { }
            }
            else
            {
                FillNextSlot(line);
            }
        }

        // Çalıştırma öncesi slot reset (isteğe bağlı temizleme)
        private void ResetSlots(bool clearTexts)
        {
            _slotIndex = 0;
            if (clearTexts)
            {
                foreach (var tb in _boxes) tb.Text = string.Empty;
            }
        }

        private void comboBox_spin_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        /// <summary>
        /// Uygulama açıldığında DB'den son kaydı okuyup label'lara yazar.
        /// </summary>

        /// <summary>
        /// Uygulama açıldığında DB'den son kaydı okuyup label'lara yazar.
        /// </summary>
        private void LoadLastVideoAyarFromDb()
        {
            try
            {
                if (!File.Exists(DbPath))
                {
                    // Veritabanı yoksa default değerler
                    SetDefaultVideoLabels();
                    return;
                }

                using (var con = new SQLiteConnection(ConnStr))
                {
                    con.Open();
                    EnsureVideoAyarlarTable(con);

                    using (var cmd = new SQLiteCommand(@"
                SELECT video_yolu, son_kalinan_sure
                FROM video_ayarlar
                WHERE son_kalinan_sure > 0
                ORDER BY kayit_tarihi DESC
                LIMIT 1;", con))
                    using (var rd = cmd.ExecuteReader())
                    {
                        if (rd.Read())
                        {
                            string yol = rd.IsDBNull(0) ? "" : rd.GetString(0);
                            double sureSn = rd.IsDBNull(1) ? 0 : rd.GetDouble(1);

                            if (!string.IsNullOrWhiteSpace(yol) && sureSn > 0)
                            {
                                label_video_adi.Text = yol;
                                label_kalinan_zaman.Text = SecondsToTimeString(sureSn);
                            }
                            else
                            {
                                SetDefaultVideoLabels();
                            }
                        }
                        else
                        {
                            // Hiç kayıt yoksa default değerler
                            SetDefaultVideoLabels();
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Video ayarları yüklenirken hata oluştu: " + ex.Message);
                SetDefaultVideoLabels();
            }
        }

        // Default label değerlerini ayarlayan yardımcı metod
        private void SetDefaultVideoLabels()
        {
            label_video_adi.Text = "";
            label_kalinan_zaman.Text = "00:00:00";
        }


        // OnFormClosing metodunu da güncelleyelim
        // OnFormClosing metodunu da güncelleyelim
        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            try { UnregisterF8(); } catch { }
            try { StopSocketServer(); } catch { }
            try { if (_pointsProc != null && !_pointsProc.HasExited) _pointsProc.Kill(); } catch { }

            // === "db ye kaydet" BÖLÜMÜ (Basitleştirilmiş Hali) ===
            try
            {
                // 1. O anki video adını label'a yaz
                // (SaveVideoAyarToDb'nin doğru videoyu alması için)
                if (!string.IsNullOrWhiteSpace(currentVideo))
                {
                    label_video_adi.Text = currentVideo;
                }

                // 2. Kaydet'i çağır.
                // (label_kalinan_zaman ZATEN video duraklatıldığında
                // CoreWebView2_WebMessageReceived içinde güncellenmişti)
                SaveVideoAyarToDb();
            }
            catch (Exception ex)
            {
                Debug.WriteLine("SaveVideoAyarToDb hatası: " + ex.Message);
            }
            // === KAYIT BÖLÜMÜ BİTTİ ===

            base.OnFormClosing(e);
        }

        // === VIDEO_AYARLAR TABLOSU İŞLEMLERİ ===
        private void EnsureVideoAyarlarTable(SQLiteConnection con)
        {
            using (var cmd = new SQLiteCommand(@"
        CREATE TABLE IF NOT EXISTS video_ayarlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kayit_tarihi TEXT NOT NULL,
            video_yolu TEXT NOT NULL,
            son_kalinan_sure REAL NOT NULL
        );", con))
            {
                cmd.ExecuteNonQuery();
            }
        }

        private void SaveVideoAyarToDb()
        {
            try
            {
                if (!File.Exists(DbPath))
                    return;

                string videoYolu = label_video_adi.Text?.Trim();
                string zamanText = label_kalinan_zaman.Text?.Trim();

                // 1) Video yolu yoksa hiç kayıt yapma
                if (string.IsNullOrWhiteSpace(videoYolu))
                    return;

                // 2) Süre etiketi boşsa da kaydetme (eski değeri ezmemek için)
                if (string.IsNullOrWhiteSpace(zamanText))
                    return;

                // 3) Süreyi saniyeye çevir
                if (!TryParseTimeToSeconds(zamanText, out double sureSn))
                {
                    // format çözülemediyse kayıt yapmayalım
                    return;
                }

                // 4) 0 veya negatif süreleri kaydetme
                if (sureSn <= 0)
                {
                    return;
                }

                // 5) Gerçekten anlamlı bir süre varsa DB'ye yaz
                using (var con = new SQLiteConnection(ConnStr))
                {
                    con.Open();
                    EnsureVideoAyarlarTable(con);

                    using (var cmd = new SQLiteCommand(@"
                INSERT INTO video_ayarlar (kayit_tarihi, video_yolu, son_kalinan_sure)
                VALUES (@tarih, @yol, @sure);", con))
                    {
                        cmd.Parameters.AddWithValue("@tarih", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
                        cmd.Parameters.AddWithValue("@yol", videoYolu);
                        cmd.Parameters.AddWithValue("@sure", sureSn);   // burası artık > 0

                        cmd.ExecuteNonQuery();
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Video ayarları kaydedilirken hata oluştu: " + ex.Message);
            }
        }



        /// <summary>
        /// "hh:mm:ss", "mm:ss" gibi formatları saniyeye çevirir.
        /// </summary>
        private bool TryParseTimeToSeconds(string text, out double seconds)
        {
            seconds = 0;
            if (string.IsNullOrWhiteSpace(text))
                return false;

            // Saat:dk:sn parçala
            var parts = text.Trim().Split(':');
            int h = 0, m = 0;
            double s = 0;

            try
            {
                if (parts.Length == 3)
                {
                    h = int.Parse(parts[0]);
                    m = int.Parse(parts[1]);
                    s = double.Parse(parts[2].Replace(',', '.'), System.Globalization.CultureInfo.InvariantCulture);
                }
                else if (parts.Length == 2)
                {
                    m = int.Parse(parts[0]);
                    s = double.Parse(parts[1].Replace(',', '.'), System.Globalization.CultureInfo.InvariantCulture);
                }
                else if (parts.Length == 1)
                {
                    s = double.Parse(parts[0].Replace(',', '.'), System.Globalization.CultureInfo.InvariantCulture);
                }
                else
                {
                    return false;
                }

                seconds = h * 3600 + m * 60 + s;
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Saniye cinsinden süreyi "hh:mm:ss" string'e çevirir.
        /// </summary>
        private string SecondsToTimeString(double seconds)
        {
            if (seconds < 0) seconds = 0;
            var ts = TimeSpan.FromSeconds(seconds);
            // 2 saat üstü bile olsa sorun yok, hh:mm:ss
            return $"{(int)ts.TotalHours:00}:{ts.Minutes:00}:{ts.Seconds:00}";
        }


        private void button_otomatik_Click(object sender, EventArgs e)
        {
            try
            {
                // court_detect.py, EXE ile aynı klasörde olsun
                string scriptPath = Path.Combine(
                    AppDomain.CurrentDomain.BaseDirectory,
                    "court_detect.py"
                );

                if (!File.Exists(scriptPath))
                {
                    MessageBox.Show("court_detect.py bulunamadı:\n" + scriptPath);
                    return;
                }

                var psi = new ProcessStartInfo
                {
                    FileName = "python",                 // Ortamda python PATH'te olmalı
                    Arguments = $"\"{scriptPath}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = Encoding.UTF8,
                    StandardErrorEncoding = Encoding.UTF8
                    // WorkingDirectory VERMİYORUZ → başka PC'de de çalışsın
                };

                string stdout;
                string stderr;

                using (var p = Process.Start(psi))
                {
                    stdout = p.StandardOutput.ReadToEnd();
                    stderr = p.StandardError.ReadToEnd();
                    p.WaitForExit();
                }

                // Hata çıktılarını görmek istersen:
                if (!string.IsNullOrWhiteSpace(stderr))
                {
                    Debug.WriteLine("PY STDERR:\n" + stderr);
                }

                // Python bazen log da basıyor olabilir. 
                // Bu yüzden stdout'un **son dolu satırını** JSON kabul ediyoruz.
                string[] lines = stdout
                    .Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);

                if (lines.Length == 0)
                {
                    MessageBox.Show("Python'dan çıktı alınamadı.\nstdout boş.");
                    return;
                }

                string jsonLine = lines.Last();  // SON satır JSON

                JObject obj;
                try
                {
                    obj = JObject.Parse(jsonLine);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        "JSON parse hatası:\n" + ex.Message +
                        "\n\nGelen stdout:\n" + stdout);
                    return;
                }

                // Python error alanı dönerse:
                if (obj["error"] != null)
                {
                    MessageBox.Show("Python hata döndürdü:\n" + obj["error"]);
                    return;
                }

                // tl, tr, ml, mr koordinatlarını al
                float[] tlArr = obj["tl"].ToObject<float[]>();
                float[] trArr = obj["tr"].ToObject<float[]>();
                float[] mlArr = obj["ml"].ToObject<float[]>();
                float[] mrArr = obj["mr"].ToObject<float[]>();

                // TextBox'ları doldur (x,y)
                int tlX = (int)Math.Round(tlArr[0], MidpointRounding.AwayFromZero);
                int tlY = (int)Math.Round(tlArr[1], MidpointRounding.AwayFromZero);

                int trX = (int)Math.Round(trArr[0], MidpointRounding.AwayFromZero);
                int trY = (int)Math.Round(trArr[1], MidpointRounding.AwayFromZero);

                int mlX = (int)Math.Round(mlArr[0], MidpointRounding.AwayFromZero);
                int mlY = (int)Math.Round(mlArr[1], MidpointRounding.AwayFromZero);

                int mrX = (int)Math.Round(mrArr[0], MidpointRounding.AwayFromZero);
                int mrY = (int)Math.Round(mrArr[1], MidpointRounding.AwayFromZero);

                textBox1.Text = $"({tlX}, {tlY})";
                textBox2.Text = $"({trX}, {trY})";
                textBox3.Text = $"({mlX}, {mlY})";
                textBox4.Text = $"({mrX}, {mrY})";

                // Ekran üzerinde 3 sn kırmızı noktaları göster
                PointF tl = new PointF(tlArr[0], tlArr[1]);
                PointF tr = new PointF(trArr[0], trArr[1]);
                PointF ml = new PointF(mlArr[0], mlArr[1]);
                PointF mr = new PointF(mrArr[0], mrArr[1]);

                //  ShowOverlayPointsFor3Seconds(tl, tr, ml, mr);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Hata: " + ex.Message);
            }



        }
        private async Task StartHalfOverlay(int sliceCount)
        {
            // 3. ve 4. noktalar
            if (!TryParsePoint(textBox3.Text, out Point p3))
            {
                MessageBox.Show("3. nokta hatalı. Ör: (120, 250)");
                return;
            }
            if (!TryParsePoint(textBox4.Text, out Point p4))
            {
                MessageBox.Show("4. nokta hatalı. Ör: (120, 250)");
                return;
            }

            int thickness = 3;
            int seconds = 0;

            // Hangi script?
            //string scriptName = sliceCount == 10
            //    ? "overlay_half10.py"
            //    : "overlay_half6.py";
            string scriptName = "overlay_half6.py";

            string script = Path.Combine(Application.StartupPath, scriptName);
            if (!File.Exists(script))
            {
                MessageBox.Show($"{scriptName} bulunamadı:\n{script}");
                return;
            }

            string args =
                $"-u \"{script}\" " +
                $"{p3.X} {p3.Y} {p4.X} {p4.Y} " +
                $"{thickness} {seconds} --pass";

            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = args,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WorkingDirectory = Path.GetDirectoryName(script),
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            try
            {
                // Önceki overlay kapat
                if (_overlayProc != null)
                {
                    try { if (!_overlayProc.HasExited) _overlayProc.Kill(); } catch { }
                    try { _overlayProc.Dispose(); } catch { }
                    _overlayProc = null;
                }

                _overlayProc = new Process
                {
                    StartInfo = psi,
                    EnableRaisingEvents = true
                };

                _overlayProc.Exited += (s, e) =>
                {
                    try { _overlayProc?.Dispose(); } catch { }
                    _overlayProc = null;
                };

                _overlayProc.Start();
                _overlayProc.BeginOutputReadLine();
                _overlayProc.BeginErrorReadLine();

                await Task.Run(() => _overlayProc.WaitForExit());
            }
            catch (Exception ex)
            {
                MessageBox.Show("Overlay hatası:\n" + ex.Message);
            }
        }

        private async void button_orta_Click(object sender, EventArgs e)
        {
            await StartHalfOverlay(6);
        }

        private async void button3_Click(object sender, EventArgs e)
        {
            await StartHalfOverlay(10);
        }

        private async void button_cizgisiz_Click(object sender, EventArgs e)
        {
            // 4 nokta oku
            var pts = new List<Point>(4);
            for (int i = 0; i < 4; i++)
            {
                if (!TryParsePoint(_boxes[i].Text, out Point p))
                {
                    MessageBox.Show("Köşe " + (i + 1) + " boş/hatalı. Ör: (120, 250)");
                    return;
                }
                pts.Add(p);
            }

            int thickness = 3;
            int seconds = 0; // 0 = sınırsız

            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "overlay_rect.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("overlay_rect.py bulunamadı:\n" + script);
                return;
            }

            // ÖNEMLİ: -u (unbuffered) eklendi; --pass YOK; sadece --silent var.
            string args =
                $"-u \"{script}\" " +    // <— -u
                $"{pts[0].X} {pts[0].Y} " +
                $"{pts[1].X} {pts[1].Y} " +
                $"{pts[2].X} {pts[2].Y} " +
                $"{pts[3].X} {pts[3].Y} " +
                $"{thickness} {seconds} " +
                "--silent";

            var psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = args,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WorkingDirectory = System.IO.Path.GetDirectoryName(script),
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            try
            {
                // Öncekini kapat & temizle
                if (_overlayProc != null)
                {
                    try { if (!_overlayProc.HasExited) _overlayProc.Kill(); } catch { }
                    try { _overlayProc.Dispose(); } catch { }
                    _overlayProc = null;
                }

                // Slotları resetle: kutular boşsa sıralı yazsın
                // true: tüm kutuları temizler; false: var olanları korur (boş buldukça doldurur).
                ResetSlots(clearTexts: false);

                _overlayProc = new Process { StartInfo = psi, EnableRaisingEvents = true };

                _overlayProc.OutputDataReceived += (s2, e2) =>
                {
                    if (!string.IsNullOrWhiteSpace(e2.Data))
                    {
                        FillNextSlotThreadSafe(e2.Data.Trim());
                    }
                };

                _overlayProc.ErrorDataReceived += (s2, e2) =>
                {
                    // İstersen logla:
                    // if (!string.IsNullOrWhiteSpace(e2.Data)) Debug.WriteLine("[PY] " + e2.Data);
                };

                _overlayProc.Exited += (s2, e2) =>
                {
                    try { _overlayProc?.Dispose(); } catch { }
                    _overlayProc = null;
                };



                ResetAllFullFlag();
                _overlayProc.Start();
                _overlayProc.BeginOutputReadLine();
                _overlayProc.BeginErrorReadLine();

                // UI kilitlenmesin
                await Task.Run(() => _overlayProc.WaitForExit());
            }
            catch (Exception ex)
            {
                MessageBox.Show("Çalıştırma hatası:\n" + ex.Message);
            }
        }



    }
}

