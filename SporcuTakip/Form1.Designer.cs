namespace SporcuTakip
{
    partial class Form1
    {
        /// <summary>
        ///Gerekli tasarımcı değişkeni.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///Kullanılan tüm kaynakları temizleyin.
        /// </summary>
        ///<param name="disposing">yönetilen kaynaklar dispose edilmeliyse doğru; aksi halde yanlış.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer üretilen kod

        /// <summary>
        /// Tasarımcı desteği için gerekli metot - bu metodun 
        ///içeriğini kod düzenleyici ile değiştirmeyin.
        /// </summary>
        private void InitializeComponent()
        {
            this.button_performans = new System.Windows.Forms.Button();
            this.button2 = new System.Windows.Forms.Button();
            this.button_veri_girisi = new System.Windows.Forms.Button();
            this.button4 = new System.Windows.Forms.Button();
            this.button_video_analiz = new System.Windows.Forms.Button();
            this.button6 = new System.Windows.Forms.Button();
            this.button7 = new System.Windows.Forms.Button();
            this.button_chatgpt = new System.Windows.Forms.Button();
            this.button_sms = new System.Windows.Forms.Button();
            this.label1 = new System.Windows.Forms.Label();
            this.textBox_log = new System.Windows.Forms.TextBox();
            this.pictureBox1 = new System.Windows.Forms.PictureBox();
            this.button_video_oynat = new System.Windows.Forms.Button();
            this.button_istatistik = new System.Windows.Forms.Button();
            this.button_guncelleme = new System.Windows.Forms.Button();
            this.webView21 = new Microsoft.Web.WebView2.WinForms.WebView2();
            this.button1 = new System.Windows.Forms.Button();
            this.button3 = new System.Windows.Forms.Button();
            this.button5 = new System.Windows.Forms.Button();
            this.button_gps = new System.Windows.Forms.Button();
            this.button_oryantiring = new System.Windows.Forms.Button();
            this.button_utmb = new System.Windows.Forms.Button();
            this.button_kaleci = new System.Windows.Forms.Button();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.webView21)).BeginInit();
            this.SuspendLayout();
            // 
            // button_performans
            // 
            this.button_performans.Location = new System.Drawing.Point(12, 127);
            this.button_performans.Visible = false;
this.button_performans.Name = "button_performans";
            this.button_performans.Size = new System.Drawing.Size(154, 23);
            this.button_performans.TabIndex = 1;
            this.button_performans.Text = "Performans Cihazları";
            this.button_performans.UseVisualStyleBackColor = true;
            this.button_performans.Click += new System.EventHandler(this.button_performans_Click);
            // 
            // button2
            // 
            this.button2.Location = new System.Drawing.Point(12, 384);
            this.button2.Visible = false;
this.button2.Name = "button2";
            this.button2.Size = new System.Drawing.Size(154, 23);
            this.button2.TabIndex = 2;
            this.button2.Text = "Maç Analiz";
            this.button2.UseVisualStyleBackColor = true;
            this.button2.Click += new System.EventHandler(this.button2_Click);
            // 
            // button_veri_girisi
            // 
            this.button_veri_girisi.BackColor = System.Drawing.Color.GreenYellow;
            this.button_veri_girisi.Location = new System.Drawing.Point(12, 135);
            this.button_veri_girisi.Name = "button_veri_girisi";
            this.button_veri_girisi.Size = new System.Drawing.Size(154, 45);
            this.button_veri_girisi.TabIndex = 3;
            this.button_veri_girisi.Text = "Tenis Veri Girişi";
            this.button_veri_girisi.UseVisualStyleBackColor = false;
            this.button_veri_girisi.Click += new System.EventHandler(this.button3_Click);
            // 
            // button4
            // 
            this.button4.Location = new System.Drawing.Point(12, 202);
            this.button4.Visible = false;
this.button4.Name = "button4";
            this.button4.Size = new System.Drawing.Size(154, 23);
            this.button4.TabIndex = 4;
            this.button4.Text = "Sporcu Takip Sistemi";
            this.button4.UseVisualStyleBackColor = true;
            // 
            // button_video_analiz
            // 
            this.button_video_analiz.Location = new System.Drawing.Point(12, 271);
            this.button_video_analiz.Visible = false;
this.button_video_analiz.Name = "button_video_analiz";
            this.button_video_analiz.Size = new System.Drawing.Size(154, 23);
            this.button_video_analiz.TabIndex = 5;
            this.button_video_analiz.Text = "Video Analiz";
            this.button_video_analiz.UseVisualStyleBackColor = true;
            this.button_video_analiz.Click += new System.EventHandler(this.button_video_analiz_Click);
            // 
            // button6
            // 
            this.button6.Location = new System.Drawing.Point(12, 165);
            this.button6.Visible = false;
this.button6.Name = "button6";
            this.button6.Size = new System.Drawing.Size(154, 23);
            this.button6.TabIndex = 6;
            this.button6.Text = "Randevu Sistemi Modülü";
            this.button6.UseVisualStyleBackColor = true;
            this.button6.Click += new System.EventHandler(this.button6_Click);
            // 
            // button7
            // 
            this.button7.Location = new System.Drawing.Point(12, 300);
            this.button7.Visible = false;
this.button7.Name = "button7";
            this.button7.Size = new System.Drawing.Size(154, 23);
            this.button7.TabIndex = 7;
            this.button7.Text = "Drill Çizme";
            this.button7.UseVisualStyleBackColor = true;
            this.button7.Click += new System.EventHandler(this.button_drill_Click);
            // 
            // button_chatgpt
            // 
            this.button_chatgpt.Enabled = false;
            this.button_chatgpt.Location = new System.Drawing.Point(12, 242);
            this.button_chatgpt.Visible = false;
this.button_chatgpt.Name = "button_chatgpt";
            this.button_chatgpt.Size = new System.Drawing.Size(154, 23);
            this.button_chatgpt.TabIndex = 8;
            this.button_chatgpt.Text = "Yapay Zeka Botu";
            this.button_chatgpt.UseVisualStyleBackColor = true;
            this.button_chatgpt.Click += new System.EventHandler(this.button_chatgpt_Click);
            // 
            // button_sms
            // 
            this.button_sms.Location = new System.Drawing.Point(12, 338);
            this.button_sms.Visible = false;
this.button_sms.Name = "button_sms";
            this.button_sms.Size = new System.Drawing.Size(154, 23);
            this.button_sms.TabIndex = 9;
            this.button_sms.Text = "SMS Modülü";
            this.button_sms.UseVisualStyleBackColor = true;
            this.button_sms.Click += new System.EventHandler(this.button_sms_Click);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(162)));
            this.label1.Location = new System.Drawing.Point(12, 255);
            this.label1.MaximumSize = new System.Drawing.Size(160, 0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(136, 64);
            this.label1.TabIndex = 10;
            this.label1.Text = "İletişim : Spor Yazılımları Ltd. Ş.\r\nSöğütlü Akçaabat-Trabzon\r\n";
            this.label1.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // textBox_log
            // 
            this.textBox_log.Location = new System.Drawing.Point(162, 23);
            this.textBox_log.Multiline = true;
            this.textBox_log.Name = "textBox_log";
            this.textBox_log.Size = new System.Drawing.Size(127, 10);
            this.textBox_log.TabIndex = 11;
            this.textBox_log.Visible = false;
            // 
            // pictureBox1
            // 
            this.pictureBox1.BackColor = System.Drawing.Color.Transparent;
            this.pictureBox1.Image = global::SporcuTakip.Properties.Resources._8347A1FB6B6E98BCF1810516920C4780;
            this.pictureBox1.Location = new System.Drawing.Point(33, 12);
            this.pictureBox1.Name = "pictureBox1";
            this.pictureBox1.Size = new System.Drawing.Size(103, 104);
            this.pictureBox1.SizeMode = System.Windows.Forms.PictureBoxSizeMode.StretchImage;
            this.pictureBox1.TabIndex = 0;
            this.pictureBox1.TabStop = false;
            // 
            // button_video_oynat
            // 
            this.button_video_oynat.BackColor = System.Drawing.Color.GreenYellow;
            this.button_video_oynat.Location = new System.Drawing.Point(12, 190);
            this.button_video_oynat.Name = "button_video_oynat";
            this.button_video_oynat.Size = new System.Drawing.Size(154, 45);
            this.button_video_oynat.TabIndex = 12;
            this.button_video_oynat.Text = "Tenis Analiz";
            this.button_video_oynat.UseVisualStyleBackColor = false;
            this.button_video_oynat.Click += new System.EventHandler(this.button_video_oynat_Click);
            // 
            // button_istatistik
            // 
            this.button_istatistik.Location = new System.Drawing.Point(12, 454);
            this.button_istatistik.Visible = false;
this.button_istatistik.Name = "button_istatistik";
            this.button_istatistik.Size = new System.Drawing.Size(154, 23);
            this.button_istatistik.TabIndex = 13;
            this.button_istatistik.Text = "İstatistik Modülü";
            this.button_istatistik.UseVisualStyleBackColor = true;
            this.button_istatistik.Click += new System.EventHandler(this.button_istatistik_Click);
            // 
            // button_guncelleme
            // 
            this.button_guncelleme.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button_guncelleme.BackColor = System.Drawing.Color.Turquoise;
            this.button_guncelleme.Location = new System.Drawing.Point(601, 23);
            this.button_guncelleme.Visible = false;
this.button_guncelleme.Name = "button_guncelleme";
            this.button_guncelleme.Size = new System.Drawing.Size(154, 23);
            this.button_guncelleme.TabIndex = 15;
            this.button_guncelleme.Text = "Güncellemeleri Al";
            this.button_guncelleme.UseVisualStyleBackColor = false;
            // 
            // webView21
            // 
            this.webView21.AllowExternalDrop = true;
            this.webView21.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.webView21.CreationProperties = null;
            this.webView21.DefaultBackgroundColor = System.Drawing.Color.White;
            this.webView21.Location = new System.Drawing.Point(186, 52);
            this.webView21.Name = "webView21";
            this.webView21.Size = new System.Drawing.Size(689, 654);
            this.webView21.TabIndex = 16;
            this.webView21.ZoomFactor = 1D;
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(12, 536);
            this.button1.Visible = false;
this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(154, 23);
            this.button1.TabIndex = 17;
            this.button1.Text = "Termal Kamera Modülü";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Click += new System.EventHandler(this.button1_Click);
            // 
            // button3
            // 
            this.button3.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button3.BackColor = System.Drawing.Color.Turquoise;
            this.button3.Location = new System.Drawing.Point(761, 23);
            this.button3.Visible = false;
this.button3.Name = "button3";
            this.button3.Size = new System.Drawing.Size(114, 23);
            this.button3.TabIndex = 18;
            this.button3.Text = "Bağışta Bulun";
            this.button3.UseVisualStyleBackColor = false;
            // 
            // button5
            // 
            this.button5.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button5.BackColor = System.Drawing.Color.Turquoise;
            this.button5.Location = new System.Drawing.Point(441, 23);
            this.button5.Visible = false;
this.button5.Name = "button5";
            this.button5.Size = new System.Drawing.Size(154, 23);
            this.button5.TabIndex = 19;
            this.button5.Text = "Yazılım-Donanım Talep Et";
            this.button5.UseVisualStyleBackColor = false;
            // 
            // button_gps
            // 
            this.button_gps.Location = new System.Drawing.Point(12, 493);
            this.button_gps.Visible = false;
this.button_gps.Name = "button_gps";
            this.button_gps.Size = new System.Drawing.Size(154, 23);
            this.button_gps.TabIndex = 20;
            this.button_gps.Text = "GPS Modülü";
            this.button_gps.UseVisualStyleBackColor = true;
            this.button_gps.Click += new System.EventHandler(this.button_gps_Click);
            // 
            // button_oryantiring
            // 
            this.button_oryantiring.Location = new System.Drawing.Point(12, 600);
            this.button_oryantiring.Visible = false;
this.button_oryantiring.Name = "button_oryantiring";
            this.button_oryantiring.Size = new System.Drawing.Size(154, 23);
            this.button_oryantiring.TabIndex = 22;
            this.button_oryantiring.Text = "Oryantiring Modülü";
            this.button_oryantiring.UseVisualStyleBackColor = true;
            this.button_oryantiring.Click += new System.EventHandler(this.button_oryantiring_Click);
            // 
            // button_utmb
            // 
            this.button_utmb.Location = new System.Drawing.Point(12, 639);
            this.button_utmb.Visible = false;
this.button_utmb.Name = "button_utmb";
            this.button_utmb.Size = new System.Drawing.Size(154, 23);
            this.button_utmb.TabIndex = 21;
            this.button_utmb.Text = "UTMB Modülü";
            this.button_utmb.UseVisualStyleBackColor = true;
            this.button_utmb.Click += new System.EventHandler(this.button_utmb_Click);
            // 
            // button_kaleci
            // 
            this.button_kaleci.BackColor = System.Drawing.Color.GreenYellow;
            this.button_kaleci.Location = new System.Drawing.Point(12, 571);
            this.button_kaleci.Visible = false;
this.button_kaleci.Name = "button_kaleci";
            this.button_kaleci.Size = new System.Drawing.Size(154, 23);
            this.button_kaleci.TabIndex = 23;
            this.button_kaleci.Text = "Kaleci Analizi";
            this.button_kaleci.UseVisualStyleBackColor = false;
            this.button_kaleci.Click += new System.EventHandler(this.button_kaleci_Click);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(914, 825);
            this.Controls.Add(this.button_kaleci);
            this.Controls.Add(this.button_oryantiring);
            this.Controls.Add(this.button_utmb);
            this.Controls.Add(this.button_gps);
            this.Controls.Add(this.button5);
            this.Controls.Add(this.button3);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.webView21);
            this.Controls.Add(this.button_guncelleme);
            this.Controls.Add(this.button_istatistik);
            this.Controls.Add(this.button_video_oynat);
            this.Controls.Add(this.textBox_log);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.button_sms);
            this.Controls.Add(this.button_chatgpt);
            this.Controls.Add(this.button7);
            this.Controls.Add(this.button6);
            this.Controls.Add(this.button_video_analiz);
            this.Controls.Add(this.button4);
            this.Controls.Add(this.button_veri_girisi);
            this.Controls.Add(this.button2);
            this.Controls.Add(this.button_performans);
            this.Controls.Add(this.pictureBox1);
            this.Name = "Form1";
            this.Text = "Tenis Veri Toplama ve Analiz Sistemi";
            this.Load += new System.EventHandler(this.Form1_Load);
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.webView21)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.PictureBox pictureBox1;
        private System.Windows.Forms.Button button_performans;
        private System.Windows.Forms.Button button2;
        private System.Windows.Forms.Button button_veri_girisi;
        private System.Windows.Forms.Button button4;
        private System.Windows.Forms.Button button_video_analiz;
        private System.Windows.Forms.Button button6;
        private System.Windows.Forms.Button button7;
        private System.Windows.Forms.Button button_chatgpt;
        private System.Windows.Forms.Button button_sms;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.TextBox textBox_log;
        private System.Windows.Forms.Button button_video_oynat;
        private System.Windows.Forms.Button button_istatistik;
        private System.Windows.Forms.Button button_guncelleme;
        private Microsoft.Web.WebView2.WinForms.WebView2 webView21;
        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.Button button3;
        private System.Windows.Forms.Button button5;
        private System.Windows.Forms.Button button_gps;
        private System.Windows.Forms.Button button_oryantiring;
        private System.Windows.Forms.Button button_utmb;
        private System.Windows.Forms.Button button_kaleci;
    }
}

