using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace SporcuTakip
{
    public partial class Form_kinematik : Form
    {
        private Process _proc;
        private string _stopFlagPath;
        private Timer _previewTimer;
        private string _previewPath;

        public Form_kinematik()
        {
            InitializeComponent();
            WireEvents();

            // varsayılanlar
            txtPythonPath.Text = GuessPython();
            txtDbPath.Text = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "angles.db");
            txtOutputPath.Text = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "processed.mp4");

            // başlangıçta kamera seçili ise
            ToggleSourceInputs(this, EventArgs.Empty);
        }

        private void WireEvents()
        {
            btnBrowsePython.Click += (s, e) => BrowseExe(txtPythonPath, "Python|python.exe");
            btnBrowseDb.Click += (s, e) => BrowseFile(txtDbPath, "SQLite DB|*.db|Tümü|*.*");
            btnBrowseOutput.Click += (s, e) => BrowseSave(txtOutputPath, "MP4 Video|*.mp4|Tümü|*.*");

            btnBrowseMedia.Click += (s, e) =>
            {
                if (rbVideo.Checked) BrowseFile(txtMediaPath, "Video|*.mp4;*.avi;*.mov;*.mkv|Tümü|*.*");
                else if (rbImage.Checked) BrowseFile(txtMediaPath, "Görüntü|*.jpg;*.jpeg;*.png;*.bmp|Tümü|*.*");
            };

            rbCamera.CheckedChanged += ToggleSourceInputs;
            rbVideo.CheckedChanged += ToggleSourceInputs;
            rbImage.CheckedChanged += ToggleSourceInputs;

            btnStart.Click += (s, e) => StartPython();
            btnStop.Click += (s, e) => StopPython();
            this.FormClosing += (s, e) => StopPython();

            chkShow.CheckedChanged += (s, e) => ApplyPreviewLayout(chkShow.Checked);
        }

        private void ToggleSourceInputs(object sender, EventArgs e)
        {
            bool cam = rbCamera.Checked;
            numCameraIndex.Enabled = cam;
            txtMediaPath.Enabled = btnBrowseMedia.Enabled = !cam;
        }

        private string GuessPython()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string venv1 = Path.Combine(baseDir, "venv", "Scripts", "python.exe");
            string venv2 = Path.Combine(baseDir, "venv2", "Scripts", "python.exe");
            if (File.Exists(venv2)) return venv2;
            if (File.Exists(venv1)) return venv1;
            return "python";
        }

        private void BrowseExe(TextBox target, string filter)
        {
            using (var d = new OpenFileDialog()) { d.Filter = filter; d.CheckFileExists = true; if (d.ShowDialog() == DialogResult.OK) target.Text = d.FileName; }
        }
        private void BrowseFile(TextBox target, string filter)
        {
            using (var d = new OpenFileDialog()) { d.Filter = filter; d.CheckFileExists = true; if (d.ShowDialog() == DialogResult.OK) target.Text = d.FileName; }
        }
        private void BrowseSave(TextBox target, string filter)
        {
            using (var d = new SaveFileDialog()) { d.Filter = filter; d.OverwritePrompt = false; if (d.ShowDialog() == DialogResult.OK) target.Text = d.FileName; }
        }

        private void SetBusy(bool busy, string status = null)
        {
            if (this.InvokeRequired)
            {
                this.BeginInvoke(new Action(() => SetBusy(busy, status)));
                return;
            }
            btnStart.Enabled = !busy;
            btnStop.Enabled = busy;
            progress.MarqueeAnimationSpeed = busy ? 50 : 0;
            lblStatus.Text = status ?? (busy ? "Çalışıyor..." : "Hazır");
        }


        private void AppendLog(string s)
        {
            if (string.IsNullOrEmpty(s)) return;
            if (txtLog.InvokeRequired) { txtLog.BeginInvoke(new Action(() => AppendLog(s))); return; }
            txtLog.AppendText(s + Environment.NewLine);
            txtLog.ScrollToCaret();
        }

        // -------- Preview alanını aç/kapat ve responsive kolon genişlikleri ----------
        private void ApplyPreviewLayout(bool show)
        {
            // göster seçiliyse log: %40, preview: %60; değilse log %100, preview %0
            if (layoutRoot.InvokeRequired) { layoutRoot.BeginInvoke(new Action(() => ApplyPreviewLayout(show))); return; }

            if (show)
            {
                layoutRoot.ColumnStyles[0].Width = 40f;
                layoutRoot.ColumnStyles[1].Width = 60f;
                //picPreview.Visible = true;
                //picPreview.BackColor = Color.Black;
                StartPreviewTimer();
            }
            else
            {
                StopPreviewTimer();
              //  picPreview.Visible = false;
                //layoutRoot.ColumnStyles[0].Width = 100f;
                //layoutRoot.ColumnStyles[1].Width = 0f;  // siyah ekran yok; kolon tamamen kapanır
            }
            layoutRoot.PerformLayout();
        }

        private void StartPreviewTimer()
        {
            if (_previewTimer == null)
            {
                _previewTimer = new Timer();
                _previewTimer.Interval = 100; // ~10 fps önizleme
                _previewTimer.Tick += (s, e) =>
                {
                    try
                    {
                        if (!string.IsNullOrEmpty(_previewPath) && File.Exists(_previewPath))
                        {
                            using (var fs = new FileStream(_previewPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                            using (var ms = new MemoryStream())
                            {
                                fs.CopyTo(ms);
                                using (var bmp = new Bitmap(ms))
                                {
                                    var old = picPreview.Image;
                                    picPreview.Image = (Image)bmp.Clone();
                                    if (old != null) old.Dispose();
                                }
                            }
                        }
                    }
                    catch { /* eşzamanlı yazım olabilir */ }
                };
            }
            _previewTimer.Start();
        }

        private void StopPreviewTimer()
        {
            if (_previewTimer != null) _previewTimer.Stop();
            if (picPreview.Image != null) { picPreview.Image.Dispose(); picPreview.Image = null; }
        }

        // -------- Python args ----------
        private string BuildArgs()
        {
            string scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "diz_acisi2.py");
            var sb = new StringBuilder("\"" + scriptPath + "\"");

            if (rbCamera.Checked) sb.Append(" --source " + numCameraIndex.Value);
            else sb.Append(" --source \"" + txtMediaPath.Text + "\"");

            sb.Append(" --db \"" + txtDbPath.Text + "\"");
            sb.Append(" --fps " + numFps.Value);
            sb.Append(chkShow.Checked ? " --show" : " --noshow");
            if (chkSave.Checked)
            {
                sb.Append(" --save");
                sb.Append(" --out \"" + txtOutputPath.Text + "\"");
            }

            // geçici yollar
            _stopFlagPath = Path.Combine(Path.GetTempPath(), "kinematic_stop_" + Guid.NewGuid().ToString("N") + ".flag");
            _previewPath = Path.Combine(Path.GetTempPath(), "kinematic_preview_" + Guid.NewGuid().ToString("N") + ".jpg");
            sb.Append(" --stopfile \"" + _stopFlagPath + "\"");
            if (chkShow.Checked) sb.Append(" --preview \"" + _previewPath + "\"");

            return sb.ToString();
        }

        // -------- Start / Stop ----------
        private void StartPython()
        {
            try
            {
                if (_proc != null && !_proc.HasExited) { MessageBox.Show("Zaten çalışıyor."); return; }

                string pythonExe = txtPythonPath.Text.Trim();
                if (string.IsNullOrWhiteSpace(pythonExe)) { MessageBox.Show("Python yolu boş."); return; }
                if (!File.Exists(pythonExe) && pythonExe != "python") { MessageBox.Show("Python bulunamadı."); return; }
                if (!rbCamera.Checked && string.IsNullOrWhiteSpace(txtMediaPath.Text)) { MessageBox.Show("Video/fotoğraf yolu seçin veya Kamera’yı seçin."); return; }

                // önizleme düzeni
                ApplyPreviewLayout(chkShow.Checked);

                var psi = new ProcessStartInfo();
                psi.FileName = pythonExe;
                psi.Arguments = BuildArgs();
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;
                psi.CreateNoWindow = true;
                psi.WorkingDirectory = AppDomain.CurrentDomain.BaseDirectory;

                _proc = new Process();
                _proc.SynchronizingObject = this;

                _proc.StartInfo = psi;
                _proc.EnableRaisingEvents = true;
                _proc.OutputDataReceived += (s, e) => { if (!string.IsNullOrEmpty(e.Data)) AppendLog(e.Data); };
                _proc.ErrorDataReceived += (s, e) => { if (!string.IsNullOrEmpty(e.Data)) AppendLog("[ERR] " + e.Data); };
                _proc.Exited += (s, e) =>
                {
                    AppendLog("[i] Python bitti. ExitCode=" + _proc.ExitCode);
                    StopPreviewTimer();
                    SetBusy(false, "Tamamlandı");
                    // kolonları eski haline al
                    ApplyPreviewLayout(false);
                };

                txtLog.Clear();
                SetBusy(true, "Çalışıyor...");
                AppendLog("[i] Komut: " + psi.FileName + " " + psi.Arguments);

                _proc.Start();
                _proc.BeginOutputReadLine();
                _proc.BeginErrorReadLine();
            }
            catch (Exception ex)
            {
                SetBusy(false, "Hata");
                MessageBox.Show("Başlatılamadı: " + ex.Message);
            }
        }

        private void StopPython()
        {
            try
            {
                // nazik durdurma için stop flag
                if (!string.IsNullOrEmpty(_stopFlagPath))
                {
                    try { File.WriteAllText(_stopFlagPath, "stop"); } catch { }
                }

                // önizleme timer'ı dursun
                StopPreviewTimer();

                if (_proc != null && !_proc.HasExited)
                {
                    // 5 sn bekle (writer.release ve db.close için zaman)
                    if (!_proc.WaitForExit(5000))
                    {
                        _proc.Kill();
                        _proc.WaitForExit();
                    }
                    _proc.Dispose();
                    AppendLog("[i] Süreç sonlandırıldı.");
                }
            }
            catch { }
            finally
            {
                _proc = null;
                SetBusy(false, "Durduruldu");

                // preview kolonunu kapat
                ApplyPreviewLayout(false);

                // tmp dosyaları temizle
                try { if (!string.IsNullOrEmpty(_stopFlagPath) && File.Exists(_stopFlagPath)) File.Delete(_stopFlagPath); } catch { }
                try { if (!string.IsNullOrEmpty(_previewPath) && File.Exists(_previewPath)) File.Delete(_previewPath); } catch { }
            }
        }
    }
}
