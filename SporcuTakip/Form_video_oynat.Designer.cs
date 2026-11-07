namespace SporcuTakip
{
    partial class Form_video_oynat
    {
        private System.ComponentModel.IContainer components = null;
       
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null)) components.Dispose();
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            this.webView21 = new Microsoft.Web.WebView2.WinForms.WebView2();
            this.button_dosyaAc = new System.Windows.Forms.Button();
            this.label_ekran_suresi = new System.Windows.Forms.Label();
            this.labelFrameSayaci = new System.Windows.Forms.Label();
            this.textBox_frame_bas = new System.Windows.Forms.TextBox();
            this.textBox_frame_bit = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.label5 = new System.Windows.Forms.Label();
            this.textBox_dustugu_bolge = new System.Windows.Forms.TextBox();
            this.textBox_vurulan_bolge = new System.Windows.Forms.TextBox();
            this.label6 = new System.Windows.Forms.Label();
            this.label7 = new System.Windows.Forms.Label();
            this.textBox_nereden_geldi = new System.Windows.Forms.TextBox();
            this.textBox_bulusulan_bolge = new System.Windows.Forms.TextBox();
            this.button_frame_al = new System.Windows.Forms.Button();
            this.button_kaydet = new System.Windows.Forms.Button();
            this.checkBox_atis_basarili_mi = new System.Windows.Forms.CheckBox();
            this.label8 = new System.Windows.Forms.Label();
            this.label9 = new System.Windows.Forms.Label();
            this.comboBox_kisi1 = new System.Windows.Forms.ComboBox();
            this.comboBox_kisi2 = new System.Windows.Forms.ComboBox();
            this.comboBox_spin = new System.Windows.Forms.ComboBox();
            this.comboBox_vurus = new System.Windows.Forms.ComboBox();
            this.label10 = new System.Windows.Forms.Label();
            this.label11 = new System.Windows.Forms.Label();
            this.button_kisi_degistir = new System.Windows.Forms.Button();
            this.textBox1 = new System.Windows.Forms.TextBox();
            this.textBox2 = new System.Windows.Forms.TextBox();
            this.textBox3 = new System.Windows.Forms.TextBox();
            this.textBox4 = new System.Windows.Forms.TextBox();
            this.button2 = new System.Windows.Forms.Button();
            this.button_cizgili = new System.Windows.Forms.Button();
            this.button4 = new System.Windows.Forms.Button();
            this.label1 = new System.Windows.Forms.Label();
            this.label12 = new System.Windows.Forms.Label();
            this.label13 = new System.Windows.Forms.Label();
            this.label14 = new System.Windows.Forms.Label();
            this.button1 = new System.Windows.Forms.Button();
            this.button5 = new System.Windows.Forms.Button();
            this.button_cizgisiz = new System.Windows.Forms.Button();
            this.radioButton1 = new System.Windows.Forms.RadioButton();
            this.radioButton2 = new System.Windows.Forms.RadioButton();
            this.radioButton3 = new System.Windows.Forms.RadioButton();
            this.radioButton4 = new System.Windows.Forms.RadioButton();
            this.radioButton5 = new System.Windows.Forms.RadioButton();
            this.radioButton6 = new System.Windows.Forms.RadioButton();
            this.label15 = new System.Windows.Forms.Label();
            this.label16 = new System.Windows.Forms.Label();
            this.label_video_adi = new System.Windows.Forms.Label();
            this.label_kalinan_zaman = new System.Windows.Forms.Label();
            this.button_otomatik = new System.Windows.Forms.Button();
            ((System.ComponentModel.ISupportInitialize)(this.webView21)).BeginInit();
            this.SuspendLayout();
            // 
            // webView21
            // 
            this.webView21.AllowExternalDrop = true;
            this.webView21.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.webView21.CreationProperties = null;
            this.webView21.DefaultBackgroundColor = System.Drawing.Color.White;
            this.webView21.Location = new System.Drawing.Point(12, 20);
            this.webView21.Name = "webView21";
            this.webView21.Size = new System.Drawing.Size(1084, 660);
            this.webView21.TabIndex = 6;
            this.webView21.ZoomFactor = 1D;
            // 
            // button_dosyaAc
            // 
            this.button_dosyaAc.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button_dosyaAc.Location = new System.Drawing.Point(1108, 23);
            this.button_dosyaAc.Name = "button_dosyaAc";
            this.button_dosyaAc.Size = new System.Drawing.Size(210, 30);
            this.button_dosyaAc.TabIndex = 2;
            this.button_dosyaAc.Text = "Video Yükle";
            this.button_dosyaAc.UseVisualStyleBackColor = true;
            this.button_dosyaAc.Click += new System.EventHandler(this.button_dosyaAc_Click);
            // 
            // label_ekran_suresi
            // 
            this.label_ekran_suresi.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label_ekran_suresi.AutoSize = true;
            this.label_ekran_suresi.Location = new System.Drawing.Point(108, 660);
            this.label_ekran_suresi.Name = "label_ekran_suresi";
            this.label_ekran_suresi.Size = new System.Drawing.Size(35, 13);
            this.label_ekran_suresi.TabIndex = 7;
            this.label_ekran_suresi.Text = "label1";
            this.label_ekran_suresi.Visible = false;
            // 
            // labelFrameSayaci
            // 
            this.labelFrameSayaci.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.labelFrameSayaci.Location = new System.Drawing.Point(108, 631);
            this.labelFrameSayaci.Name = "labelFrameSayaci";
            this.labelFrameSayaci.Size = new System.Drawing.Size(35, 13);
            this.labelFrameSayaci.TabIndex = 8;
            this.labelFrameSayaci.Text = "label1";
            this.labelFrameSayaci.Visible = false;
            // 
            // textBox_frame_bas
            // 
            this.textBox_frame_bas.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.textBox_frame_bas.Location = new System.Drawing.Point(114, 708);
            this.textBox_frame_bas.Name = "textBox_frame_bas";
            this.textBox_frame_bas.Size = new System.Drawing.Size(100, 20);
            this.textBox_frame_bas.TabIndex = 10;
            // 
            // textBox_frame_bit
            // 
            this.textBox_frame_bit.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.textBox_frame_bit.Location = new System.Drawing.Point(114, 734);
            this.textBox_frame_bit.Name = "textBox_frame_bit";
            this.textBox_frame_bit.Size = new System.Drawing.Size(100, 20);
            this.textBox_frame_bit.TabIndex = 11;
            // 
            // label2
            // 
            this.label2.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(27, 714);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(85, 13);
            this.label2.TabIndex = 12;
            this.label2.Text = "Frame Başlangıç";
            // 
            // label3
            // 
            this.label3.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(27, 740);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(58, 13);
            this.label3.TabIndex = 13;
            this.label3.Text = "Frame Bitiş";
            // 
            // label4
            // 
            this.label4.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(365, 739);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(108, 13);
            this.label4.TabIndex = 17;
            this.label4.Text = "Topun düştüğü bölge";
            // 
            // label5
            // 
            this.label5.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(365, 713);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(117, 13);
            this.label5.TabIndex = 16;
            this.label5.Text = "Topun vurulduğu bölge";
            // 
            // textBox_dustugu_bolge
            // 
            this.textBox_dustugu_bolge.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.textBox_dustugu_bolge.Location = new System.Drawing.Point(483, 736);
            this.textBox_dustugu_bolge.Name = "textBox_dustugu_bolge";
            this.textBox_dustugu_bolge.Size = new System.Drawing.Size(100, 20);
            this.textBox_dustugu_bolge.TabIndex = 15;
            // 
            // textBox_vurulan_bolge
            // 
            this.textBox_vurulan_bolge.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.textBox_vurulan_bolge.Location = new System.Drawing.Point(483, 707);
            this.textBox_vurulan_bolge.Name = "textBox_vurulan_bolge";
            this.textBox_vurulan_bolge.Size = new System.Drawing.Size(100, 20);
            this.textBox_vurulan_bolge.TabIndex = 14;
            // 
            // label6
            // 
            this.label6.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(601, 738);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(73, 13);
            this.label6.TabIndex = 21;
            this.label6.Text = "Nereden geldi";
            // 
            // label7
            // 
            this.label7.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.label7.AutoSize = true;
            this.label7.Location = new System.Drawing.Point(601, 709);
            this.label7.Name = "label7";
            this.label7.Size = new System.Drawing.Size(112, 13);
            this.label7.TabIndex = 20;
            this.label7.Text = "Topla buluştuğu bölge";
            // 
            // textBox_nereden_geldi
            // 
            this.textBox_nereden_geldi.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.textBox_nereden_geldi.Location = new System.Drawing.Point(730, 732);
            this.textBox_nereden_geldi.Name = "textBox_nereden_geldi";
            this.textBox_nereden_geldi.Size = new System.Drawing.Size(100, 20);
            this.textBox_nereden_geldi.TabIndex = 19;
            // 
            // textBox_bulusulan_bolge
            // 
            this.textBox_bulusulan_bolge.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.textBox_bulusulan_bolge.Location = new System.Drawing.Point(730, 706);
            this.textBox_bulusulan_bolge.Name = "textBox_bulusulan_bolge";
            this.textBox_bulusulan_bolge.Size = new System.Drawing.Size(100, 20);
            this.textBox_bulusulan_bolge.TabIndex = 18;
            // 
            // button_frame_al
            // 
            this.button_frame_al.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.button_frame_al.Location = new System.Drawing.Point(230, 708);
            this.button_frame_al.Name = "button_frame_al";
            this.button_frame_al.Size = new System.Drawing.Size(100, 47);
            this.button_frame_al.TabIndex = 22;
            this.button_frame_al.Text = "Frame başlangıç değerini al";
            this.button_frame_al.UseVisualStyleBackColor = true;
            this.button_frame_al.Click += new System.EventHandler(this.button_frame_al_Click);
            // 
            // button_kaydet
            // 
            this.button_kaydet.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.button_kaydet.Location = new System.Drawing.Point(953, 708);
            this.button_kaydet.Name = "button_kaydet";
            this.button_kaydet.Size = new System.Drawing.Size(100, 45);
            this.button_kaydet.TabIndex = 23;
            this.button_kaydet.Text = "Kaydet";
            this.button_kaydet.UseVisualStyleBackColor = true;
            this.button_kaydet.Click += new System.EventHandler(this.button_kaydet_Click);
            // 
            // checkBox_atis_basarili_mi
            // 
            this.checkBox_atis_basarili_mi.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.checkBox_atis_basarili_mi.AutoSize = true;
            this.checkBox_atis_basarili_mi.Checked = true;
            this.checkBox_atis_basarili_mi.CheckState = System.Windows.Forms.CheckState.Checked;
            this.checkBox_atis_basarili_mi.Location = new System.Drawing.Point(856, 722);
            this.checkBox_atis_basarili_mi.Name = "checkBox_atis_basarili_mi";
            this.checkBox_atis_basarili_mi.Size = new System.Drawing.Size(91, 17);
            this.checkBox_atis_basarili_mi.TabIndex = 24;
            this.checkBox_atis_basarili_mi.Text = "Atış başarılı mı";
            this.checkBox_atis_basarili_mi.UseVisualStyleBackColor = true;
            // 
            // label8
            // 
            this.label8.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label8.AutoSize = true;
            this.label8.Location = new System.Drawing.Point(1105, 104);
            this.label8.Name = "label8";
            this.label8.Size = new System.Drawing.Size(32, 13);
            this.label8.TabIndex = 25;
            this.label8.Text = "1.Kişi";
            // 
            // label9
            // 
            this.label9.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label9.AutoSize = true;
            this.label9.Location = new System.Drawing.Point(1105, 142);
            this.label9.Name = "label9";
            this.label9.Size = new System.Drawing.Size(32, 13);
            this.label9.TabIndex = 26;
            this.label9.Text = "2.Kişi";
            // 
            // comboBox_kisi1
            // 
            this.comboBox_kisi1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.comboBox_kisi1.FormattingEnabled = true;
            this.comboBox_kisi1.Location = new System.Drawing.Point(1164, 101);
            this.comboBox_kisi1.Name = "comboBox_kisi1";
            this.comboBox_kisi1.Size = new System.Drawing.Size(154, 21);
            this.comboBox_kisi1.TabIndex = 27;
            // 
            // comboBox_kisi2
            // 
            this.comboBox_kisi2.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.comboBox_kisi2.FormattingEnabled = true;
            this.comboBox_kisi2.Location = new System.Drawing.Point(1164, 142);
            this.comboBox_kisi2.Name = "comboBox_kisi2";
            this.comboBox_kisi2.Size = new System.Drawing.Size(154, 21);
            this.comboBox_kisi2.TabIndex = 28;
            // 
            // comboBox_spin
            // 
            this.comboBox_spin.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.comboBox_spin.FormattingEnabled = true;
            this.comboBox_spin.Items.AddRange(new object[] {
            "Backspin",
            "Topspin",
            "Slice"});
            this.comboBox_spin.Location = new System.Drawing.Point(1167, 293);
            this.comboBox_spin.Name = "comboBox_spin";
            this.comboBox_spin.Size = new System.Drawing.Size(151, 21);
            this.comboBox_spin.TabIndex = 32;
            this.comboBox_spin.SelectedIndexChanged += new System.EventHandler(this.comboBox_spin_SelectedIndexChanged);
            // 
            // comboBox_vurus
            // 
            this.comboBox_vurus.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.comboBox_vurus.FormattingEnabled = true;
            this.comboBox_vurus.Location = new System.Drawing.Point(1167, 252);
            this.comboBox_vurus.Name = "comboBox_vurus";
            this.comboBox_vurus.Size = new System.Drawing.Size(151, 21);
            this.comboBox_vurus.TabIndex = 31;
            // 
            // label10
            // 
            this.label10.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label10.AutoSize = true;
            this.label10.Location = new System.Drawing.Point(1107, 301);
            this.label10.Name = "label10";
            this.label10.Size = new System.Drawing.Size(28, 13);
            this.label10.TabIndex = 30;
            this.label10.Text = "Spin";
            // 
            // label11
            // 
            this.label11.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label11.AutoSize = true;
            this.label11.Location = new System.Drawing.Point(1107, 255);
            this.label11.Name = "label11";
            this.label11.Size = new System.Drawing.Size(51, 13);
            this.label11.TabIndex = 29;
            this.label11.Text = "Vuruş stili";
            // 
            // button_kisi_degistir
            // 
            this.button_kisi_degistir.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button_kisi_degistir.Location = new System.Drawing.Point(1107, 182);
            this.button_kisi_degistir.Name = "button_kisi_degistir";
            this.button_kisi_degistir.Size = new System.Drawing.Size(211, 30);
            this.button_kisi_degistir.TabIndex = 33;
            this.button_kisi_degistir.Text = "Kişi Değiştir";
            this.button_kisi_degistir.UseVisualStyleBackColor = true;
            this.button_kisi_degistir.Click += new System.EventHandler(this.button_kisi_degistir_Click);
            // 
            // textBox1
            // 
            this.textBox1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.textBox1.Location = new System.Drawing.Point(1188, 457);
            this.textBox1.Name = "textBox1";
            this.textBox1.Size = new System.Drawing.Size(130, 20);
            this.textBox1.TabIndex = 34;
            // 
            // textBox2
            // 
            this.textBox2.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.textBox2.Location = new System.Drawing.Point(1188, 483);
            this.textBox2.Name = "textBox2";
            this.textBox2.Size = new System.Drawing.Size(130, 20);
            this.textBox2.TabIndex = 35;
            // 
            // textBox3
            // 
            this.textBox3.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.textBox3.Location = new System.Drawing.Point(1188, 509);
            this.textBox3.Name = "textBox3";
            this.textBox3.Size = new System.Drawing.Size(130, 20);
            this.textBox3.TabIndex = 36;
            // 
            // textBox4
            // 
            this.textBox4.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.textBox4.Location = new System.Drawing.Point(1188, 535);
            this.textBox4.Name = "textBox4";
            this.textBox4.Size = new System.Drawing.Size(130, 20);
            this.textBox4.TabIndex = 37;
            // 
            // button2
            // 
            this.button2.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button2.Location = new System.Drawing.Point(30, 573);
            this.button2.Name = "button2";
            this.button2.Size = new System.Drawing.Size(206, 23);
            this.button2.TabIndex = 38;
            this.button2.Text = "Manuel Nokta Al";
            this.button2.UseVisualStyleBackColor = true;
            this.button2.Visible = false;
            this.button2.Click += new System.EventHandler(this.button_noktaAl_Click);
            // 
            // button_cizgili
            // 
            this.button_cizgili.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button_cizgili.Location = new System.Drawing.Point(1112, 602);
            this.button_cizgili.Name = "button_cizgili";
            this.button_cizgili.Size = new System.Drawing.Size(206, 23);
            this.button_cizgili.TabIndex = 39;
            this.button_cizgili.Text = "Çizgili Çizim";
            this.button_cizgili.UseVisualStyleBackColor = true;
            this.button_cizgili.Click += new System.EventHandler(this.button_ciz_Click);
            // 
            // button4
            // 
            this.button4.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button4.Location = new System.Drawing.Point(1112, 660);
            this.button4.Name = "button4";
            this.button4.Size = new System.Drawing.Size(206, 23);
            this.button4.TabIndex = 40;
            this.button4.Text = "Sil";
            this.button4.UseVisualStyleBackColor = true;
            this.button4.Click += new System.EventHandler(this.button_temizle_Click);
            // 
            // label1
            // 
            this.label1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(1107, 457);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(61, 13);
            this.label1.TabIndex = 42;
            this.label1.Text = "Koordinat 1";
            // 
            // label12
            // 
            this.label12.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label12.AutoSize = true;
            this.label12.Location = new System.Drawing.Point(1107, 490);
            this.label12.Name = "label12";
            this.label12.Size = new System.Drawing.Size(61, 13);
            this.label12.TabIndex = 43;
            this.label12.Text = "Koordinat 2";
            // 
            // label13
            // 
            this.label13.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label13.AutoSize = true;
            this.label13.Location = new System.Drawing.Point(1107, 516);
            this.label13.Name = "label13";
            this.label13.Size = new System.Drawing.Size(61, 13);
            this.label13.TabIndex = 44;
            this.label13.Text = "Koordinat 3";
            // 
            // label14
            // 
            this.label14.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label14.AutoSize = true;
            this.label14.Location = new System.Drawing.Point(1107, 542);
            this.label14.Name = "label14";
            this.label14.Size = new System.Drawing.Size(61, 13);
            this.label14.TabIndex = 45;
            this.label14.Text = "Koordinat 4";
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(30, 605);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(122, 23);
            this.button1.TabIndex = 46;
            this.button1.Text = "Roboflow-tenis- sahası";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Visible = false;
            this.button1.Click += new System.EventHandler(this.button_cizgileri_bul_Click);
            // 
            // button5
            // 
            this.button5.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button5.Location = new System.Drawing.Point(1112, 573);
            this.button5.Name = "button5";
            this.button5.Size = new System.Drawing.Size(206, 23);
            this.button5.TabIndex = 47;
            this.button5.Text = "Sürüklenebilir Noktalar";
            this.button5.UseVisualStyleBackColor = true;
            this.button5.Click += new System.EventHandler(this.button_show_points_Click);
            // 
            // button_cizgisiz
            // 
            this.button_cizgisiz.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button_cizgisiz.Location = new System.Drawing.Point(1112, 631);
            this.button_cizgisiz.Name = "button_cizgisiz";
            this.button_cizgisiz.Size = new System.Drawing.Size(206, 23);
            this.button_cizgisiz.TabIndex = 48;
            this.button_cizgisiz.Text = "Çizgisiz Çizim";
            this.button_cizgisiz.UseVisualStyleBackColor = true;
            this.button_cizgisiz.Click += new System.EventHandler(this.button_cizgisiz_Click);
            // 
            // radioButton1
            // 
            this.radioButton1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.radioButton1.AutoSize = true;
            this.radioButton1.Location = new System.Drawing.Point(1163, 348);
            this.radioButton1.Name = "radioButton1";
            this.radioButton1.Size = new System.Drawing.Size(37, 17);
            this.radioButton1.TabIndex = 49;
            this.radioButton1.TabStop = true;
            this.radioButton1.Text = "Alt";
            this.radioButton1.UseVisualStyleBackColor = true;
            // 
            // radioButton2
            // 
            this.radioButton2.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.radioButton2.AutoSize = true;
            this.radioButton2.Location = new System.Drawing.Point(1209, 348);
            this.radioButton2.Name = "radioButton2";
            this.radioButton2.Size = new System.Drawing.Size(45, 17);
            this.radioButton2.TabIndex = 50;
            this.radioButton2.TabStop = true;
            this.radioButton2.Text = "Orta";
            this.radioButton2.UseVisualStyleBackColor = true;
            // 
            // radioButton3
            // 
            this.radioButton3.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.radioButton3.AutoSize = true;
            this.radioButton3.Location = new System.Drawing.Point(1267, 348);
            this.radioButton3.Name = "radioButton3";
            this.radioButton3.Size = new System.Drawing.Size(61, 17);
            this.radioButton3.TabIndex = 51;
            this.radioButton3.TabStop = true;
            this.radioButton3.Text = "Yüksek";
            this.radioButton3.UseVisualStyleBackColor = true;
            // 
            // radioButton4
            // 
            this.radioButton4.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.radioButton4.AutoSize = true;
            this.radioButton4.Location = new System.Drawing.Point(1167, 397);
            this.radioButton4.Name = "radioButton4";
            this.radioButton4.Size = new System.Drawing.Size(51, 17);
            this.radioButton4.TabIndex = 53;
            this.radioButton4.TabStop = true;
            this.radioButton4.Text = "Kolay";
            this.radioButton4.UseVisualStyleBackColor = true;
            // 
            // radioButton5
            // 
            this.radioButton5.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.radioButton5.AutoSize = true;
            this.radioButton5.Location = new System.Drawing.Point(1224, 397);
            this.radioButton5.Name = "radioButton5";
            this.radioButton5.Size = new System.Drawing.Size(45, 17);
            this.radioButton5.TabIndex = 52;
            this.radioButton5.TabStop = true;
            this.radioButton5.Text = "Nötr";
            this.radioButton5.UseVisualStyleBackColor = true;
            // 
            // radioButton6
            // 
            this.radioButton6.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.radioButton6.AutoSize = true;
            this.radioButton6.Location = new System.Drawing.Point(1282, 397);
            this.radioButton6.Name = "radioButton6";
            this.radioButton6.Size = new System.Drawing.Size(41, 17);
            this.radioButton6.TabIndex = 54;
            this.radioButton6.TabStop = true;
            this.radioButton6.Text = "Zor";
            this.radioButton6.UseVisualStyleBackColor = true;
            // 
            // label15
            // 
            this.label15.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label15.AutoSize = true;
            this.label15.Location = new System.Drawing.Point(1104, 348);
            this.label15.Name = "label15";
            this.label15.Size = new System.Drawing.Size(53, 13);
            this.label15.TabIndex = 55;
            this.label15.Text = "Yükseklik";
            // 
            // label16
            // 
            this.label16.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label16.AutoSize = true;
            this.label16.Location = new System.Drawing.Point(1102, 399);
            this.label16.Name = "label16";
            this.label16.Size = new System.Drawing.Size(65, 13);
            this.label16.TabIndex = 56;
            this.label16.Text = "Karakteristik";
            // 
            // label_video_adi
            // 
            this.label_video_adi.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label_video_adi.AutoSize = true;
            this.label_video_adi.Location = new System.Drawing.Point(1109, 726);
            this.label_video_adi.Name = "label_video_adi";
            this.label_video_adi.Size = new System.Drawing.Size(52, 13);
            this.label_video_adi.TabIndex = 57;
            this.label_video_adi.Text = "Video Adı";
            // 
            // label_kalinan_zaman
            // 
            this.label_kalinan_zaman.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label_kalinan_zaman.AutoSize = true;
            this.label_kalinan_zaman.Location = new System.Drawing.Point(1109, 746);
            this.label_kalinan_zaman.Name = "label_kalinan_zaman";
            this.label_kalinan_zaman.Size = new System.Drawing.Size(75, 13);
            this.label_kalinan_zaman.TabIndex = 58;
            this.label_kalinan_zaman.Text = "Kalınan saniye";
            // 
            // button_otomatik
            // 
            this.button_otomatik.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.button_otomatik.Location = new System.Drawing.Point(1112, 689);
            this.button_otomatik.Name = "button_otomatik";
            this.button_otomatik.Size = new System.Drawing.Size(206, 23);
            this.button_otomatik.TabIndex = 59;
            this.button_otomatik.Text = "Otomatik Yerleştir";
            this.button_otomatik.UseVisualStyleBackColor = true;
            this.button_otomatik.Click += new System.EventHandler(this.button_otomatik_Click);
            // 
            // Form_video_oynat
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1340, 767);
            this.Controls.Add(this.button_otomatik);
            this.Controls.Add(this.label_kalinan_zaman);
            this.Controls.Add(this.label_video_adi);
            this.Controls.Add(this.label16);
            this.Controls.Add(this.label15);
            this.Controls.Add(this.radioButton6);
            this.Controls.Add(this.radioButton4);
            this.Controls.Add(this.radioButton5);
            this.Controls.Add(this.radioButton3);
            this.Controls.Add(this.radioButton2);
            this.Controls.Add(this.radioButton1);
            this.Controls.Add(this.button_cizgisiz);
            this.Controls.Add(this.button5);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.label14);
            this.Controls.Add(this.label13);
            this.Controls.Add(this.label12);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.button4);
            this.Controls.Add(this.button_cizgili);
            this.Controls.Add(this.button2);
            this.Controls.Add(this.textBox4);
            this.Controls.Add(this.textBox3);
            this.Controls.Add(this.textBox2);
            this.Controls.Add(this.textBox1);
            this.Controls.Add(this.button_kisi_degistir);
            this.Controls.Add(this.comboBox_spin);
            this.Controls.Add(this.comboBox_vurus);
            this.Controls.Add(this.label10);
            this.Controls.Add(this.label11);
            this.Controls.Add(this.comboBox_kisi2);
            this.Controls.Add(this.comboBox_kisi1);
            this.Controls.Add(this.label9);
            this.Controls.Add(this.label8);
            this.Controls.Add(this.checkBox_atis_basarili_mi);
            this.Controls.Add(this.button_kaydet);
            this.Controls.Add(this.button_frame_al);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.label7);
            this.Controls.Add(this.textBox_nereden_geldi);
            this.Controls.Add(this.textBox_bulusulan_bolge);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.label5);
            this.Controls.Add(this.textBox_dustugu_bolge);
            this.Controls.Add(this.textBox_vurulan_bolge);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.textBox_frame_bit);
            this.Controls.Add(this.textBox_frame_bas);
            this.Controls.Add(this.labelFrameSayaci);
            this.Controls.Add(this.label_ekran_suresi);
            this.Controls.Add(this.webView21);
            this.Controls.Add(this.button_dosyaAc);
            this.MinimumSize = new System.Drawing.Size(700, 450);
            this.Name = "Form_video_oynat";
            this.Text = "Video Oynatıcı";
            this.Load += new System.EventHandler(this.Form_video_oynat_Load);
            ((System.ComponentModel.ISupportInitialize)(this.webView21)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion
        private Microsoft.Web.WebView2.WinForms.WebView2 webView21;
        private System.Windows.Forms.Button button_dosyaAc;
        private System.Windows.Forms.Label label_ekran_suresi;
        private System.Windows.Forms.Label labelFrameSayaci;
        private System.Windows.Forms.TextBox textBox_frame_bas;
        private System.Windows.Forms.TextBox textBox_frame_bit;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.TextBox textBox_dustugu_bolge;
        private System.Windows.Forms.TextBox textBox_vurulan_bolge;
        private System.Windows.Forms.Label label6;
        private System.Windows.Forms.Label label7;
        private System.Windows.Forms.TextBox textBox_nereden_geldi;
        private System.Windows.Forms.TextBox textBox_bulusulan_bolge;
        private System.Windows.Forms.Button button_frame_al;
        private System.Windows.Forms.Button button_kaydet;
        private System.Windows.Forms.CheckBox checkBox_atis_basarili_mi;
        private System.Windows.Forms.Label label8;
        private System.Windows.Forms.Label label9;
        private System.Windows.Forms.ComboBox comboBox_kisi1;
        private System.Windows.Forms.ComboBox comboBox_kisi2;
        private System.Windows.Forms.ComboBox comboBox_spin;
        private System.Windows.Forms.ComboBox comboBox_vurus;
        private System.Windows.Forms.Label label10;
        private System.Windows.Forms.Label label11;
        private System.Windows.Forms.Button button_kisi_degistir;
        private System.Windows.Forms.TextBox textBox1;
        private System.Windows.Forms.TextBox textBox2;
        private System.Windows.Forms.TextBox textBox3;
        private System.Windows.Forms.TextBox textBox4;
        private System.Windows.Forms.Button button2;
        private System.Windows.Forms.Button button_cizgili;
        private System.Windows.Forms.Button button4;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label label12;
        private System.Windows.Forms.Label label13;
        private System.Windows.Forms.Label label14;
        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.Button button5;
        private System.Windows.Forms.Button button_cizgisiz;
        private System.Windows.Forms.RadioButton radioButton1;
        private System.Windows.Forms.RadioButton radioButton2;
        private System.Windows.Forms.RadioButton radioButton3;
        private System.Windows.Forms.RadioButton radioButton4;
        private System.Windows.Forms.RadioButton radioButton5;
        private System.Windows.Forms.RadioButton radioButton6;
        private System.Windows.Forms.Label label15;
        private System.Windows.Forms.Label label16;
        private System.Windows.Forms.Label label_video_adi;
        private System.Windows.Forms.Label label_kalinan_zaman;
        private System.Windows.Forms.Button button_otomatik;
    }
}
