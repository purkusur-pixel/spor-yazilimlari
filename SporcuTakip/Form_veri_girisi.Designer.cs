
namespace SporcuTakip
{
    partial class Form_veri_girisi
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.btn_kisi_kaydet = new System.Windows.Forms.Button();
            this.txt_isim = new System.Windows.Forms.TextBox();
            this.txt_soyisim = new System.Windows.Forms.TextBox();
            this.txt_notlar = new System.Windows.Forms.TextBox();
            this.txt_kayitlikisiler = new System.Windows.Forms.TextBox();
            this.isim_lbl = new System.Windows.Forms.Label();
            this.soyisim_lbl = new System.Windows.Forms.Label();
            this.notlar_lbl = new System.Windows.Forms.Label();
            this.kayitli_kisiler_lbl = new System.Windows.Forms.Label();
            this.vurus_stili_lbl = new System.Windows.Forms.Label();
            this.vurus_stili_adi_txt = new System.Windows.Forms.TextBox();
            this.kayitli_vurus_stilleri_lbl = new System.Windows.Forms.Label();
            this.kayitli_vurus_stilleri_txt = new System.Windows.Forms.TextBox();
            this.stik_ekle_btn = new System.Windows.Forms.Button();
            this.button_db = new System.Windows.Forms.Button();
            this.button_kisi_sil = new System.Windows.Forms.Button();
            this.comboBox_kisiler = new System.Windows.Forms.ComboBox();
            this.button_vurus_sil = new System.Windows.Forms.Button();
            this.comboBox_vurus_stilleri = new System.Windows.Forms.ComboBox();
            this.button1 = new System.Windows.Forms.Button();
            this.kayitli_spinler_txt = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.spin_adi_txt = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.comboBox_spinler = new System.Windows.Forms.ComboBox();
            this.button2 = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // btn_kisi_kaydet
            // 
            this.btn_kisi_kaydet.Location = new System.Drawing.Point(72, 250);
            this.btn_kisi_kaydet.Name = "btn_kisi_kaydet";
            this.btn_kisi_kaydet.Size = new System.Drawing.Size(170, 23);
            this.btn_kisi_kaydet.TabIndex = 0;
            this.btn_kisi_kaydet.Text = "Kişi Kaydet";
            this.btn_kisi_kaydet.UseVisualStyleBackColor = true;
            this.btn_kisi_kaydet.Click += new System.EventHandler(this.button_kisi_kaydet_Click);
            // 
            // txt_isim
            // 
            this.txt_isim.Location = new System.Drawing.Point(72, 75);
            this.txt_isim.Margin = new System.Windows.Forms.Padding(2);
            this.txt_isim.Name = "txt_isim";
            this.txt_isim.Size = new System.Drawing.Size(170, 20);
            this.txt_isim.TabIndex = 1;
            // 
            // txt_soyisim
            // 
            this.txt_soyisim.Location = new System.Drawing.Point(72, 107);
            this.txt_soyisim.Margin = new System.Windows.Forms.Padding(2);
            this.txt_soyisim.Name = "txt_soyisim";
            this.txt_soyisim.Size = new System.Drawing.Size(170, 20);
            this.txt_soyisim.TabIndex = 2;
            // 
            // txt_notlar
            // 
            this.txt_notlar.Location = new System.Drawing.Point(72, 147);
            this.txt_notlar.Margin = new System.Windows.Forms.Padding(2);
            this.txt_notlar.Multiline = true;
            this.txt_notlar.Name = "txt_notlar";
            this.txt_notlar.Size = new System.Drawing.Size(170, 98);
            this.txt_notlar.TabIndex = 3;
            // 
            // txt_kayitlikisiler
            // 
            this.txt_kayitlikisiler.Location = new System.Drawing.Point(72, 279);
            this.txt_kayitlikisiler.Margin = new System.Windows.Forms.Padding(2);
            this.txt_kayitlikisiler.Multiline = true;
            this.txt_kayitlikisiler.Name = "txt_kayitlikisiler";
            this.txt_kayitlikisiler.Size = new System.Drawing.Size(170, 174);
            this.txt_kayitlikisiler.TabIndex = 4;
            // 
            // isim_lbl
            // 
            this.isim_lbl.AutoSize = true;
            this.isim_lbl.Location = new System.Drawing.Point(46, 75);
            this.isim_lbl.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.isim_lbl.Name = "isim_lbl";
            this.isim_lbl.Size = new System.Drawing.Size(23, 13);
            this.isim_lbl.TabIndex = 5;
            this.isim_lbl.Text = "Ad:";
            // 
            // soyisim_lbl
            // 
            this.soyisim_lbl.AutoSize = true;
            this.soyisim_lbl.Location = new System.Drawing.Point(34, 107);
            this.soyisim_lbl.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.soyisim_lbl.Name = "soyisim_lbl";
            this.soyisim_lbl.Size = new System.Drawing.Size(40, 13);
            this.soyisim_lbl.TabIndex = 6;
            this.soyisim_lbl.Text = "Soyad:";
            // 
            // notlar_lbl
            // 
            this.notlar_lbl.AutoSize = true;
            this.notlar_lbl.Location = new System.Drawing.Point(34, 150);
            this.notlar_lbl.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.notlar_lbl.Name = "notlar_lbl";
            this.notlar_lbl.Size = new System.Drawing.Size(38, 13);
            this.notlar_lbl.TabIndex = 7;
            this.notlar_lbl.Text = "Notlar:";
            // 
            // kayitli_kisiler_lbl
            // 
            this.kayitli_kisiler_lbl.AutoSize = true;
            this.kayitli_kisiler_lbl.Location = new System.Drawing.Point(4, 279);
            this.kayitli_kisiler_lbl.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.kayitli_kisiler_lbl.Name = "kayitli_kisiler_lbl";
            this.kayitli_kisiler_lbl.Size = new System.Drawing.Size(67, 13);
            this.kayitli_kisiler_lbl.TabIndex = 8;
            this.kayitli_kisiler_lbl.Text = "Kayıtlı Kişiler:";
            // 
            // vurus_stili_lbl
            // 
            this.vurus_stili_lbl.AutoSize = true;
            this.vurus_stili_lbl.Location = new System.Drawing.Point(274, 76);
            this.vurus_stili_lbl.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.vurus_stili_lbl.Name = "vurus_stili_lbl";
            this.vurus_stili_lbl.Size = new System.Drawing.Size(74, 13);
            this.vurus_stili_lbl.TabIndex = 9;
            this.vurus_stili_lbl.Text = "Vuruş Stili Adı:";
            // 
            // vurus_stili_adi_txt
            // 
            this.vurus_stili_adi_txt.Location = new System.Drawing.Point(347, 76);
            this.vurus_stili_adi_txt.Margin = new System.Windows.Forms.Padding(2);
            this.vurus_stili_adi_txt.Multiline = true;
            this.vurus_stili_adi_txt.Name = "vurus_stili_adi_txt";
            this.vurus_stili_adi_txt.Size = new System.Drawing.Size(156, 34);
            this.vurus_stili_adi_txt.TabIndex = 10;
            this.vurus_stili_adi_txt.TextChanged += new System.EventHandler(this.vurus_stili_adi_txt_TextChanged);
            // 
            // kayitli_vurus_stilleri_lbl
            // 
            this.kayitli_vurus_stilleri_lbl.AutoSize = true;
            this.kayitli_vurus_stilleri_lbl.Location = new System.Drawing.Point(252, 121);
            this.kayitli_vurus_stilleri_lbl.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.kayitli_vurus_stilleri_lbl.Name = "kayitli_vurus_stilleri_lbl";
            this.kayitli_vurus_stilleri_lbl.Size = new System.Drawing.Size(97, 13);
            this.kayitli_vurus_stilleri_lbl.TabIndex = 11;
            this.kayitli_vurus_stilleri_lbl.Text = "Kayıtlı Vuruş Stilleri:";
            // 
            // kayitli_vurus_stilleri_txt
            // 
            this.kayitli_vurus_stilleri_txt.Location = new System.Drawing.Point(347, 121);
            this.kayitli_vurus_stilleri_txt.Margin = new System.Windows.Forms.Padding(2);
            this.kayitli_vurus_stilleri_txt.Multiline = true;
            this.kayitli_vurus_stilleri_txt.Name = "kayitli_vurus_stilleri_txt";
            this.kayitli_vurus_stilleri_txt.Size = new System.Drawing.Size(230, 152);
            this.kayitli_vurus_stilleri_txt.TabIndex = 12;
            // 
            // stik_ekle_btn
            // 
            this.stik_ekle_btn.Location = new System.Drawing.Point(507, 76);
            this.stik_ekle_btn.Margin = new System.Windows.Forms.Padding(2);
            this.stik_ekle_btn.Name = "stik_ekle_btn";
            this.stik_ekle_btn.Size = new System.Drawing.Size(69, 33);
            this.stik_ekle_btn.TabIndex = 13;
            this.stik_ekle_btn.Text = "Stil Ekle";
            this.stik_ekle_btn.UseVisualStyleBackColor = true;
            this.stik_ekle_btn.Click += new System.EventHandler(this.stik_ekle_btn_Click);
            // 
            // button_db
            // 
            this.button_db.Location = new System.Drawing.Point(338, 429);
            this.button_db.Name = "button_db";
            this.button_db.Size = new System.Drawing.Size(384, 23);
            this.button_db.TabIndex = 14;
            this.button_db.Text = "Veri Tabanı yedeği üret";
            this.button_db.UseVisualStyleBackColor = true;
            this.button_db.Click += new System.EventHandler(this.button_db_Click);
            // 
            // button_kisi_sil
            // 
            this.button_kisi_sil.Location = new System.Drawing.Point(338, 387);
            this.button_kisi_sil.Name = "button_kisi_sil";
            this.button_kisi_sil.Size = new System.Drawing.Size(121, 23);
            this.button_kisi_sil.TabIndex = 15;
            this.button_kisi_sil.Text = "Kişi Sil";
            this.button_kisi_sil.UseVisualStyleBackColor = true;
            this.button_kisi_sil.Click += new System.EventHandler(this.button_kisi_sil_Click);
            // 
            // comboBox_kisiler
            // 
            this.comboBox_kisiler.FormattingEnabled = true;
            this.comboBox_kisiler.Location = new System.Drawing.Point(338, 348);
            this.comboBox_kisiler.Name = "comboBox_kisiler";
            this.comboBox_kisiler.Size = new System.Drawing.Size(121, 21);
            this.comboBox_kisiler.TabIndex = 16;
            this.comboBox_kisiler.Text = "Kişiler";
            // 
            // button_vurus_sil
            // 
            this.button_vurus_sil.Location = new System.Drawing.Point(465, 387);
            this.button_vurus_sil.Name = "button_vurus_sil";
            this.button_vurus_sil.Size = new System.Drawing.Size(121, 23);
            this.button_vurus_sil.TabIndex = 17;
            this.button_vurus_sil.Text = "Stil Sil";
            this.button_vurus_sil.UseVisualStyleBackColor = true;
            this.button_vurus_sil.Click += new System.EventHandler(this.button_vurus_sil_Click);
            // 
            // comboBox_vurus_stilleri
            // 
            this.comboBox_vurus_stilleri.FormattingEnabled = true;
            this.comboBox_vurus_stilleri.Location = new System.Drawing.Point(465, 348);
            this.comboBox_vurus_stilleri.Name = "comboBox_vurus_stilleri";
            this.comboBox_vurus_stilleri.Size = new System.Drawing.Size(121, 21);
            this.comboBox_vurus_stilleri.TabIndex = 18;
            this.comboBox_vurus_stilleri.Text = "Stiller";
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(841, 76);
            this.button1.Margin = new System.Windows.Forms.Padding(2);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(69, 33);
            this.button1.TabIndex = 23;
            this.button1.Text = "Spin Ekle";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Click += new System.EventHandler(this.button_spin_ekle_Click);
            // 
            // kayitli_spinler_txt
            // 
            this.kayitli_spinler_txt.Location = new System.Drawing.Point(681, 121);
            this.kayitli_spinler_txt.Margin = new System.Windows.Forms.Padding(2);
            this.kayitli_spinler_txt.Multiline = true;
            this.kayitli_spinler_txt.Name = "kayitli_spinler_txt";
            this.kayitli_spinler_txt.Size = new System.Drawing.Size(230, 152);
            this.kayitli_spinler_txt.TabIndex = 22;
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(586, 121);
            this.label1.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(69, 13);
            this.label1.TabIndex = 21;
            this.label1.Text = "Kayıtlı Spinler";
            // 
            // spin_adi_txt
            // 
            this.spin_adi_txt.Location = new System.Drawing.Point(681, 76);
            this.spin_adi_txt.Margin = new System.Windows.Forms.Padding(2);
            this.spin_adi_txt.Multiline = true;
            this.spin_adi_txt.Name = "spin_adi_txt";
            this.spin_adi_txt.Size = new System.Drawing.Size(156, 34);
            this.spin_adi_txt.TabIndex = 20;
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(608, 76);
            this.label2.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(49, 13);
            this.label2.TabIndex = 19;
            this.label2.Text = "Spin Adı:";
            // 
            // comboBox_spinler
            // 
            this.comboBox_spinler.FormattingEnabled = true;
            this.comboBox_spinler.Location = new System.Drawing.Point(601, 348);
            this.comboBox_spinler.Name = "comboBox_spinler";
            this.comboBox_spinler.Size = new System.Drawing.Size(121, 21);
            this.comboBox_spinler.TabIndex = 25;
            this.comboBox_spinler.Text = "Spinler";
            // 
            // button2
            // 
            this.button2.Location = new System.Drawing.Point(601, 387);
            this.button2.Name = "button2";
            this.button2.Size = new System.Drawing.Size(121, 23);
            this.button2.TabIndex = 24;
            this.button2.Text = "Spin Sil";
            this.button2.UseVisualStyleBackColor = true;
            this.button2.Click += new System.EventHandler(this.button_spin_sil_Click);
            // 
            // Form_veri_girisi
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(935, 483);
            this.Controls.Add(this.comboBox_spinler);
            this.Controls.Add(this.button2);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.kayitli_spinler_txt);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.spin_adi_txt);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.comboBox_vurus_stilleri);
            this.Controls.Add(this.button_vurus_sil);
            this.Controls.Add(this.comboBox_kisiler);
            this.Controls.Add(this.button_kisi_sil);
            this.Controls.Add(this.button_db);
            this.Controls.Add(this.stik_ekle_btn);
            this.Controls.Add(this.kayitli_vurus_stilleri_txt);
            this.Controls.Add(this.kayitli_vurus_stilleri_lbl);
            this.Controls.Add(this.vurus_stili_adi_txt);
            this.Controls.Add(this.vurus_stili_lbl);
            this.Controls.Add(this.kayitli_kisiler_lbl);
            this.Controls.Add(this.notlar_lbl);
            this.Controls.Add(this.soyisim_lbl);
            this.Controls.Add(this.isim_lbl);
            this.Controls.Add(this.txt_kayitlikisiler);
            this.Controls.Add(this.txt_notlar);
            this.Controls.Add(this.txt_soyisim);
            this.Controls.Add(this.txt_isim);
            this.Controls.Add(this.btn_kisi_kaydet);
            this.Name = "Form_veri_girisi";
            this.Text = "Form_veri_girisi";
            this.Load += new System.EventHandler(this.Form_veri_girisi_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button btn_kisi_kaydet;
        private System.Windows.Forms.TextBox txt_isim;
        private System.Windows.Forms.TextBox txt_soyisim;
        private System.Windows.Forms.TextBox txt_notlar;
        private System.Windows.Forms.TextBox txt_kayitlikisiler;
        private System.Windows.Forms.Label isim_lbl;
        private System.Windows.Forms.Label soyisim_lbl;
        private System.Windows.Forms.Label notlar_lbl;
        private System.Windows.Forms.Label kayitli_kisiler_lbl;
        private System.Windows.Forms.Label vurus_stili_lbl;
        private System.Windows.Forms.TextBox vurus_stili_adi_txt;
        private System.Windows.Forms.Label kayitli_vurus_stilleri_lbl;
        private System.Windows.Forms.TextBox kayitli_vurus_stilleri_txt;
        private System.Windows.Forms.Button stik_ekle_btn;
        private System.Windows.Forms.Button button_db;
        private System.Windows.Forms.Button button_kisi_sil;
        private System.Windows.Forms.ComboBox comboBox_kisiler;
        private System.Windows.Forms.Button button_vurus_sil;
        private System.Windows.Forms.ComboBox comboBox_vurus_stilleri;
        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.TextBox kayitli_spinler_txt;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.TextBox spin_adi_txt;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.ComboBox comboBox_spinler;
        private System.Windows.Forms.Button button2;
    }
}