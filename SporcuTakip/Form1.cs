using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using Microsoft.Web.WebView2.WinForms;
using Microsoft.Web.WebView2.Core;
using Tulpep.NotificationWindow;
using System.Diagnostics;

namespace SporcuTakip
{
    public partial class Form1 : Form
    {
       
        public Form1()
        {
            InitializeComponent();
        }

        private void DikeyEsitHizala(params Button[] buttons)
        {
            if (buttons == null || buttons.Length < 2)
                return;

            int firstY = buttons[0].Location.Y;
            int lastY = buttons[buttons.Length - 1].Location.Y;
            int totalSpace = lastY - firstY;
            int gap = totalSpace / (buttons.Length - 1);

            for (int i = 0; i < buttons.Length; i++)
            {
                var loc = buttons[i].Location;
                buttons[i].Location = new Point(loc.X, firstY + (gap * i));
            }
        }

        private void WebMessageReceived(object sender, CoreWebView2WebMessageReceivedEventArgs e)
        {
            string mesaj = e.TryGetWebMessageAsString();
            if (mesaj == "bildirim")
            {
                ShowNotification("Web", "Web sayfasından bildirim geldi", Color.MediumSeaGreen);
            }
            if (mesaj == "bildirim2")
            {
                ShowNotification("Web2", "Web sayfasından bildirim2 geldi", Color.MediumSeaGreen);
            }
        }

        private void ShowNotification(string baslik, string mesaj, Color renk)
        {
            PopupNotifier popup = new PopupNotifier
            {
                TitleText = baslik,
                ContentText = mesaj,
                BodyColor = renk,
                TitleColor = Color.White,
                ContentColor = Color.White,
                TitleFont = new Font("Segoe UI", 14, FontStyle.Bold),
                ContentFont = new Font("Segoe UI", 11)
            };
            popup.Popup();
        }

        private void webView2_Click(object sender, EventArgs e)
        {

        }

        private void button_sms_Click(object sender, EventArgs e)
        {
            Form_sms smsFormu = new Form_sms();
            smsFormu.Show();
        }

        private void button_chatgpt_Click(object sender, EventArgs e)
        {
            MessageBox.Show("Yapay zeka modülü güvenlik nedeniyle devre dışı bırakılmıştır.", "Bilgi");
        }

        private void button_video_analiz_Click(object sender, EventArgs e)
        {
            Form_kinematik kinematik = new Form_kinematik();
            kinematik.Show();
        }

        private void textBox_log_TextChanged(object sender, EventArgs e)
        {

        }

        public void AppendLog(string text)
        {
            if (textBox_log.InvokeRequired)
            {
                textBox_log.Invoke(new Action<string>(AppendLog), text);
            }
            else
            {
                textBox_log.AppendText(text + Environment.NewLine);
            }
        }

        private void button_video_oynat_Click(object sender, EventArgs e)
        {
            Form_video_oynat videoformu = new Form_video_oynat();
            videoformu.Show();
        }

        private void button3_Click(object sender, EventArgs e)
        {
            Form_veri_girisi veri_girisi = new Form_veri_girisi();
            veri_girisi.Show();
        }

        private void button_performans_Click(object sender, EventArgs e)
        {
           Form_performans veri_performans = new Form_performans();
            veri_performans.Show();
        }

        private const string HomeUrl = "https://performansmerkezi.trabzon.edu.tr";
        private async void Form1_Load(object sender, EventArgs e)
        {
            // Tenis butonlarının düzenli ve sabit kalması için DikeyEsitHizala çağrısı kaldırıldı

            try
            {
                await webView21.EnsureCoreWebView2Async();

                // target="_blank" linkleri aynı sekmede aç
                webView21.CoreWebView2.NewWindowRequested += (s, ev) =>
                {
                    ev.Handled = true;
                    webView21.CoreWebView2.Navigate(ev.Uri);
                };

                // Siteye git
                webView21.CoreWebView2.Navigate(HomeUrl);
            }
            catch (WebView2RuntimeNotFoundException)
            {
                MessageBox.Show("Microsoft Edge WebView2 Runtime yüklü değil. Lütfen kurup tekrar deneyin.",
                    "WebView2 Runtime Eksik", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            catch (Exception ex)
            {
                MessageBox.Show("WebView2 başlatılırken hata: " + ex.Message);
            }
        }


        private void button_drill_Click(object sender, EventArgs e)
        {
            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "soccer_diagrammer4.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("soccer_diagrammer4.py bulunamadı:\n" + script);
                return;
            }

            var psi = new ProcessStartInfo()
            {
                FileName = pythonExe,
                Arguments = $"\"{script}\"",
                UseShellExecute = true,
            };

            Process.Start(psi);
        }

        private void button_gps_Click(object sender, EventArgs e)
        {
            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "soccer_pitch_anim.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("soccer_diagrammer4.py bulunamadı:\n" + script);
                return;
            }

            var psi = new ProcessStartInfo()
            {
                FileName = pythonExe,
                Arguments = $"\"{script}\"",
                UseShellExecute = true,
            };

            Process.Start(psi);
        }

        private void button_istatistik_Click(object sender, EventArgs e)
        {
            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "MiniSPSS.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("soccer_diagrammer4.py bulunamadı:\n" + script);
                return;
            }

            var psi = new ProcessStartInfo()
            {
                FileName = pythonExe,
                Arguments = $"\"{script}\"",
                UseShellExecute = true,
            };

            Process.Start(psi);
        }

        private void button_utmb_Click(object sender, EventArgs e)
        {

            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "utmb4.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("utmb.py bulunamadı:\n" + script);
                return;
            }

            var psi = new ProcessStartInfo()
            {
                FileName = pythonExe,
                Arguments = $"\"{script}\"",
                UseShellExecute = true,
            };

            Process.Start(psi);
        }

        private void button_oryantiring_Click(object sender, EventArgs e)
        {

            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "oryantiring10.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("oryantiring10.py bulunamadı:\n" + script);
                return;
            }

            var psi = new ProcessStartInfo()
            {
                FileName = pythonExe,
                Arguments = $"\"{script}\"",
                UseShellExecute = true,
            };

            Process.Start(psi);
        }

        private void button_kaleci_Click(object sender, EventArgs e)
        {
            Form_kaleci videoformu_kaleci = new Form_kaleci();
            videoformu_kaleci.Show();
        }



private void button6_Click(object sender, EventArgs e)
    {
        Process.Start(new ProcessStartInfo
        {
            FileName = "https://randevu.trabzon.edu.tr",
            UseShellExecute = true
        });
    }

        private void button1_Click(object sender, EventArgs e)
        {
            string pythonExe = "python";
            string script = System.IO.Path.Combine(Application.StartupPath, "termal_gui.py");
            if (!System.IO.File.Exists(script))
            {
                MessageBox.Show("soccer_diagrammer4.py bulunamadı:\n" + script);
                return;
            }

            var psi = new ProcessStartInfo()
            {
                FileName = pythonExe,
                Arguments = $"\"{script}\"",
                UseShellExecute = true,
            };

            Process.Start(psi);
        }

        private void button2_Click(object sender, EventArgs e)
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "https://sporozelyetenek.trabzon.edu.tr",
                UseShellExecute = true
            });
        }
    }
}
