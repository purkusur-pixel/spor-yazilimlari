using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace SporcuTakip
{
    public partial class Form_video_analiz : Form
    {
        public Form_video_analiz()
        {
            InitializeComponent();
        }

        private void Form_video_analiz_Load(object sender, EventArgs e)
        {
            //// yuz.py dosyasının yolunu belirt
            //string scriptPath = Path.Combine(Application.StartupPath, "yuz.py");

            //// Python process'i başlat
            //ProcessStartInfo psi = new ProcessStartInfo();
            //psi.FileName = "python"; // ya da python3
            //psi.Arguments = $"\"{scriptPath}\"";
            //psi.UseShellExecute = false;
            //psi.CreateNoWindow = false;

            //try
            //{
            //    Process.Start(psi);
            //}
            //catch (Exception ex)
            //{
            //    MessageBox.Show("Hata: " + ex.Message);
            //}
        }
    }
}
