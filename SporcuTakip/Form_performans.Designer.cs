//namespace SporcuTakip
//{
//    partial class Form_performans
//    {
//        private System.ComponentModel.IContainer components = null;

//        private System.Windows.Forms.TableLayoutPanel tableMain;
//        private System.Windows.Forms.Panel panelLeft;
//        private System.Windows.Forms.TableLayoutPanel tableLeft;
//        private System.Windows.Forms.Label labelTest;
//        private System.Windows.Forms.ComboBox comboTest;
//        private System.Windows.Forms.Label labelKisi;
//        private System.Windows.Forms.ComboBox comboKisi;
//        private System.Windows.Forms.FlowLayoutPanel flowButtons;
//        private System.Windows.Forms.Button btnKisiEkle;
//        private System.Windows.Forms.Button btnTestiBaslat;
//        private System.Windows.Forms.Button btnKaydet;
//        private System.Windows.Forms.Button btnGrafikTemizle;

//        private System.Windows.Forms.Panel panelRight;
//        private System.Windows.Forms.SplitContainer splitRight;

//        // CHART YOK! Yerine Panel:
//        private System.Windows.Forms.Panel panelCanvas;

//        private System.Windows.Forms.DataGridView gridSonuclar;

//        protected override void Dispose(bool disposing)
//        {
//            if (disposing && (components != null)) components.Dispose();
//            base.Dispose(disposing);
//        }

//        private void InitializeComponent()
//        {
//            this.tableMain = new System.Windows.Forms.TableLayoutPanel();
//            this.panelLeft = new System.Windows.Forms.Panel();
//            this.tableLeft = new System.Windows.Forms.TableLayoutPanel();
//            this.labelTest = new System.Windows.Forms.Label();
//            this.comboTest = new System.Windows.Forms.ComboBox();
//            this.labelKisi = new System.Windows.Forms.Label();
//            this.comboKisi = new System.Windows.Forms.ComboBox();
//            this.flowButtons = new System.Windows.Forms.FlowLayoutPanel();
//            this.btnKisiEkle = new System.Windows.Forms.Button();
//            this.btnTestiBaslat = new System.Windows.Forms.Button();
//            this.btnKaydet = new System.Windows.Forms.Button();
//            this.btnGrafikTemizle = new System.Windows.Forms.Button();
//            this.panelRight = new System.Windows.Forms.Panel();
//            this.splitRight = new System.Windows.Forms.SplitContainer();
//            this.panelCanvas = new System.Windows.Forms.Panel();
//            this.gridSonuclar = new System.Windows.Forms.DataGridView();
//            this.tableMain.SuspendLayout();
//            this.panelLeft.SuspendLayout();
//            this.tableLeft.SuspendLayout();
//            this.flowButtons.SuspendLayout();
//            this.panelRight.SuspendLayout();
//            ((System.ComponentModel.ISupportInitialize)(this.splitRight)).BeginInit();
//            this.splitRight.Panel1.SuspendLayout();
//            this.splitRight.Panel2.SuspendLayout();
//            this.splitRight.SuspendLayout();
//            ((System.ComponentModel.ISupportInitialize)(this.gridSonuclar)).BeginInit();
//            this.SuspendLayout();
//            // 
//            // tableMain
//            // 
//            this.tableMain.ColumnCount = 2;
//            this.tableMain.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 285F));
//            this.tableMain.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
//            this.tableMain.Controls.Add(this.panelLeft, 0, 0);
//            this.tableMain.Controls.Add(this.panelRight, 1, 0);
//            this.tableMain.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.tableMain.Location = new System.Drawing.Point(0, 0);
//            this.tableMain.Name = "tableMain";
//            this.tableMain.RowCount = 1;
//            this.tableMain.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
//            this.tableMain.Size = new System.Drawing.Size(1000, 600);
//            this.tableMain.TabIndex = 0;
//            // 
//            // panelLeft
//            // 
//            this.panelLeft.Controls.Add(this.tableLeft);
//            this.panelLeft.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.panelLeft.Location = new System.Drawing.Point(3, 3);
//            this.panelLeft.Name = "panelLeft";
//            this.panelLeft.Padding = new System.Windows.Forms.Padding(10);
//            this.panelLeft.Size = new System.Drawing.Size(279, 594);
//            this.panelLeft.TabIndex = 0;
//            // 
//            // tableLeft
//            // 
//            this.tableLeft.ColumnCount = 1;
//            this.tableLeft.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
//            this.tableLeft.Controls.Add(this.labelTest, 0, 0);
//            this.tableLeft.Controls.Add(this.comboTest, 0, 1);
//            this.tableLeft.Controls.Add(this.labelKisi, 0, 2);
//            this.tableLeft.Controls.Add(this.comboKisi, 0, 3);
//            this.tableLeft.Controls.Add(this.flowButtons, 0, 4);
//            this.tableLeft.Dock = System.Windows.Forms.DockStyle.Top;
//            this.tableLeft.Location = new System.Drawing.Point(10, 10);
//            this.tableLeft.Name = "tableLeft";
//            this.tableLeft.RowCount = 5;
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 36F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 36F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 120F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
//            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 20F));
//            this.tableLeft.Size = new System.Drawing.Size(259, 584);
//            this.tableLeft.TabIndex = 0;
//            // 
//            // labelTest
//            // 
//            this.labelTest.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.labelTest.Location = new System.Drawing.Point(3, 0);
//            this.labelTest.Name = "labelTest";
//            this.labelTest.Size = new System.Drawing.Size(253, 28);
//            this.labelTest.TabIndex = 0;
//            this.labelTest.Text = "Test";
//            this.labelTest.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
//            // 
//            // comboTest
//            // 
//            this.comboTest.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.comboTest.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
//            this.comboTest.Items.AddRange(new object[] {
//            "CMJ (Countermovement Jump)",
//            "SJ (Squat Jump)",
//            "IMTP (Isometric Mid-Thigh Pull)",
//            "Drop Jump",
//            "Custom"});
//            this.comboTest.Location = new System.Drawing.Point(3, 31);
//            this.comboTest.Name = "comboTest";
//            this.comboTest.Size = new System.Drawing.Size(253, 21);
//            this.comboTest.TabIndex = 1;
//            // 
//            // labelKisi
//            // 
//            this.labelKisi.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.labelKisi.Location = new System.Drawing.Point(3, 64);
//            this.labelKisi.Name = "labelKisi";
//            this.labelKisi.Size = new System.Drawing.Size(253, 28);
//            this.labelKisi.TabIndex = 2;
//            this.labelKisi.Text = "Kişi";
//            this.labelKisi.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
//            // 
//            // comboKisi
//            // 
//            this.comboKisi.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.comboKisi.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
//            this.comboKisi.Location = new System.Drawing.Point(3, 95);
//            this.comboKisi.Name = "comboKisi";
//            this.tableLeft.SetRowSpan(this.comboKisi, 2);
//            this.comboKisi.Size = new System.Drawing.Size(253, 21);
//            this.comboKisi.TabIndex = 3;
//            // 
//            // flowButtons
//            // 
//            this.flowButtons.Controls.Add(this.btnKisiEkle);
//            this.flowButtons.Controls.Add(this.btnTestiBaslat);
//            this.flowButtons.Controls.Add(this.btnKaydet);
//            this.flowButtons.Controls.Add(this.btnGrafikTemizle);
//            this.flowButtons.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.flowButtons.FlowDirection = System.Windows.Forms.FlowDirection.TopDown;
//            this.flowButtons.Location = new System.Drawing.Point(3, 251);
//            this.flowButtons.Name = "flowButtons";
//            this.flowButtons.Size = new System.Drawing.Size(253, 330);
//            this.flowButtons.TabIndex = 4;
//            // 
//            // btnKisiEkle
//            // 
//            this.btnKisiEkle.Location = new System.Drawing.Point(3, 3);
//            this.btnKisiEkle.Name = "btnKisiEkle";
//            this.btnKisiEkle.Size = new System.Drawing.Size(240, 23);
//            this.btnKisiEkle.TabIndex = 0;
//            this.btnKisiEkle.Text = "Kişi Ekle";
//            this.btnKisiEkle.Click += new System.EventHandler(this.btnKisiEkle_Click);
//            // 
//            // btnTestiBaslat
//            // 
//            this.btnTestiBaslat.Location = new System.Drawing.Point(3, 32);
//            this.btnTestiBaslat.Name = "btnTestiBaslat";
//            this.btnTestiBaslat.Size = new System.Drawing.Size(240, 23);
//            this.btnTestiBaslat.TabIndex = 1;
//            this.btnTestiBaslat.Text = "Testi Başlat";
//            this.btnTestiBaslat.Click += new System.EventHandler(this.btnTestiBaslat_Click);
//            // 
//            // btnKaydet
//            // 
//            this.btnKaydet.Location = new System.Drawing.Point(3, 61);
//            this.btnKaydet.Name = "btnKaydet";
//            this.btnKaydet.Size = new System.Drawing.Size(240, 23);
//            this.btnKaydet.TabIndex = 2;
//            this.btnKaydet.Text = "Kaydet";
//            this.btnKaydet.Click += new System.EventHandler(this.btnKaydet_Click);
//            // 
//            // btnGrafikTemizle
//            // 
//            this.btnGrafikTemizle.Location = new System.Drawing.Point(3, 90);
//            this.btnGrafikTemizle.Name = "btnGrafikTemizle";
//            this.btnGrafikTemizle.Size = new System.Drawing.Size(240, 23);
//            this.btnGrafikTemizle.TabIndex = 3;
//            this.btnGrafikTemizle.Text = "Grafiği Temizle";
//            this.btnGrafikTemizle.Click += new System.EventHandler(this.btnGrafikTemizle_Click);
//            // 
//            // panelRight
//            // 
//            this.panelRight.Controls.Add(this.splitRight);
//            this.panelRight.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.panelRight.Location = new System.Drawing.Point(288, 3);
//            this.panelRight.Name = "panelRight";
//            this.panelRight.Padding = new System.Windows.Forms.Padding(10);
//            this.panelRight.Size = new System.Drawing.Size(709, 594);
//            this.panelRight.TabIndex = 1;
//            // 
//            // splitRight
//            // 
//            this.splitRight.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.splitRight.Location = new System.Drawing.Point(10, 10);
//            this.splitRight.Name = "splitRight";
//            this.splitRight.Orientation = System.Windows.Forms.Orientation.Horizontal;
//            // 
//            // splitRight.Panel1
//            // 
//            this.splitRight.Panel1.Controls.Add(this.panelCanvas);
//            // 
//            // splitRight.Panel2
//            // 
//            this.splitRight.Panel2.Controls.Add(this.gridSonuclar);
//            this.splitRight.Size = new System.Drawing.Size(689, 574);
//            this.splitRight.SplitterDistance = 287;
//            this.splitRight.TabIndex = 0;
//            // 
//            // panelCanvas
//            // 
//            this.panelCanvas.BackColor = System.Drawing.Color.White;
//            this.panelCanvas.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.panelCanvas.Location = new System.Drawing.Point(0, 0);
//            this.panelCanvas.Name = "panelCanvas";
//            this.panelCanvas.Size = new System.Drawing.Size(689, 287);
//            this.panelCanvas.TabIndex = 0;
//            this.panelCanvas.Paint += new System.Windows.Forms.PaintEventHandler(this.panelCanvas_Paint);
//            this.panelCanvas.Resize += new System.EventHandler(this.panelCanvas_Resize);
//            // 
//            // gridSonuclar
//            // 
//            this.gridSonuclar.AllowUserToAddRows = false;
//            this.gridSonuclar.AllowUserToDeleteRows = false;
//            this.gridSonuclar.AutoSizeColumnsMode = System.Windows.Forms.DataGridViewAutoSizeColumnsMode.Fill;
//            this.gridSonuclar.Dock = System.Windows.Forms.DockStyle.Fill;
//            this.gridSonuclar.Location = new System.Drawing.Point(0, 0);
//            this.gridSonuclar.Name = "gridSonuclar";
//            this.gridSonuclar.ReadOnly = true;
//            this.gridSonuclar.RowHeadersVisible = false;
//            this.gridSonuclar.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
//            this.gridSonuclar.Size = new System.Drawing.Size(689, 283);
//            this.gridSonuclar.TabIndex = 0;
//            // 
//            // Form_performans
//            // 
//            this.ClientSize = new System.Drawing.Size(1000, 600);
//            this.Controls.Add(this.tableMain);
//            this.Name = "Form_performans";
//            this.Text = "Performans (ForceDesk - Basit Çizim)";
//            this.Load += new System.EventHandler(this.Form_performans_Load);
//            this.tableMain.ResumeLayout(false);
//            this.panelLeft.ResumeLayout(false);
//            this.tableLeft.ResumeLayout(false);
//            this.flowButtons.ResumeLayout(false);
//            this.panelRight.ResumeLayout(false);
//            this.splitRight.Panel1.ResumeLayout(false);
//            this.splitRight.Panel2.ResumeLayout(false);
//            ((System.ComponentModel.ISupportInitialize)(this.splitRight)).EndInit();
//            this.splitRight.ResumeLayout(false);
//            ((System.ComponentModel.ISupportInitialize)(this.gridSonuclar)).EndInit();
//            this.ResumeLayout(false);

//        }
//    }
//}
namespace SporcuTakip
{
    partial class Form_performans
    {
        private System.ComponentModel.IContainer components = null;

        private System.Windows.Forms.TableLayoutPanel tableMain;
        private System.Windows.Forms.Panel panelLeft;
        private System.Windows.Forms.TableLayoutPanel tableLeft;
        private System.Windows.Forms.Label labelTest;
        private System.Windows.Forms.ComboBox comboTest;
        private System.Windows.Forms.Label labelKisi;
        private System.Windows.Forms.ComboBox comboKisi;

        private System.Windows.Forms.Label labelPort;      // <--- EKLENDİ
        private System.Windows.Forms.ComboBox comboPort;   // <--- EKLENDİ

        private System.Windows.Forms.FlowLayoutPanel flowButtons;
        private System.Windows.Forms.Button btnKisiEkle;
        private System.Windows.Forms.Button btnTestiBaslat;
        private System.Windows.Forms.Button btnKaydet;
        private System.Windows.Forms.Button btnGrafikTemizle;

        private System.Windows.Forms.Panel panelRight;
        private System.Windows.Forms.SplitContainer splitRight;
        private System.Windows.Forms.Panel panelCanvas;
        private System.Windows.Forms.DataGridView gridSonuclar;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null)) components.Dispose();
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            this.tableMain = new System.Windows.Forms.TableLayoutPanel();
            this.panelLeft = new System.Windows.Forms.Panel();
            this.tableLeft = new System.Windows.Forms.TableLayoutPanel();
            this.labelTest = new System.Windows.Forms.Label();
            this.comboTest = new System.Windows.Forms.ComboBox();
            this.labelKisi = new System.Windows.Forms.Label();
            this.comboKisi = new System.Windows.Forms.ComboBox();
            this.labelPort = new System.Windows.Forms.Label();
            this.comboPort = new System.Windows.Forms.ComboBox();
            this.flowButtons = new System.Windows.Forms.FlowLayoutPanel();
            this.btnKisiEkle = new System.Windows.Forms.Button();
            this.btnTestiBaslat = new System.Windows.Forms.Button();
            this.btnKaydet = new System.Windows.Forms.Button();
            this.btnGrafikTemizle = new System.Windows.Forms.Button();
            this.panelRight = new System.Windows.Forms.Panel();
            this.splitRight = new System.Windows.Forms.SplitContainer();
            this.panelCanvas = new System.Windows.Forms.Panel();
            this.gridSonuclar = new System.Windows.Forms.DataGridView();
            this.tableMain.SuspendLayout();
            this.panelLeft.SuspendLayout();
            this.tableLeft.SuspendLayout();
            this.flowButtons.SuspendLayout();
            this.panelRight.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.splitRight)).BeginInit();
            this.splitRight.Panel1.SuspendLayout();
            this.splitRight.Panel2.SuspendLayout();
            this.splitRight.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.gridSonuclar)).BeginInit();
            this.SuspendLayout();
            // 
            // tableMain
            // 
            this.tableMain.ColumnCount = 2;
            this.tableMain.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 285F));
            this.tableMain.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableMain.Controls.Add(this.panelLeft, 0, 0);
            this.tableMain.Controls.Add(this.panelRight, 1, 0);
            this.tableMain.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableMain.Location = new System.Drawing.Point(0, 0);
            this.tableMain.Name = "tableMain";
            this.tableMain.RowCount = 1;
            this.tableMain.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableMain.Size = new System.Drawing.Size(1000, 600);
            this.tableMain.TabIndex = 0;
            // 
            // panelLeft
            // 
            this.panelLeft.Controls.Add(this.tableLeft);
            this.panelLeft.Dock = System.Windows.Forms.DockStyle.Fill;
            this.panelLeft.Location = new System.Drawing.Point(3, 3);
            this.panelLeft.Name = "panelLeft";
            this.panelLeft.Padding = new System.Windows.Forms.Padding(10);
            this.panelLeft.Size = new System.Drawing.Size(279, 594);
            this.panelLeft.TabIndex = 0;
            // 
            // tableLeft
            // 
            this.tableLeft.ColumnCount = 1;
            this.tableLeft.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLeft.Controls.Add(this.labelTest, 0, 0);
            this.tableLeft.Controls.Add(this.comboTest, 0, 1);
            this.tableLeft.Controls.Add(this.labelKisi, 0, 2);
            this.tableLeft.Controls.Add(this.comboKisi, 0, 3);
            this.tableLeft.Controls.Add(this.labelPort, 0, 4);
            this.tableLeft.Controls.Add(this.comboPort, 0, 5);
            this.tableLeft.Controls.Add(this.flowButtons, 0, 6);
            this.tableLeft.Dock = System.Windows.Forms.DockStyle.Top;
            this.tableLeft.Location = new System.Drawing.Point(10, 10);
            this.tableLeft.Name = "tableLeft";
            this.tableLeft.RowCount = 7;
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 36F));
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 36F));
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.tableLeft.Size = new System.Drawing.Size(259, 584);
            this.tableLeft.TabIndex = 0;
            // 
            // labelTest
            // 
            this.labelTest.Dock = System.Windows.Forms.DockStyle.Fill;
            this.labelTest.Location = new System.Drawing.Point(3, 0);
            this.labelTest.Name = "labelTest";
            this.labelTest.Size = new System.Drawing.Size(253, 28);
            this.labelTest.TabIndex = 0;
            this.labelTest.Text = "Test";
            this.labelTest.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // comboTest
            // 
            this.comboTest.Dock = System.Windows.Forms.DockStyle.Fill;
            this.comboTest.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.comboTest.Items.AddRange(new object[] {
            "CMJ (Countermovement Jump)",
            "SJ (Squat Jump)",
            "IMTP (Isometric Mid-Thigh Pull)",
            "Drop Jump",
            "Custom"});
            this.comboTest.Location = new System.Drawing.Point(3, 31);
            this.comboTest.Name = "comboTest";
            this.comboTest.Size = new System.Drawing.Size(253, 21);
            this.comboTest.TabIndex = 1;
            // 
            // labelKisi
            // 
            this.labelKisi.Dock = System.Windows.Forms.DockStyle.Fill;
            this.labelKisi.Location = new System.Drawing.Point(3, 64);
            this.labelKisi.Name = "labelKisi";
            this.labelKisi.Size = new System.Drawing.Size(253, 28);
            this.labelKisi.TabIndex = 2;
            this.labelKisi.Text = "Kişi";
            this.labelKisi.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // comboKisi
            // 
            this.comboKisi.Dock = System.Windows.Forms.DockStyle.Fill;
            this.comboKisi.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.comboKisi.Location = new System.Drawing.Point(3, 95);
            this.comboKisi.Name = "comboKisi";
            this.comboKisi.Size = new System.Drawing.Size(253, 21);
            this.comboKisi.TabIndex = 3;
            // 
            // labelPort
            // 
            this.labelPort.Dock = System.Windows.Forms.DockStyle.Fill;
            this.labelPort.Location = new System.Drawing.Point(3, 128);
            this.labelPort.Name = "labelPort";
            this.labelPort.Size = new System.Drawing.Size(253, 28);
            this.labelPort.TabIndex = 4;
            this.labelPort.Text = "Seri Port";
            this.labelPort.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // comboPort
            // 
            this.comboPort.Dock = System.Windows.Forms.DockStyle.Fill;
            this.comboPort.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.comboPort.Location = new System.Drawing.Point(3, 159);
            this.comboPort.Name = "comboPort";
            this.comboPort.Size = new System.Drawing.Size(253, 21);
            this.comboPort.TabIndex = 5;
            // 
            // flowButtons
            // 
            this.flowButtons.Controls.Add(this.btnKisiEkle);
            this.flowButtons.Controls.Add(this.btnTestiBaslat);
            this.flowButtons.Controls.Add(this.btnKaydet);
            this.flowButtons.Controls.Add(this.btnGrafikTemizle);
            this.flowButtons.Dock = System.Windows.Forms.DockStyle.Fill;
            this.flowButtons.FlowDirection = System.Windows.Forms.FlowDirection.TopDown;
            this.flowButtons.Location = new System.Drawing.Point(3, 187);
            this.flowButtons.Name = "flowButtons";
            this.flowButtons.Size = new System.Drawing.Size(253, 394);
            this.flowButtons.TabIndex = 6;
            // 
            // btnKisiEkle
            // 
            this.btnKisiEkle.Location = new System.Drawing.Point(3, 3);
            this.btnKisiEkle.Name = "btnKisiEkle";
            this.btnKisiEkle.Size = new System.Drawing.Size(240, 23);
            this.btnKisiEkle.TabIndex = 0;
            this.btnKisiEkle.Text = "Kişi Ekle";
            this.btnKisiEkle.Click += new System.EventHandler(this.btnKisiEkle_Click);
            // 
            // btnTestiBaslat
            // 
            this.btnTestiBaslat.Location = new System.Drawing.Point(3, 32);
            this.btnTestiBaslat.Name = "btnTestiBaslat";
            this.btnTestiBaslat.Size = new System.Drawing.Size(240, 23);
            this.btnTestiBaslat.TabIndex = 1;
            this.btnTestiBaslat.Text = "Testi Başlat";
            this.btnTestiBaslat.Click += new System.EventHandler(this.btnTestiBaslat_Click);
            // 
            // btnKaydet
            // 
            this.btnKaydet.Location = new System.Drawing.Point(3, 61);
            this.btnKaydet.Name = "btnKaydet";
            this.btnKaydet.Size = new System.Drawing.Size(240, 23);
            this.btnKaydet.TabIndex = 2;
            this.btnKaydet.Text = "Kaydet";
            this.btnKaydet.Click += new System.EventHandler(this.btnKaydet_Click);
            // 
            // btnGrafikTemizle
            // 
            this.btnGrafikTemizle.Location = new System.Drawing.Point(3, 90);
            this.btnGrafikTemizle.Name = "btnGrafikTemizle";
            this.btnGrafikTemizle.Size = new System.Drawing.Size(240, 23);
            this.btnGrafikTemizle.TabIndex = 3;
            this.btnGrafikTemizle.Text = "Grafiği Temizle";
            this.btnGrafikTemizle.Click += new System.EventHandler(this.btnGrafikTemizle_Click);
            // 
            // panelRight
            // 
            this.panelRight.Controls.Add(this.splitRight);
            this.panelRight.Dock = System.Windows.Forms.DockStyle.Fill;
            this.panelRight.Location = new System.Drawing.Point(288, 3);
            this.panelRight.Name = "panelRight";
            this.panelRight.Padding = new System.Windows.Forms.Padding(10);
            this.panelRight.Size = new System.Drawing.Size(709, 594);
            this.panelRight.TabIndex = 1;
            // 
            // splitRight
            // 
            this.splitRight.Dock = System.Windows.Forms.DockStyle.Fill;
            this.splitRight.Location = new System.Drawing.Point(10, 10);
            this.splitRight.Name = "splitRight";
            this.splitRight.Orientation = System.Windows.Forms.Orientation.Horizontal;
            // 
            // splitRight.Panel1
            // 
            this.splitRight.Panel1.Controls.Add(this.panelCanvas);
            // 
            // splitRight.Panel2
            // 
            this.splitRight.Panel2.Controls.Add(this.gridSonuclar);
            this.splitRight.Size = new System.Drawing.Size(689, 574);
            this.splitRight.SplitterDistance = 287;
            this.splitRight.TabIndex = 0;
            // 
            // panelCanvas
            // 
            this.panelCanvas.BackColor = System.Drawing.Color.White;
            this.panelCanvas.Dock = System.Windows.Forms.DockStyle.Fill;
            this.panelCanvas.Location = new System.Drawing.Point(0, 0);
            this.panelCanvas.Name = "panelCanvas";
            this.panelCanvas.Size = new System.Drawing.Size(689, 287);
            this.panelCanvas.TabIndex = 0;
            this.panelCanvas.Paint += new System.Windows.Forms.PaintEventHandler(this.panelCanvas_Paint);
            this.panelCanvas.Resize += new System.EventHandler(this.panelCanvas_Resize);
            // 
            // gridSonuclar
            // 
            this.gridSonuclar.AllowUserToAddRows = false;
            this.gridSonuclar.AllowUserToDeleteRows = false;
            this.gridSonuclar.AutoSizeColumnsMode = System.Windows.Forms.DataGridViewAutoSizeColumnsMode.Fill;
            this.gridSonuclar.Dock = System.Windows.Forms.DockStyle.Fill;
            this.gridSonuclar.Location = new System.Drawing.Point(0, 0);
            this.gridSonuclar.Name = "gridSonuclar";
            this.gridSonuclar.ReadOnly = true;
            this.gridSonuclar.RowHeadersVisible = false;
            this.gridSonuclar.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.gridSonuclar.Size = new System.Drawing.Size(689, 283);
            this.gridSonuclar.TabIndex = 0;
            // 
            // Form_performans
            // 
            this.ClientSize = new System.Drawing.Size(1000, 600);
            this.Controls.Add(this.tableMain);
            this.Name = "Form_performans";
            this.Text = "Performans (ForceDesk - Basit Çizim)";
            this.Load += new System.EventHandler(this.Form_performans_Load);
            this.tableMain.ResumeLayout(false);
            this.panelLeft.ResumeLayout(false);
            this.tableLeft.ResumeLayout(false);
            this.flowButtons.ResumeLayout(false);
            this.panelRight.ResumeLayout(false);
            this.splitRight.Panel1.ResumeLayout(false);
            this.splitRight.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.splitRight)).EndInit();
            this.splitRight.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.gridSonuclar)).EndInit();
            this.ResumeLayout(false);

        }
    }
}
