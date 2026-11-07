using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Windows.Forms;

namespace SporcuTakip
{
    public partial class Form_sms : Form
    {
        private WebView2 webView;

        public Form_sms()
        {
            InitializeComponent();
        }

        private async void Form_sms_Load(object sender, EventArgs e)
        {
            webView = new WebView2();
            webView.Dock = DockStyle.Fill;
            this.Controls.Add(webView);

            await webView.EnsureCoreWebView2Async();
            webView.CoreWebView2.WebMessageReceived += WebMessageReceived;

            string htmlPath = Path.Combine(Application.StartupPath, "sms.html");
            webView.Source = new Uri(htmlPath);
        }

        private void WebMessageReceived(object sender, CoreWebView2WebMessageReceivedEventArgs e)
        {
            string json = e.TryGetWebMessageAsString();
            var smsData = JsonSerializer.Deserialize<SmsPayload>(json);

            // Test amaçlı:
            MessageBox.Show($"Başlık: {smsData.Title}\nMesaj: {smsData.Message}\nKişi Sayısı: {smsData.Recipients.Count}");
        }

        public class SmsPayload
        {
            public string Title { get; set; }
            public string Message { get; set; }
            public List<Dictionary<string, string>> Recipients { get; set; }
        }
    }
}
